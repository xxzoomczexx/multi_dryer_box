"""
Tepelny model susicky v case (soustredene parametry, "0D").

Uzly: PTC (keramika) -> 2 chladice 60x60x10 (sendvic) -> vzduch v komore (+ drobne vnitrni dily)
      -> steny z PETG -> okoli; vzduch -> civka s filamentem; vzduch -> prepazka -> oddil elektroniky.
Ventilator 5015 tlaci vzduch kanaly mezi zebry (laminarni proudeni, korelace pro rovnobezne desky).
PTC: odpor roste nad spinaci teplotou (exponencialni model), napajeni 24 V s proudovym limitem zdroje.
Regulace: PI na teplotu vzduchu (SHT40), vystup = strida PWM topeni.

Vsechny hodnoty jsou odhady z modelu ve Fusionu (susicka_celek_v2) a z katalogovych udaju;
vysledky berte jako radovy odhad, overi se merenim na prototypu.
Spusteni: python termika_0d.py  -> obrazky do slozky vystupy/
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vystupy")
os.makedirs(OUT, exist_ok=True)

# ---------------- vzduch (~70 C) ----------------
RHO, CP, MU, K_AIR, PR = 1.03, 1008.0, 2.04e-5, 0.0293, 0.70

# ---------------- chladice (2x 60x60x10, odhad z fotky) ----------------
N_HS = 2
HS_W, HS_L = 0.060, 0.060          # sirka (napric zebry), delka ve smeru proudeni
BASE_T, FIN_H, FIN_T, FIN_N = 0.002, 0.008, 0.0012, 20
K_AL = 200.0
gap = (HS_W - FIN_N * FIN_T) / (FIN_N - 1)          # mezera mezi zebry
n_ch = FIN_N - 1
A_ch = N_HS * n_ch * gap * FIN_H                     # prurez vsech kanalu
Dh = 2 * gap * FIN_H / (gap + FIN_H)                 # hydraulicky prumer kanalu
A_fin = N_HS * FIN_N * 2 * FIN_H * HS_L              # plocha zeber
A_base = N_HS * n_ch * gap * HS_L                    # plocha zakladny mezi zebry
M_HS = N_HS * 2700 * (HS_W * HS_L * BASE_T + FIN_N * FIN_T * FIN_H * HS_L)

# ---------------- ventilator 5015 24 V (linearni charakteristika, odhad) ----------------
Q_MAX, P_MAX = 2.0e-3, 200.0       # m3/s (~4,2 CFM), Pa
K_MINOR = 1.5                      # vstup/vystup z kanalu + kryt


def fan_point(speed=1.0):
    """Prusecik charakteristiky ventilatoru (skalovane otackami) a odporu kanalu."""
    qmax, pmax = Q_MAX * speed, P_MAX * speed ** 2
    lo, hi = 0.0, qmax
    for _ in range(60):
        q = 0.5 * (lo + hi)
        v = q / A_ch
        re = RHO * v * Dh / MU
        f = 70.0 / max(re, 1e-9)              # laminarni f*Re pro obdelnikovy kanal ~70
        dp = f * HS_L / Dh * RHO * v * v / 2 + K_MINOR * RHO * v * v / 2
        dp_fan = pmax * (1 - q / qmax)
        if dp > dp_fan:
            hi = q
        else:
            lo = q
    q = 0.5 * (lo + hi)
    return q, q / A_ch


def h_channel(v):
    """Prestup tepla v kanalu mezi zebry (rovnobezne desky, nabihajici laminarni proudeni)."""
    dh_pp = 2 * gap
    re = RHO * v * dh_pp / MU
    x = HS_L / (dh_pp * re * PR)
    nu = 7.55 + 0.024 * x ** -1.14 / (1 + 0.0358 * PR ** 0.17 * x ** -0.64)
    return nu * K_AIR / dh_pp


def heater_conductance(speed=1.0):
    """Vraci (m*cp [W/K], ucinnost vymeniku eps, prutok, rychlost, h)."""
    q, v = fan_point(speed)
    h = h_channel(v)
    m = math.sqrt(2 * h / (K_AL * FIN_T))
    eta = math.tanh(m * FIN_H) / (m * FIN_H)
    ua = h * (eta * A_fin + A_base)
    mcp = RHO * q * CP
    eps = 1 - math.exp(-ua / mcp)
    return mcp, eps, q, v, h, eta, ua


# ---------------- PTC RS PRO 336-739 (24 V, 50 W, ~100 C na povrchu) ----------------
U_SUPPLY = 24.0
I_LIMIT = 3.5              # proudovy limit laboratorniho zdroje [A] (None = bez limitu)
R_MIN = 6.0                # odpor za studena [ohm] -> ~4 A naraz
T_SW, K_PTC = 95.0, 0.12   # spinaci teplota keramiky a strmost
R_INT = 0.40               # keramika -> chladice (pouzdro + pasta + rozvod v zakladne), K/W
C_PTC = 25.0               # J/K


def ptc_power(t_ptc, duty):
    r = R_MIN * math.exp(K_PTC * max(0.0, t_ptc - T_SW))
    if I_LIMIT is not None and U_SUPPLY / r > I_LIMIT:
        p, i = I_LIMIT ** 2 * r, I_LIMIT
    else:
        p, i = U_SUPPLY ** 2 / r, U_SUPPLY / r
    return duty * p, i


# ---------------- komora ----------------
T_AMB, T_ELEC = 22.0, 30.0
A_WALL = 2 * (0.266 * 0.230) + 2 * (0.110 * 0.230) + 0.266 * 0.110   # steny + strop komory
A_DIV = 0.266 * 0.110
H_IN, H_OUT = 8.0, 8.0             # uvnitr (cirkulace), venku (konvekce + zareni)
WALL_T, K_PETG = 0.003, 0.20
C_WALL = 0.7 * 840e-6 * 1270 * 1200      # ~70 % obalu je kolem komory
U_DIV = 1.5                        # dvojita prepazka se vzduchovou mezerou
UA_LEAK = 0.10                     # netesnosti
C_AIR = 1.2 * 1005 * 0.0067 + 200.0      # vzduch + kolebka, hridelky, loziska
C_SPOOL = 1.0 * 1200 + 0.25 * 1300       # 1 kg filamentu + civka
UA_SPOOL = 8.0 * 0.10


def simulate(setpoint, t_end_h=4.0, speed=1.0, insul_r=0.0, dt=0.5):
    """insul_r = pridany tepelny odpor izolace na vnejsi strane sten [m2K/W]."""
    mcp, eps, *_ = heater_conductance(speed)
    g_hs = eps * mcp                        # chladice -> vzduch [W/K]
    ua_in = H_IN * A_WALL
    ua_out = A_WALL / (WALL_T / K_PETG + insul_r + 1.0 / H_OUT)
    t_ptc = t_hs = t_air = t_wall = t_sp = T_AMB
    integ = 0.0
    kp, ki = 0.15, 0.0008
    n = int(t_end_h * 3600 / dt)
    rec = {k: [] for k in ("t", "ptc", "hs", "air", "wall", "spool", "p", "i", "duty")}
    for k in range(n):
        err = setpoint - t_air
        duty = kp * err + ki * integ
        if 0.0 < duty < 1.0 or (duty >= 1.0 and err < 0) or (duty <= 0.0 and err > 0):
            integ += err * dt               # anti-windup
        duty = min(1.0, max(0.0, duty))
        p, i = ptc_power(t_ptc, duty)
        q_ph = (t_ptc - t_hs) / R_INT
        q_ha = g_hs * (t_hs - t_air)
        q_aw = ua_in * (t_air - t_wall)
        q_wo = ua_out * (t_wall - T_AMB)
        q_as = UA_SPOOL * (t_air - t_sp)
        q_div = U_DIV * A_DIV * (t_air - T_ELEC) + UA_LEAK * (t_air - T_AMB)
        t_ptc += dt * (p - q_ph) / C_PTC
        t_hs += dt * (q_ph - q_ha) / (M_HS * 900)
        t_air += dt * (q_ha - q_aw - q_as - q_div) / C_AIR
        t_wall += dt * (q_aw - q_wo) / C_WALL
        t_sp += dt * q_as / C_SPOOL
        if k % int(10 / dt) == 0:
            for key, val in zip(rec, (k * dt / 60, t_ptc, t_hs, t_air, t_wall, t_sp, p, i, duty)):
                rec[key].append(val)
    return {k: np.array(v) for k, v in rec.items()}, dict(ua_out=ua_out, g_hs=g_hs)


def max_temp(speed=1.0, insul_r=0.0):
    r, _ = simulate(200.0, t_end_h=8.0, speed=speed, insul_r=insul_r, dt=1.0)
    return r["air"][-1], r["p"][-1], r["hs"][-1]


def main():
    mcp, eps, q, v, h, eta, ua = heater_conductance()
    print("Chladice: mezera %.2f mm, kanalu %d, prurez %.2f cm2, Dh %.2f mm, hmotnost %.0f g"
          % (gap * 1e3, N_HS * n_ch, A_ch * 1e4, Dh * 1e3, M_HS * 1e3))
    print("Ventilator: prutok %.2f l/s, rychlost v kanalech %.2f m/s" % (q * 1e3, v))
    print("h = %.0f W/m2K, ucinnost zeber %.2f, UA = %.2f W/K, m*cp = %.2f W/K, eps = %.2f"
          % (h, eta, ua, mcp, eps))
    print("Ohrev vzduchu pri 40 W: %.1f K" % (40 / mcp))

    scen = [("PETG 65 °C", 65.0), ("ABS 80 °C", 80.0)]
    res = {name: simulate(sp) for name, sp in scen}
    ins = simulate(80.0, insul_r=10e-3 / 0.035)     # 10 mm XPS/EPS zvenku

    for name, (r, info) in list(res.items()) + [("ABS 80 °C + izolace 10 mm", ins)]:
        last = slice(-60, None)
        print("%-28s vzduch %.1f °C, civka %.1f °C, chladic (TCO) max %.1f °C, PTC max %.1f °C, "
              "vykon ustal. %.1f W, max proud %.2f A, cas do (cil-2 °C) %s min"
              % (name, r["air"][-1], r["spool"][-1], r["hs"].max(), r["ptc"].max(),
                 r["p"][last].mean(), r["i"].max(),
                 next(("%.0f" % t for t, a in zip(r["t"], r["air"]) if a >= (65 if "PETG" in name else 80) - 2), "nedosazeno")))
    for spd in (0.6, 0.8, 1.0):
        for ins_r, lab in ((0.0, "bez izolace"), (10e-3 / 0.035, "izolace 10 mm")):
            ta, p, ths = max_temp(spd, ins_r)
            print("max. teplota komory (topeni naplno): ventilator %3.0f %%, %-14s -> %.1f °C (%.1f W, chladic %.1f °C)"
                  % (spd * 100, lab, ta, p, ths))

    # ---- grafy ----
    fig, axs = plt.subplots(2, 2, figsize=(13, 8.5), sharex=True)
    for name, (r, _) in res.items():
        axs[0, 0].plot(r["t"], r["air"], label=f"vzduch – {name}")
        axs[0, 0].plot(r["t"], r["spool"], "--", label=f"cívka – {name}")
        axs[0, 1].plot(r["t"], r["hs"], label=f"chladiče / TCO – {name}")
        axs[0, 1].plot(r["t"], r["ptc"], ":", label=f"keramika PTC – {name}")
        axs[1, 0].plot(r["t"], r["p"], label=name)
        axs[1, 1].plot(r["t"], r["wall"], label=name)
    r, _ = ins
    axs[0, 0].plot(r["t"], r["air"], color="k", lw=1, label="vzduch – ABS 80 °C, izolace 10 mm")
    axs[0, 1].axhline(118, color="r", lw=0.8, ls="--", label="SF129R0 holding 118 °C")
    axs[0, 1].axhline(133, color="r", lw=0.8, label="SF129R0 vybavení 133 °C")
    axs[0, 0].set_title("Teplota v komoře (SHT40) a cívky")
    axs[0, 1].set_title("Topný modul")
    axs[1, 0].set_title("Výkon PTC (24 V, limit zdroje 3,5 A)")
    axs[1, 1].set_title("Stěna z PETG (průměr)")
    for a, yl in zip(axs.flat, ("°C", "°C", "W", "°C")):
        a.set_ylabel(yl)
        a.grid(alpha=0.3)
        a.legend(fontsize=7)
    for a in axs[1]:
        a.set_xlabel("čas [min]")
    fig.suptitle("Sušička – tepelný model (PTC RS 336-739, 2× chladič 60×60×10, ventilátor 5015)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "termika_0d.png"), dpi=130)
    print("ulozeno", os.path.join(OUT, "termika_0d.png"))


if __name__ == "__main__":
    main()
