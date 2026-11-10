# Topny modul susicky filamentu - skript pro Autodesk Fusion
# Postavi v novem dokumentu: chladic s zebry, PTC (RS PRO 336-739), tepelnou pojistku,
# prilozku na PTC, distancni sloupky, radialni ventilator 5015 a kryt (kanal) z vydechu do zeber.
#
# Souradnice: vzduch proudi ve smeru +X, zebra miri nahoru (+Z), PTC je zespodu na zakladne.
# Rozmery v mm, upravuj v sekci PARAMETRY. Ventilator a PTC jsou zjednodusene obalove tvary
# (pro presny tvar 5015 stahni STEP od vyrobce a vloz ho misto nej).

import adsk.core
import adsk.fusion
import traceback

# ---------------- PARAMETRY (mm) ----------------
HS_L = 60.0        # delka chladice ve smeru proudeni (X)
HS_W = 60.0        # sirka chladice (Y)
HS_BASE = 4.0      # tloustka zakladny
FIN_H = 25.0       # vyska zeber
FIN_T = 1.5        # tloustka zebra
FIN_N = 10         # pocet zeber
HOLE_XY = 26.0     # montazni otvory M3 v rozich (+-HOLE_XY)

PTC_L, PTC_W, PTC_T = 40.0, 35.0, 7.2   # RS PRO 336-739
TCO_L, TCO_W, TCO_T = 12.0, 4.0, 4.0     # tepelna pojistka (zjednoduseno jako kvadr)

FAN_D, FAN_H = 50.0, 15.0   # radialni ventilator 5015
FAN_OUT_W = 20.0            # sirka vydechu ventilatoru
DUCT_L = 30.0               # delka krytu mezi ventilatorem a chladicem
WALL = 1.6                  # tloustka steny krytu (tisk)

STRAP_W, STRAP_T = 10.0, 1.0   # kovova prilozka pres PTC
STANDOFF_H, STANDOFF_D = 15.0, 6.0

NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def cm(v):
    return v / 10.0  # Fusion API pracuje v centimetrech


def pt(x, y, z):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


class Builder:
    def __init__(self, comp):
        self.c = comp
        self.planes = {}

    def _offset_plane(self, base, dist, axis):
        if abs(dist) < 1e-9:
            return base
        key = (axis, round(dist, 4))
        if key in self.planes:
            return self.planes[key]
        for sign in (1.0, -1.0):
            pi = self.c.constructionPlanes.createInput()
            pi.setByOffset(base, adsk.core.ValueInput.createByReal(sign * cm(dist)))
            p = self.c.constructionPlanes.add(pi)
            o = p.geometry.origin
            got = o.z if axis == 'z' else o.x
            if abs(got - cm(dist)) < 1e-6:
                p.isLightBulbOn = False
                self.planes[key] = p
                return p
            p.deleteMe()
        raise RuntimeError('Nepodarilo se vytvorit rovinu %s = %s' % (axis, dist))

    def plane_xy(self, z):
        return self._offset_plane(self.c.xYConstructionPlane, z, 'z')

    def plane_yz(self, x):
        return self._offset_plane(self.c.yZConstructionPlane, x, 'x')

    def _sk_point(self, sk, x, y, z):
        p = sk.modelToSketchSpace(pt(x, y, z))
        return adsk.core.Point3D.create(p.x, p.y, 0)

    def _extrude(self, sk, height, op, name):
        prof = sk.profiles.item(0)
        ext = self.c.features.extrudeFeatures.addSimple(
            prof, adsk.core.ValueInput.createByReal(cm(height)), op)
        if name and op == NEW:
            ext.bodies.item(0).name = name
        return ext

    def box(self, x0, y0, z0, x1, y1, z1, op=NEW, name=None):
        sk = self.c.sketches.add(self.plane_xy(z0))
        sk.isVisible = False
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            self._sk_point(sk, x0, y0, z0), self._sk_point(sk, x1, y1, z0))
        return self._extrude(sk, z1 - z0, op, name)

    def cyl(self, cx, cy, r, z0, z1, op=NEW, name=None):
        sk = self.c.sketches.add(self.plane_xy(z0))
        sk.isVisible = False
        sk.sketchCurves.sketchCircles.addByCenterRadius(self._sk_point(sk, cx, cy, z0), cm(r))
        return self._extrude(sk, z1 - z0, op, name)

    def rect_yz(self, x, y0, y1, z0, z1):
        sk = self.c.sketches.add(self.plane_yz(x))
        sk.isVisible = False
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            self._sk_point(sk, x, y0, z0), self._sk_point(sk, x, y1, z1))
        return sk.profiles.item(0)

    def loft(self, x0, r0, x1, r1, name):
        li = self.c.features.loftFeatures.createInput(NEW)
        li.loftSections.add(self.rect_yz(x0, *r0))
        li.loftSections.add(self.rect_yz(x1, *r1))
        li.isSolid = True
        body = self.c.features.loftFeatures.add(li).bodies.item(0)
        body.name = name
        return body


def new_comp(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def find_appearance(app, design, keywords):
    """Najde vzhled v knihovnach podle klicovych slov (prvni shoda), jinak None."""
    try:
        for lib in app.materialLibraries:
            for i in range(lib.appearances.count):
                a = lib.appearances.item(i)
                n = a.name.lower()
                if all(k in n for k in keywords):
                    existing = design.appearances.itemByName(a.name)
                    return existing if existing else design.appearances.addByCopy(a, a.name)
    except Exception:
        pass
    return None


def paint(comp, appearance, opacity=None):
    for b in comp.bRepBodies:
        try:
            if appearance:
                b.appearance = appearance
            if opacity is not None:
                b.opacity = opacity
        except Exception:
            pass


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        # ---- chladic ----
        hs = new_comp(root, 'Chladic %dx%d' % (HS_L, HS_W))
        b = Builder(hs)
        b.box(-HS_L / 2, -HS_W / 2, 0, HS_L / 2, HS_W / 2, HS_BASE, NEW, 'Chladic')
        pitch = (HS_W - FIN_T) / (FIN_N - 1)
        for i in range(FIN_N):
            y = -HS_W / 2 + FIN_T / 2 + i * pitch
            b.box(-HS_L / 2, y - FIN_T / 2, HS_BASE, HS_L / 2, y + FIN_T / 2, HS_BASE + FIN_H, JOIN)
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.cyl(sx * HOLE_XY, sy * HOLE_XY, 1.6, 0, HS_BASE, CUT)      # M3 pruchozi
        strap_hole_y = PTC_W / 2 + 4.5
        for sy in (-1, 1):
            b.cyl(0, sy * strap_hole_y, 1.25, 0, HS_BASE - 0.5, CUT)         # M3 zavit (vrtat 2,5)

        # ---- PTC zespodu na zakladne ----
        ptc = new_comp(root, 'PTC RS PRO 336-739')
        b = Builder(ptc)
        b.box(-PTC_L / 2, -PTC_W / 2, -PTC_T, PTC_L / 2, PTC_W / 2, 0, NEW, 'PTC 40x35x7,2')
        for sy in (-1, 1):
            b.box(PTC_L / 2, sy * 5 - 0.75, -PTC_T / 2 - 0.75,
                  PTC_L / 2 + 20, sy * 5 + 0.75, -PTC_T / 2 + 0.75, NEW, 'Privod')

        # ---- tepelna pojistka vedle PTC ----
        tco = new_comp(root, 'Tepelna pojistka SF129R0')
        b = Builder(tco)
        ty = -(PTC_W / 2 + 4.5 + TCO_W / 2 + 0.5)
        if ty - TCO_W / 2 < -HS_W / 2:
            ty = -HS_W / 2 + TCO_W / 2 + 0.5
        b.box(STRAP_W / 2 + 2, ty - TCO_W / 2, -TCO_T, STRAP_W / 2 + 2 + TCO_L, ty + TCO_W / 2, 0,
              NEW, 'TCO (zjednoduseno)')

        # ---- prilozka pres PTC ----
        st = new_comp(root, 'Prilozka')
        b = Builder(st)
        leg_y0, leg_y1 = PTC_W / 2 + 2.5, PTC_W / 2 + 6.5
        b.box(-STRAP_W / 2, -leg_y1, -PTC_T - STRAP_T, STRAP_W / 2, leg_y1, -PTC_T, NEW, 'Prilozka')
        b.box(-STRAP_W / 2, leg_y0, -PTC_T, STRAP_W / 2, leg_y1, 0, JOIN)
        b.box(-STRAP_W / 2, -leg_y1, -PTC_T, STRAP_W / 2, -leg_y0, 0, JOIN)
        for sy in (-1, 1):
            b.cyl(0, sy * strap_hole_y, 1.6, -PTC_T - STRAP_T, 0, CUT)

        # ---- distancni sloupky ----
        so = new_comp(root, 'Sloupky M3')
        b = Builder(so)
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.cyl(sx * HOLE_XY, sy * HOLE_XY, STANDOFF_D / 2, -STANDOFF_H, 0, NEW, 'Sloupek')
                b.cyl(sx * HOLE_XY, sy * HOLE_XY, 1.25, -STANDOFF_H, 0, CUT)

        # ---- ventilator 5015 ----
        fan = new_comp(root, 'Ventilator 5015 24V')
        b = Builder(fan)
        r = FAN_D / 2
        z0 = HS_BASE + FIN_H / 2 - FAN_H / 2          # vydech na stred zeber
        x_out = -HS_L / 2 - DUCT_L
        cx = x_out - r - 1.0
        y_out0, y_out1 = r - FAN_OUT_W, r                # tangencialni vydech
        b.cyl(cx, 0, r, z0, z0 + FAN_H, NEW, 'Ventilator 5015')
        b.box(cx, y_out0, z0, x_out, y_out1, z0 + FAN_H, JOIN)
        b.cyl(cx, 0, 14, z0 + FAN_H - 1, z0 + FAN_H, CUT)                     # sani
        b.cyl(cx, 0, 8, z0 + FAN_H - 1, z0 + FAN_H, JOIN)                     # naboj
        b.box(x_out - 8, y_out0 + 1.2, z0 + 1.2, x_out, y_out1 - 1.2, z0 + FAN_H - 1.2, CUT)

        # ---- kryt z vydechu do zeber ----
        du = new_comp(root, 'Kryt (tisk)')
        b = Builder(du)
        x1 = -HS_L / 2
        outer = b.loft(x_out, (y_out0 - WALL, y_out1 + WALL, z0 - WALL, z0 + FAN_H + WALL),
                       x1, (-HS_W / 2 - WALL, HS_W / 2 + WALL, HS_BASE - WALL, HS_BASE + FIN_H + WALL),
                       'Kryt')
        inner = b.loft(x_out, (y_out0, y_out1, z0, z0 + FAN_H),
                       x1, (-HS_W / 2, HS_W / 2, HS_BASE, HS_BASE + FIN_H), 'tmp')
        tools = adsk.core.ObjectCollection.create()
        tools.add(inner)
        ci = du.features.combineFeatures.createInput(outer, tools)
        ci.operation = CUT
        du.features.combineFeatures.add(ci)

        # ---- vzhled ----
        paint(hs, find_appearance(app, design, ['aluminum', 'satin']))
        paint(ptc, find_appearance(app, design, ['paint', 'red']))
        paint(tco, find_appearance(app, design, ['brass']))
        paint(st, find_appearance(app, design, ['steel', 'satin']))
        paint(so, find_appearance(app, design, ['brass']))
        paint(fan, find_appearance(app, design, ['plastic', 'black']))
        paint(du, find_appearance(app, design, ['plastic', 'white']), opacity=0.45)

        app.activeViewport.fit()
        ui.messageBox('Hotovo: topny modul je v novem dokumentu.\n'
                      'Kryt je pruhledny, aby byla videt zebra. Rozmery zmenis v sekci PARAMETRY skriptu.')
    except Exception:
        if ui:
            ui.messageBox('Chyba skriptu:\n{}'.format(traceback.format_exc()))
