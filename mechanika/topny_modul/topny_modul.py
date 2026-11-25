# Topny modul susicky filamentu - skript pro Autodesk Fusion
# Postavi v novem dokumentu: chladic s zebry, topny vykonovy rezistor Arcol HS50 10R J (TME, 10 ohm,
# 50 W, hlinikove pouzdro; pri 24 V 57,6 W -> firmware omezi stridu na ~85 %), tepelnou pojistku
# SF129R0 a NTC 100k hned vedle rezistoru, distancni sloupky, ventilator (radialni 5015 nebo axialni)
# a kryt (kanal) z vydechu do zeber. Pro porovnani velikosti prida pruhlednou civku.
# (Puvodne PTC 24 V 120 C 76x63x7 z AliExpressu - nahrazeno 2026-11-25.)
#
# Souradnice: vzduch proudi ve smeru +X, zebra miri nahoru (+Z), rezistor je zespodu na zakladne
# chladice (rovnou stranou k chladici, s teplovodivou pastou, M3 do zavitu v zakladne). Dno boxu je
# v z = -STANDOFF_H. Rozmery v mm, upravuj v sekci PARAMETRY. Ventilator, rezistor a pojistka jsou
# zjednodusene obalove tvary; rezistor podle datasheetu Arcol HS50, chladic po doruceni premerit.
#
# Po dobehnuti ulozi vedle skriptu nahled.png (izometrie) a rozmery.txt.

import adsk.core
import adsk.fusion
import os
import traceback

# ---------------- PARAMETRY (mm) ----------------
# Chladic: Fischer Elektronik SK 100 100 AL/SA (TME) - 100 mm, sirka 64 (TME) / 66 (RS), vyska 40,
# zakladna 10 mm. Pocet a tloustka zeber zjednodusene, po doruceni premerit.
HS_L = 100.0       # delka chladice ve smeru proudeni (X)
HS_W = 66.0        # sirka chladice (Y)
HS_H = 40.0        # celkova vyska chladice
HS_BASE = 10.0     # tloustka zakladny (do ni zavity M3 pro rezistor a sloupky)
FIN_T = 1.5        # tloustka zebra
FIN_N = 14         # pocet zeber
FIN_H = HS_H - HS_BASE

# Rezistor Arcol HS50 - datasheet Arcol HS10-HS300, radek HS50 (max. rozmery, F a G +-0,3).
# HS10-HS50 maji jen 2 otvory v patce, uhloprickou (+F/2, +G/2) a (-F/2, -G/2).
RES_B = 72.5                 # B: celkova delka vcetne vyvodu
RES_E = 49.1                 # E: delka pouzdra vcetne patek
RES_A = 29.7                 # A: sirka pres patky
RES_C = 14.8                 # C: celkova vyska
RES_D = 14.2                 # D: sirka zebrovaneho tela
RES_K = 2.6                  # K: tloustka patky
RES_J = 5.2                  # J: delka patky s otvorem
RES_H = 8.5                  # H: vyska osy vyvodu nad dosedaci plochou
RES_F, RES_G = 39.7, 21.4    # F, G: roztec otvoru (podelne, napric)
RES_HOLE_D = 3.2             # L: prumer otvoru -> sroub M3
RES_LEAD_D = 2.0             # vyvod Ø 2,0

TCO_L, TCO_W, TCO_T = 12.0, 4.0, 4.0     # tepelna pojistka SF129R0 (zjednoduseno jako kvadr)
NTC_D, NTC_L = 3.0, 8.0                  # NTC 100k (sklenena kapka v trubicce)

FAN_TYPE = '5015'           # '5015' = radialni, 'axial' = klasicky ctvercovy
FAN_D, FAN_H = 50.0, 15.0   # radialni 5015
FAN_OUT_W = 20.0            # sirka vydechu 5015
AX_SIZE, AX_THICK = 60.0, 15.0   # axialni ventilator (60x60x15, pripadne 40/80, 10/25)
DUCT_L = 30.0               # delka krytu mezi ventilatorem a chladicem
WALL = 1.6                  # tloustka steny krytu (tisk)

STANDOFF_H, STANDOFF_D = 15.0, 6.0
STANDOFF_X = HS_L / 2 - 5.0      # sloupky v rozich zakladny (slepe zavity M3 zespodu)
STANDOFF_Y = HS_W / 2 - 5.0

SPOOL_D, SPOOL_W = 200.0, 70.0   # civka 1 kg pro porovnani velikosti
SPOOL_GAP = 30.0                 # mezera mezi modulem a civkou

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
            got = {'x': o.x, 'y': o.y, 'z': o.z}[axis]
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

    def plane_xz(self, y):
        return self._offset_plane(self.c.xZConstructionPlane, y, 'y')

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

    def cyl_y(self, cx, cy, cz, r, length, op=NEW, name=None):
        """Valec s osou v Y, symetricky kolem cy (smer normaly roviny XZ je pak jedno)."""
        sk = self.c.sketches.add(self.plane_xz(cy))
        sk.isVisible = False
        sk.sketchCurves.sketchCircles.addByCenterRadius(self._sk_point(sk, cx, cy, cz), cm(r))
        ei = self.c.features.extrudeFeatures.createInput(sk.profiles.item(0), op)
        ei.setSymmetricExtent(adsk.core.ValueInput.createByReal(cm(length)), True)
        ext = self.c.features.extrudeFeatures.add(ei)
        if name and op == NEW:
            ext.bodies.item(0).name = name
        return ext

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
    return occ


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


def hollow(comp, outer, inner):
    tools = adsk.core.ObjectCollection.create()
    tools.add(inner)
    ci = comp.features.combineFeatures.createInput(outer, tools)
    ci.operation = CUT
    comp.features.combineFeatures.add(ci)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        module_occs = []

        # ---- chladic ----
        occ = new_comp(root, 'Chladic %dx%dx%d' % (HS_L, HS_W, HS_H))
        module_occs.append(occ)
        hs = occ.component
        b = Builder(hs)
        b.box(-HS_L / 2, -HS_W / 2, 0, HS_L / 2, HS_W / 2, HS_BASE, NEW, 'Chladic')
        pitch = (HS_W - FIN_T) / (FIN_N - 1)
        for i in range(FIN_N):
            y = -HS_W / 2 + FIN_T / 2 + i * pitch
            b.box(-HS_L / 2, y - FIN_T / 2, HS_BASE, HS_L / 2, y + FIN_T / 2, HS_BASE + FIN_H, JOIN)
        blind = min(5.0, HS_BASE - 1.0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.cyl(sx * STANDOFF_X, sy * STANDOFF_Y, 1.25, 0, blind, CUT)   # M3 slepy zavit (vrtat 2,5)
        res_holes = ((RES_F / 2, RES_G / 2), (-RES_F / 2, -RES_G / 2))   # uhlopricne (datasheet)
        for hx, hy in res_holes:
            b.cyl(hx, hy, 1.25, 0, blind, CUT)                                # M3 zavit pro rezistor

        # ---- rezistor zespodu na zakladne (dosedaci plocha nahoru k chladici) ----
        occ = new_comp(root, 'Rezistor Arcol HS50 10R')
        module_occs.append(occ)
        res = occ.component
        b = Builder(res)
        core_l = RES_E - 2 * RES_J
        b.box(-RES_E / 2, -RES_A / 2, -RES_K, RES_E / 2, RES_A / 2, 0, NEW, 'Rezistor patka')
        b.box(-core_l / 2, -RES_D / 2, -RES_C, core_l / 2, RES_D / 2, -RES_K, JOIN)
        for hx, hy in res_holes:
            b.cyl(hx, hy, RES_HOLE_D / 2, -RES_K, 0, CUT)
        r = RES_LEAD_D / 2
        for sx in (-1, 1):   # axialni vyvody na koncich (zjednodusene na ctverec)
            b.box(sx * core_l / 2, -r, -RES_H - r, sx * RES_B / 2, r, -RES_H + r, NEW, 'Vyvod')

        # ---- tepelna pojistka a NTC hned vedle rezistoru (po stranach, na zakladne) ----
        side = RES_A / 2 + 3.0
        occ = new_comp(root, 'Tepelna pojistka SF129R0')
        module_occs.append(occ)
        tco = occ.component
        b = Builder(tco)
        b.box(-TCO_L / 2, -side - TCO_W, -TCO_T, TCO_L / 2, -side, 0, NEW, 'TCO')
        occ = new_comp(root, 'NTC 100k')
        module_occs.append(occ)
        ntc = occ.component
        b = Builder(ntc)
        b.box(-NTC_L / 2, side, -NTC_D, NTC_L / 2, side + NTC_D, 0, NEW, 'NTC')

        # ---- distancni sloupky ke dnu boxu ----
        occ = new_comp(root, 'Sloupky M3')
        module_occs.append(occ)
        so = occ.component
        b = Builder(so)
        for sx in (-1, 1):
            for sy in (-1, 1):
                b.cyl(sx * STANDOFF_X, sy * STANDOFF_Y, STANDOFF_D / 2, -STANDOFF_H, 0, NEW, 'Sloupek')
                b.cyl(sx * STANDOFF_X, sy * STANDOFF_Y, 1.25, -STANDOFF_H, 0, CUT)

        # ---- ventilator ----
        x1 = -HS_L / 2
        x_out = x1 - DUCT_L
        fin_box = (-HS_W / 2, HS_W / 2, HS_BASE, HS_BASE + FIN_H)
        if FAN_TYPE == 'axial':
            occ = new_comp(root, 'Ventilator %dx%dx%d 24V' % (AX_SIZE, AX_SIZE, AX_THICK))
            module_occs.append(occ)
            fan = occ.component
            b = Builder(fan)
            s = AX_SIZE / 2
            zc = HS_BASE + FIN_H / 2
            fb = b.loft(x_out - AX_THICK, (-s, s, zc - s, zc + s), x_out, (-s, s, zc - s, zc + s),
                        'Ventilator')
            hole = b.loft(x_out - AX_THICK, (-s + 2, s - 2, zc - s + 2, zc + s - 2),
                          x_out, (-s + 2, s - 2, zc - s + 2, zc + s - 2), 'tmp')
            hollow(fan, fb, hole)
            out_box = (-s, s, zc - s, zc + s)
        else:
            occ = new_comp(root, 'Ventilator 5015 24V')
            module_occs.append(occ)
            fan = occ.component
            b = Builder(fan)
            r = FAN_D / 2
            z0 = HS_BASE + FIN_H / 2 - FAN_H / 2          # vydech na stred zeber
            cx = x_out - r - 1.0
            y_out0, y_out1 = r - FAN_OUT_W, r                # tangencialni vydech
            b.cyl(cx, 0, r, z0, z0 + FAN_H, NEW, 'Ventilator 5015')
            b.box(cx, y_out0, z0, x_out, y_out1, z0 + FAN_H, JOIN)
            b.cyl(cx, 0, 14, z0 + FAN_H - 1, z0 + FAN_H, CUT)                     # sani
            b.cyl(cx, 0, 8, z0 + FAN_H - 1, z0 + FAN_H, JOIN)                     # naboj
            b.box(x_out - 8, y_out0 + 1.2, z0 + 1.2, x_out, y_out1 - 1.2, z0 + FAN_H - 1.2, CUT)
            out_box = (y_out0, y_out1, z0, z0 + FAN_H)

        # ---- kryt z vydechu do zeber ----
        occ = new_comp(root, 'Kryt (tisk)')
        module_occs.append(occ)
        du = occ.component
        b = Builder(du)

        def grow(r4, w):
            return (r4[0] - w, r4[1] + w, r4[2] - w, r4[3] + w)

        outer = b.loft(x_out, grow(out_box, WALL), x1, grow(fin_box, WALL), 'Kryt')
        inner = b.loft(x_out, out_box, x1, fin_box, 'tmp')
        hollow(du, outer, inner)

        # ---- rozmery modulu (bez civky) ----
        bb = None
        for o in module_occs:
            for body in o.component.bRepBodies:   # komponenty maji jednotkovou transformaci
                ob = body.boundingBox
                if bb is None:
                    bb = adsk.core.BoundingBox3D.create(ob.minPoint.copy(), ob.maxPoint.copy())
                else:
                    bb.combine(ob)
        mod_x = (bb.maxPoint.x - bb.minPoint.x) * 10
        mod_y = (bb.maxPoint.y - bb.minPoint.y) * 10
        mod_z = (bb.maxPoint.z - bb.minPoint.z) * 10

        # ---- civka pro porovnani (stoji na dne boxu, osa v Y) ----
        occ = new_comp(root, 'Civka 1 kg (pro porovnani)')
        sp = occ.component
        b = Builder(sp)
        spool_y = bb.maxPoint.y * 10 + SPOOL_GAP + SPOOL_W / 2
        spool_z = -STANDOFF_H + SPOOL_D / 2
        b.cyl_y(0, spool_y, spool_z, SPOOL_D / 2, SPOOL_W, NEW, 'Civka')
        b.cyl_y(0, spool_y, spool_z, 27.0, SPOOL_W, CUT)   # otvor ~54 mm

        # ---- vzhled ----
        paint(hs, find_appearance(app, design, ['aluminum', 'satin']))
        paint(res, find_appearance(app, design, ['aluminum', 'anodized']))
        paint(tco, find_appearance(app, design, ['brass']))
        paint(ntc, find_appearance(app, design, ['plastic', 'black']))
        paint(so, find_appearance(app, design, ['brass']))
        paint(fan, find_appearance(app, design, ['plastic', 'black']))
        paint(du, find_appearance(app, design, ['plastic', 'white']), opacity=0.45)
        paint(sp, find_appearance(app, design, ['plastic', 'blue']), opacity=0.25)

        # ---- nahled a rozmery do souboru ----
        here = os.path.dirname(os.path.realpath(__file__))
        txt = ('Topny modul (bez civky): %.0f x %.0f x %.0f mm (X smer proudeni, Y, Z vcetne sloupku)\n'
               'Chladic %.0f x %.0f x %.0f, rezistor HS50 %.1f x %.1f x %.1f, ventilator %s, sloupky %.0f mm\n'
               'Civka pro porovnani: D %.0f x %.0f mm\n'
               % (mod_x, mod_y, mod_z, HS_L, HS_W, HS_H, RES_B, RES_A, RES_C,
                  FAN_TYPE, STANDOFF_H, SPOOL_D, SPOOL_W))
        saved = ''
        try:
            with open(os.path.join(here, 'rozmery.txt'), 'w') as f:
                f.write(txt)
            vp = app.activeViewport
            cam = vp.camera
            cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
            cam.isSmoothTransition = False
            vp.camera = cam
            vp.fit()
            vp.saveAsImageFile(os.path.join(here, 'nahled.png'), 1600, 1000)
            cam = vp.camera
            cam.viewOrientation = adsk.core.ViewOrientations.FrontViewOrientation
            cam.isSmoothTransition = False
            vp.camera = cam
            vp.fit()
            vp.saveAsImageFile(os.path.join(here, 'nahled_zepredu.png'), 1600, 1000)
            cam = vp.camera
            cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
            cam.isSmoothTransition = False
            vp.camera = cam
            vp.fit()
            saved = '\nNahled a rozmery ulozeny vedle skriptu.'
        except Exception:
            saved = '\nNahled se nepodarilo ulozit:\n' + traceback.format_exc()

        ui.messageBox('Hotovo: topny modul je v novem dokumentu.\n\n' + txt +
                      '\nKryt a civka jsou pruhledne. Rozmery zmenis v sekci PARAMETRY skriptu.' + saved)
    except Exception:
        if ui:
            ui.messageBox('Chyba skriptu:\n{}'.format(traceback.format_exc()))
