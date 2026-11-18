"""
2D simulace proudeni a teploty vzduchu v komore susicky (rez XZ = pohled zepredu).

Navier-Stokes (nestlacitelne, Boussinesq vztlak) na MAC siti, semi-Lagrangeovska advekce,
projekce tlaku (primy resic). Turbulence jen pres efektivni viskozitu -> vysledek je kvalitativni:
ukazuje smer cirkulace, mrtva mista a rozlozeni teploty, ne presne rychlosti.

Geometrie ze sestavy susicka_celek_v2 (mm): komora X -110..156, Z 0..230 (hloubka 110),
civka D200 (stred 0;118) - v hloubce zabira jen 70 ze 110 mm, proto porezni oblast,
kolebka X -75..75 Z 8..33 (pevna), ventilator 5015 X 126.9..141.9 Z 5..56, kryt 56..76,
sendvic s PTC X 120.8..148 Z 76..136 (zebra vedou vzduch svisle -> anizotropni odpor).
Ztraty: steny a strop U ~ 3,8 W/m2K do 22 C, prepazka 1,5 W/m2K do 30 C,
predni a zadni stena (mimo rez) jako objemovy odvod tepla.
Vykon a prutok z tepelneho modelu termika_0d.py (topeni naplno, bez izolace).
Spusteni: python proudeni_2d.py  -> vystupy/proudeni_2d.png
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.ndimage import map_coordinates

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vystupy")
os.makedirs(OUT, exist_ok=True)

# ---------------- parametry ----------------
DX = 2.5e-3
X0, X1, Z0, Z1 = -0.110, 0.156, 0.0, 0.230
DEPTH = 0.110
NX, NZ = int(round((X1 - X0) / DX)), int(round((Z1 - Z0) / DX))
RHO, CP = 1.03, 1008.0
NU = 3.0e-4                    # efektivni (turbulentni) viskozita
ALPHA = NU / 0.9
G, BETA, TREF = 9.81, 1 / 335.0, 60.0
T_AMB, T_ELEC = 22.0, 30.0
U_WALL = 1 / (1 / 8 + 0.003 / 0.2 + 1 / 8)
U_DIV = 1.5
Q_HEAT = 37.0                  # W (topeni naplno, z termika_0d)
Q_FLOW = 1.78e-3               # m3/s (ventilator 5015 v kanalech chladicu)
DT = 0.004
T_END = 60.0

xc = X0 + (np.arange(NX) + 0.5) * DX
zc = Z0 + (np.arange(NZ) + 0.5) * DX
XX, ZZ = np.meshgrid(xc, zc)


def box(x0, x1, z0, z1):
    return (XX >= x0) & (XX <= x1) & (ZZ >= z0) & (ZZ <= z1)


def line_mask(p0, p1, w=DX):
    (xa, za), (xb, zb) = p0, p1
    d = np.array([xb - xa, zb - za])
    L = np.hypot(*d)
    t = np.clip(((XX - xa) * d[0] + (ZZ - za) * d[1]) / L ** 2, 0, 1)
    dist = np.hypot(XX - (xa + t * d[0]), ZZ - (za + t * d[1]))
    return dist <= w * 0.75


mm = 1e-3
SPOOL = (XX ** 2 + (ZZ - 0.118) ** 2) <= 0.100 ** 2
CRADLE = box(-0.075, 0.075, 0.008, 0.033)
HEATER = box(120.8 * mm, 148.0 * mm, 76 * mm, 136 * mm)
FAN_X0, FAN_X1 = 126.9 * mm, 141.9 * mm
FAN_OUT = box(FAN_X0, FAN_X1, 36 * mm, 56 * mm)
DUCT = line_mask((FAN_X0 - 1.6 * mm, 56 * mm), (119.2 * mm, 76 * mm)) | \
    line_mask((FAN_X1 + 1.6 * mm, 56 * mm), (149.6 * mm, 76 * mm))
FAN_SIDES = line_mask((FAN_X0 - 1.0 * mm, 8 * mm), (FAN_X0 - 1.0 * mm, 56 * mm)) | \
    line_mask((FAN_X1 + 1.0 * mm, 30 * mm), (FAN_X1 + 1.0 * mm, 56 * mm))
SOLID = (CRADLE | DUCT | FAN_SIDES) & ~HEATER
SENSOR_OLD = (0.0, 0.196)          # SHT40 v puvodni sestave (nahore uprostred)
SENSOR = SENSOR_OLD

# varianta "kanal": sachta nad topenim + vodorovny kanal pod stropem s tryskou u X = 65 mm
VEDENI = "kanal" in sys.argv
if VEDENI:
    def wall(x0, x1, z0, z1):
        """Stena 1,6 mm - rozsirena aspon na jednu bunku site."""
        cx, cz = 0.5 * (x0 + x1), 0.5 * (z0 + z1)
        hx, hz = max(0.5 * (x1 - x0), 0.55 * DX), max(0.5 * (z1 - z0), 0.55 * DX)
        return box(cx - hx, cx + hx, cz - hz, cz + hz)
    KANAL = (wall(119.2 * mm, 120.8 * mm, 76 * mm, 206 * mm)         # rukav + sachta vlevo (k civce)
             | wall(148.0 * mm, 149.6 * mm, 76 * mm, 229.5 * mm)     # rukav + sachta vpravo (u steny)
             | wall(65 * mm, 120.8 * mm, 204.4 * mm, 206 * mm)       # dno vodorovne casti
             | wall(65 * mm, 151.2 * mm, 227.9 * mm, 229.5 * mm))    # strop kanalu
    SOLID = SOLID | (KANAL & ~HEATER)
    SENSOR = (0.100, 0.046)        # SHT40 presunuty ke vstupu ventilatoru
FLUID = ~SOLID
# pas vzduchu kolem obvodu civky (2-12 mm od civky) - to, co filament "vidi"
RR = np.hypot(XX, ZZ - 0.118)
RING = (RR > 0.102) & (RR < 0.112) & ~SOLID & (ZZ > 0.035)

# otevrene steny bunek (normalova rychlost muze byt nenulova)
UO = np.zeros((NZ, NX + 1), bool)
UO[:, 1:-1] = FLUID[:, :-1] & FLUID[:, 1:]
WO = np.zeros((NZ + 1, NX), bool)
WO[1:-1, :] = FLUID[:-1, :] & FLUID[1:, :]
# rovina ventilatoru: steny bunek s predepsanou rychlosti (tlak je nemeni)
J_FAN = int(round(46e-3 / DX))
FAN_PLANE = np.zeros((NZ + 1, NX), bool)
FAN_PLANE[J_FAN, :] = (xc > 126.9e-3 + 0.5 * DX) & (xc < 141.9e-3 - 0.5 * DX)
FAN_PLANE &= WO
WO_P = WO & ~FAN_PLANE


def face_avg_u(m):
    a = np.zeros((NZ, NX + 1), bool)
    a[:, 1:-1] = m[:, :-1] | m[:, 1:]
    return a


def face_avg_w(m):
    a = np.zeros((NZ + 1, NX), bool)
    a[1:-1, :] = m[:-1, :] | m[1:, :]
    return a


HEAT_U, HEAT_W = face_avg_u(HEATER), face_avg_w(HEATER)
SPOOL_U, SPOOL_W = face_avg_u(SPOOL), face_avg_w(SPOOL)
FAN_W = face_avg_w(FAN_OUT)
C_HEAT_U, C_HEAT_W, C_SPOOL = 400.0, 8.0, 25.0     # odpor [1/s]
K_FAN = 150.0
W_FAN = Q_FLOW / DEPTH / (FAN_PLANE.sum() * DX)    # prumerovano pres hloubku komory
Q_VOL = Q_HEAT / DEPTH / (HEATER.sum() * DX * DX)  # W/m3 v oblasti topeni

# ---------------- tlak: Laplace na tekutych bunkach ----------------
idx = -np.ones((NZ, NX), int)
fl = np.argwhere(FLUID)
idx[FLUID] = np.arange(len(fl))
rows, cols, vals = [], [], []
for n, (j, i) in enumerate(fl):
    diag = 0
    for (jj, ii, open_) in ((j, i - 1, UO[j, i]), (j, i + 1, UO[j, i + 1]),
                            (j - 1, i, WO_P[j, i]), (j + 1, i, WO_P[j + 1, i])):
        if open_:
            rows.append(n); cols.append(idx[jj, ii]); vals.append(1.0)
            diag -= 1
    rows.append(n); cols.append(n); vals.append(diag)
A = sp.csr_matrix((vals, (rows, cols)), shape=(len(fl), len(fl))).tolil()
A[0, :] = 0
A[0, 0] = 1
LU = spla.splu(A.tocsc())


def lap(f, open_x, open_z, dirichlet0):
    """5bodovy Laplace; uzavrene steny: Dirichlet 0 (rychlost) nebo Neumann (teplota)."""
    out = np.zeros_like(f)
    c = f[1:-1, 1:-1]
    for sl, osl in (((slice(1, -1), slice(0, -2)), None), ((slice(1, -1), slice(2, None)), None),
                    ((slice(0, -2), slice(1, -1)), None), ((slice(2, None), slice(1, -1)), None)):
        nb = f[sl]
        out[1:-1, 1:-1] += nb - c
    return out / DX ** 2


def sample(field, x, z, ox, oz):
    """Bilinearni vzorkovani pole na fyzickych souradnicich (ox, oz = posun mrize v bunkach)."""
    ci = (x - X0) / DX - ox
    cj = (z - Z0) / DX - oz
    return map_coordinates(field, [cj, ci], order=1, mode="nearest")


def centers(u, w):
    return 0.5 * (u[:, :-1] + u[:, 1:]), 0.5 * (w[:-1, :] + w[1:, :])


# souradnice uzlu jednotlivych mrizi
xu, zu = np.meshgrid(X0 + np.arange(NX + 1) * DX, zc)
xw, zw = np.meshgrid(xc, Z0 + np.arange(NZ + 1) * DX)

# okrajove bunky pro ztraty tepla
EDGE_L = np.zeros((NZ, NX)); EDGE_L[:, 0] = 1
EDGE_R = np.zeros((NZ, NX)); EDGE_R[:, -1] = 1
EDGE_T = np.zeros((NZ, NX))
for _i in range(NX):                      # strop: nejvyssi tekuta bunka ve sloupci (i nad kanalem)
    _j = np.nonzero(FLUID[:, _i])[0]
    EDGE_T[_j.max(), _i] = 1
EDGE_B = np.zeros((NZ, NX)); EDGE_B[0, :] = 1


def advect_T(T, u, w):
    """Upwind metoda konecnych objemu s rychlostmi na stenach bunek (zachovava teplo)."""
    vmax = max(np.abs(u).max(), np.abs(w).max(), 1e-9)
    nsub = max(1, int(np.ceil(vmax * DT / DX / 0.8)))
    dt = DT / nsub
    ui, wi = u[:, 1:-1], w[1:-1, :]
    for _ in range(nsub):
        fx = np.where(ui > 0, ui * T[:, :-1], ui * T[:, 1:])
        fz = np.where(wi > 0, wi * T[:-1, :], wi * T[1:, :])
        d = np.zeros_like(T)
        d[:, :-1] -= fx; d[:, 1:] += fx
        d[:-1, :] -= fz; d[1:, :] += fz
        T = T + dt * d / DX
    return T


def run():
    u = np.zeros((NZ, NX + 1))
    w = np.zeros((NZ + 1, NX))
    T = np.full((NZ, NX), 55.0)
    nsteps = int(T_END / DT)
    hist = []
    t0 = time.time()
    for n in range(nsteps):
        ucn, wcn = centers(u, w)
        # --- advekce (semi-Lagrange) ---
        uu = sample(ucn, xu, zu, 0.5, 0.5); wu = sample(wcn, xu, zu, 0.5, 0.5)
        uw = sample(ucn, xw, zw, 0.5, 0.5); ww = sample(wcn, xw, zw, 0.5, 0.5)
        ut = sample(ucn, XX, ZZ, 0.5, 0.5); wt = sample(wcn, XX, ZZ, 0.5, 0.5)
        u_new = sample(u, xu - DT * uu, zu - DT * wu, 0.0, 0.5)
        w_new = sample(w, xw - DT * uw, zw - DT * ww, 0.5, 0.0)
        T_new = advect_T(T, u, w)
        # --- difuze ---
        u_new += DT * NU * lap(u_new * UO, None, None, True) * UO
        w_new += DT * NU * lap(w_new * WO, None, None, True) * WO
        # vedeni tepla jen pres otevrene steny bunek (pevne dily a okraje = izolovane, ztraty zvlast)
        gx = (T_new[:, 1:] - T_new[:, :-1]) * UO[:, 1:-1]
        gz = (T_new[1:, :] - T_new[:-1, :]) * WO[1:-1, :]
        lapT = np.zeros_like(T_new)
        lapT[:, :-1] += gx; lapT[:, 1:] -= gx
        lapT[:-1, :] += gz; lapT[1:, :] -= gz
        lapT /= DX ** 2
        T_new += DT * ALPHA * lapT * FLUID
        # --- sily: vztlak, ventilator, odpor zeber a civky ---
        Tf = np.zeros((NZ + 1, NX)); Tf[1:-1] = 0.5 * (T_new[:-1] + T_new[1:])
        w_new += DT * G * BETA * (Tf - TREF) * WO
        u_new = np.where(HEAT_U, u_new / (1 + DT * C_HEAT_U), u_new)
        w_new = np.where(HEAT_W, w_new / (1 + DT * C_HEAT_W), w_new)
        u_new = np.where(SPOOL_U, u_new / (1 + DT * C_SPOOL), u_new)
        w_new = np.where(SPOOL_W, w_new / (1 + DT * C_SPOOL), w_new)
        u_new *= UO; w_new *= WO
        w_new[FAN_PLANE] = W_FAN
        # --- projekce ---
        div = (u_new[:, 1:] - u_new[:, :-1] + w_new[1:, :] - w_new[:-1, :]) / DX
        b = div[FLUID] * DX * DX / DT
        b[0] = 0.0
        p = np.zeros((NZ, NX)); p[FLUID] = LU.solve(b)
        u_new[:, 1:-1] -= DT * (p[:, 1:] - p[:, :-1]) / DX * UO[:, 1:-1]
        w_new[1:-1, :] -= DT * (p[1:, :] - p[:-1, :]) / DX * WO_P[1:-1, :]
        u, w = u_new, w_new
        # --- teplo: zdroj, ztraty ---
        rc = RHO * CP
        T_new += DT * Q_VOL / rc * HEATER
        T_new -= DT * (U_WALL * (T_new - T_AMB) * (EDGE_L + EDGE_R + EDGE_T) / DX
                       + U_DIV * (T_new - T_ELEC) * EDGE_B / DX
                       + 2 * U_WALL * (T_new - T_AMB) / DEPTH) / rc * FLUID
        T = T_new
        if n % 250 == 0:
            hist.append((n * DT, T[FLUID].mean(), np.abs(w).max()))
    print("cas vypoctu %.0f s" % (time.time() - t0))
    return u, w, T, np.array(hist)


def main():
    print("mriz %d x %d, krok %.1f mm, rychlost z ventilatoru %.2f m/s, zdroj %.0f W/m3"
          % (NX, NZ, DX * 1e3, W_FAN, Q_VOL))
    u, w, T, hist = run()
    uc, wc = centers(u, w)
    spd = np.hypot(uc, wc)
    Tf = np.where(FLUID, T, np.nan)
    ts = float(sample(T, np.array([SENSOR[0]]), np.array([SENSOR[1]]), 0.5, 0.5)[0])
    print("prumerna teplota vzduchu %.1f °C, na miste SHT40 %.1f °C" % (np.nanmean(Tf), ts))
    print("v okoli civky (porezni oblast): min %.1f, max %.1f °C" % (np.nanmin(Tf[SPOOL]), np.nanmax(Tf[SPOOL])))
    tso = float(sample(T, np.array([SENSOR_OLD[0]]), np.array([SENSOR_OLD[1]]), 0.5, 0.5)[0])
    print("puvodni misto SHT40 (0;196): %.1f °C" % tso)
    ring = Tf[RING]
    print("vzduch kolem obvodu civky: prumer %.1f, min %.1f, max %.1f °C, rozptyl (max-min) %.1f K, sm. odch. %.1f K"
          % (ring.mean(), ring.min(), ring.max(), ring.max() - ring.min(), ring.std()))
    sp_ring = spd[RING]
    print("rychlost kolem obvodu civky: prumer %.2f m/s" % sp_ring.mean())
    print("vzduch u prave steny (za topenim, Z 70-150 mm): max %.1f °C" % np.nanmax(Tf[(ZZ > 0.07) & (ZZ < 0.15)][:, -1] if False else Tf[(ZZ[:, -1] > 0.07) & (ZZ[:, -1] < 0.15), -1]))
    print("vystup z topeni (Z 136-140 mm): %.1f °C" % np.nanmean(Tf[box(120.8 * mm, 148 * mm, 136 * mm, 141 * mm)]))
    print("max rychlost %.2f m/s, prumer mimo topeni %.2f m/s" % (spd.max(), spd[FLUID & ~HEATER & ~FAN_OUT].mean()))
    print("vyvoj (t, Tprum, wmax):", np.round(hist[::8], 2).tolist())

    fig, ax = plt.subplots(1, 2, figsize=(15, 6.6))
    ext = [X0 * 1e3, X1 * 1e3, Z0 * 1e3, Z1 * 1e3]
    im = ax[0].imshow(Tf, origin="lower", extent=ext, cmap="inferno", vmin=np.nanpercentile(Tf, 1), vmax=np.nanpercentile(Tf, 99.5))
    fig.colorbar(im, ax=ax[0], label="teplota vzduchu [°C]")
    ax[0].set_title("Teplota (topení naplno %.0f W, ventilátor 5015)" % Q_HEAT)
    im2 = ax[1].imshow(np.where(FLUID, spd, np.nan), origin="lower", extent=ext, cmap="viridis", vmax=np.percentile(spd, 99))
    fig.colorbar(im2, ax=ax[1], label="rychlost [m/s] (průměr přes hloubku)")
    ax[1].streamplot(xc * 1e3, zc * 1e3, uc, wc, color="w", density=1.6, linewidth=0.6, arrowsize=0.8)
    ax[1].set_title("Proudění vzduchu")
    for a in ax:
        a.add_patch(plt.Circle((0, 118), 100, fill=False, ec="c", lw=1.2, ls="--"))
        a.add_patch(plt.Rectangle((-75, 8), 150, 25, fc="0.6", ec="k"))
        a.add_patch(plt.Rectangle((120.8, 76), 27.2, 60, fill=False, ec="r", lw=1.2))
        a.add_patch(plt.Rectangle((FAN_X0 * 1e3, 5), 15, 51, fill=False, ec="w", lw=1))
        a.plot([FAN_X0 * 1e3 - 1.6, 119.2], [56, 76], "w-", lw=1.5)
        a.plot([FAN_X1 * 1e3 + 1.6, 149.6], [56, 76], "w-", lw=1.5)
        if VEDENI:
            a.plot([120.0, 120.0, 65], [76, 205.2, 205.2], "w-", lw=2)
            a.plot([148.8, 148.8, 65], [76, 228.7, 228.7], "w-", lw=2)
        a.plot(SENSOR[0] * 1e3, SENSOR[1] * 1e3, "c^", ms=8)
        a.annotate("SHT40", (SENSOR[0] * 1e3 + 4, SENSOR[1] * 1e3 + 4), color="c", fontsize=8)
        a.annotate("PTC + chladiče", (100, 140), color="r", fontsize=8)
        a.annotate("cívka (v hloubce 70 ze 110 mm)", (-60, 222), color="c", fontsize=8)
        a.set_xlabel("X [mm]"); a.set_ylabel("Z [mm]")
        a.set_aspect("equal")
    fig.suptitle("Sušička – 2D řez komorou%s (kvalitativní, efektivní turbulentní viskozita)" % (" s kanálem pod strop" if VEDENI else ""))
    fig.tight_layout()
    name = "proudeni_2d_kanal.png" if VEDENI else "proudeni_2d.png"
    fig.savefig(os.path.join(OUT, name), dpi=130)
    print("ulozeno", os.path.join(OUT, name))


if __name__ == "__main__":
    main()
