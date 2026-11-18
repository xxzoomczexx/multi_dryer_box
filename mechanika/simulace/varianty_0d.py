"""Porovnani variant chladice / izolace / ventilatoru (pouziva model z termika_0d.py)."""
import termika_0d as m

VARIANTY = [
    # nazev, pocet chladicu, sirka, delka, zakladna, vyska zeber, tloustka zebra, pocet zeber
    ("2x 60x60x10 (Ali, objednavany)", 2, .060, .060, .002, .008, .0012, 20),
    ("2x 60x60x15 BOKA (odhad jako zebra)", 2, .060, .060, .003, .012, .0010, 14),
    ("2x 60x60x20 (rovna zebra)", 2, .060, .060, .003, .017, .0015, 16),
    ("2x 60x60x25", 2, .060, .060, .004, .021, .0015, 16),
    ("1x 60x60x39 (jednostranny)", 1, .060, .060, .005, .034, .0010, 20),
]
for name, n, w, l, b, fh, ft, fn in VARIANTY:
    m.N_HS, m.HS_W, m.HS_L, m.BASE_T, m.FIN_H, m.FIN_T, m.FIN_N = n, w, l, b, fh, ft, fn
    m.gap = (w - fn * ft) / (fn - 1); m.n_ch = fn - 1
    m.A_ch = n * m.n_ch * m.gap * fh; m.Dh = 2 * m.gap * fh / (m.gap + fh)
    m.A_fin = n * fn * 2 * fh * l; m.A_base = n * m.n_ch * m.gap * l
    m.M_HS = n * 2700 * (w * l * b + fn * ft * fh * l)
    m.R_INT = 0.40 if n == 2 else 0.55      # jednostranne: jen jedna plocha PTC
    mcp, eps, q, v, h, eta, ua = m.heater_conductance()
    row = []
    for ins in (0.0, 10e-3 / 0.035):
        ta, p, ths = m.max_temp(1.0, ins)
        row.append("%.1f °C / %.0f W / chladic %.0f °C" % (ta, p, ths))
    print("%-36s prutok %.2f l/s, eps*mcp %.2f W/K | bez izolace: %s | izolace 10 mm: %s"
          % (name, q * 1e3, eps * mcp, row[0], row[1]))
