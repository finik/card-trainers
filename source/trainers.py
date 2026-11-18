"""
Cardistry trainers: a deck split into 5 solid packets.
Front: 2..6 of diamonds pips. Back: the finik/finikforge logo (art/finikforge_logo.svg), or just its valknut. Both inlaid INK_LAYERS deep, faces stay flat.
Exports stl/trainers.3mf: one object per trainer, parts body/logo/pips on filaments 1/2/3 (black/red/gray).
Run:  python3 source/trainers.py
"""
import os, re, numpy as np, trimesh
from shapely.geometry import Polygon, box
from shapely import make_valid
from svgelements import SVG, Path, Line, Move, Close
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import affinity
from manifold3d import Manifold, CrossSection

# ---------------- parameters ----------------
CARD_W, CARD_H, CORNER_R = 63.5, 88.9, 3.2      # poker size, 1/8" corners
LAYER, LAYERS = 0.2, 17                          # 3.4 mm, 5 packets = 17 mm deck
INK_LAYERS = 3                                   # colour depth on each face
T, INK = LAYER*LAYERS, LAYER*INK_LAYERS
RANKS = (2, 3, 4, 5, 6)

PIP, PIP_W = 13.0, 9.6                           # diamond pip height, width
PIP_COL, PIP_ROW = 14.5, 28.0                    # pip column / top-row offsets from the card centre

BACK = "logo"                                    # "logo" (full finikforge logo) or "valknut"
LOGO_D = 56.0                                    # logo diameter (card is 63.5 wide)
VK_W, VK_GAP = 46.0, 1.0                         # valknut width, weave gap between its three pieces

# finik/finikforge vk.py: the three interlaced pieces of the valknut (SVG units, y down)
VK_PATHS = [
    "m904.64 970.23-34.05-57.39h-177.4l48.349-82.486-32.12-57.1-112.07 196.98z",
    "m786.91 643.91-32.677 58.183 83.914 147-97.609-0.62816-33.395 56.378 228.63-1.4434z",
    "m557.09 906.42 66.726-0.79259 85.924-148.65 47.261 83.114 65.522 0.73205-114.56-195.54z",
]

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PKG, "stl")
LOGO_SVG = os.path.join(PKG, "art", "finikforge_logo.svg")

# ---------------- 2D helpers ----------------
def cs(g):
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    loops = []
    for p in polys:
        p = orient(p)
        loops.append(list(p.exterior.coords)[:-1])
        loops += [list(i.coords)[:-1] for i in p.interiors]
    return CrossSection(loops)

def card_outline():
    return box(-CARD_W/2 + CORNER_R, -CARD_H/2 + CORNER_R, CARD_W/2 - CORNER_R, CARD_H/2 - CORNER_R).buffer(CORNER_R, 32)

def diamond(h=PIP, w=PIP_W):
    """diamond pip, height h, centred; sides bowed in slightly like a printed card's"""
    n = 12
    top, right = np.array([0, h/2]), np.array([w/2, 0])
    pts = []
    for a, b in ((top, right), (right, -top), (-top, -right), (-right, top)):
        for k in range(n):
            t = k/n
            q = a + (b - a)*t
            pts.append(q*(1 - 0.10*np.sin(np.pi*t)))            # pull the middle of each side towards the centre
    return Polygon(pts)

PIP_LAYOUT = {
    2: [(0, 1), (0, -1)],
    3: [(0, 1), (0, 0), (0, -1)],
    4: [(-1, 1), (1, 1), (-1, -1), (1, -1)],
    5: [(-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1)],
    6: [(-1, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (1, -1)],
}

def pips_face(rank):
    pips = []
    for cx, cy in PIP_LAYOUT[rank]:
        p = diamond()
        if cy < 0: p = affinity.rotate(p, 180, origin=(0, 0))      # bottom half reads upside down, like real cards
        pips.append(affinity.translate(p, cx*PIP_COL, cy*PIP_ROW))
    return unary_union(pips)

def svg_poly(d):
    """SVG path with m/l/h/v/z (relative or absolute) -> polygon, y flipped to point up"""
    toks = re.findall(r"[MmLlHhVvZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    pts, cur, cmd, k = [], np.zeros(2), None, 0
    while k < len(toks):
        if toks[k].isalpha():
            cmd = toks[k]; k += 1
            if cmd in "Zz": continue
        rel = cmd.islower(); c = cmd.lower()
        if c in "ml":
            v = np.array([float(toks[k]), float(toks[k + 1])]); k += 2
            cur = cur + v if rel else v              # cur starts at 0, so a leading relative m works too
            if c == "m": cmd = "l" if rel else "L"
        elif c == "h":
            x = float(toks[k]); k += 1; cur = cur + (x, 0) if rel else np.array([x, cur[1]])
        elif c == "v":
            y = float(toks[k]); k += 1; cur = cur + (0, y) if rel else np.array([cur[0], y])
        pts.append(cur.copy())
    return Polygon([(x, -y) for x, y in pts])

def valknut():
    """the three finikforge pieces, each shrunk by half the gap so the weave reads; centred, VK_W wide"""
    pieces = [orient(svg_poly(d)) for d in VK_PATHS]
    x0, y0, x1, y1 = unary_union(pieces).bounds
    sc = VK_W/(x1 - x0)
    pieces = [affinity.scale(affinity.translate(p, -(x0 + x1)/2, -(y0 + y1)/2), sc, sc, origin=(0, 0)) for p in pieces]
    return unary_union([p.buffer(-VK_GAP/2, join_style=2) for p in pieces])

def logo():
    """finikforge logo: each SVG path filled evenodd, centred, LOGO_D across (at 56 mm: thinnest stroke 0.46, EST./2020)"""
    shapes = []
    for e in SVG.parse(LOGO_SVG).elements():
        if not isinstance(e, Path): continue
        e = Path(e); e.reify()
        g = None
        for sub in e.as_subpaths():
            pts = []
            for seg in sub:
                if isinstance(seg, (Move, Line, Close)): pts.append((seg.end.x, seg.end.y)); continue
                pts += [(q.x, q.y) for q in (seg.point(t) for t in np.linspace(0, 1, 9)[1:])]
            if len(pts) < 3: continue
            q = make_valid(Polygon(pts))
            g = q if g is None else g.symmetric_difference(q)
        if g is not None: shapes.append(g)
    art = unary_union(shapes)
    x0, y0, x1, y1 = art.bounds
    sc = LOGO_D/max(x1 - x0, y1 - y0)
    return affinity.scale(affinity.translate(art, -(x0 + x1)/2, -(y0 + y1)/2), sc, -sc, origin=(0, 0))   # SVG y is down

# ---------------- solids ----------------
def ext(g, z0, z1): return Manifold.extrude(cs(g), z1 - z0).translate((0, 0, z0))

def to_tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts))

def trainer(rank):
    """printed pips-up: logo on the bed side (mirrored so it reads right when flipped), diamonds on top.
    returns {part: (solid, filament)}"""
    logo_ink = ext(affinity.scale(logo() if BACK == "logo" else valknut(), xfact=-1, origin=(0, 0)), 0, INK)
    pips_ink = ext(pips_face(rank), T - INK, T)
    body = ext(card_outline(), 0, T) - logo_ink - pips_ink
    return {"body": (body, FIL_BODY), "logo": (logo_ink, FIL_LOGO), "pips": (pips_ink, FIL_PIPS)}

# ---------------- 3MF: one object per trainer, one part per colour ----------------
FIL_BODY, FIL_LOGO, FIL_PIPS = 1, 2, 3          # filament slots: black, red, gray
BED, PLATE_GAP = 256.0, 8.0

def plate_xy(i):
    """3 across on top, 2 below, centred on the bed"""
    dx, dy = CARD_W + PLATE_GAP, CARD_H + PLATE_GAP
    row, col = divmod(i, 3)
    n = min(3, len(RANKS) - 3*row)
    return BED/2 + (col - (n - 1)/2)*dx, BED/2 + (0.5 - row)*dy

def mesh_xml(oid, tm):
    v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in tm.vertices)
    f = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tm.faces)
    return f'<object id="{oid}" type="model"><mesh><vertices>{v}</vertices><triangles>{f}</triangles></mesh></object>'

def export_3mf(path, cards):
    """cards: [(name, {part: (solid, filament)})]; parts are 3MF components, filaments set in Bambu's model_settings.config"""
    import zipfile
    res, build, cfg, oid = [], [], [], 1
    for i, (name, parts) in enumerate(cards):
        ids = []
        for m, _ in parts.values():
            tm = to_tm(m); assert tm.is_watertight, name
            res.append(mesh_xml(oid, tm)); ids.append(oid); oid += 1
        res.append(f'<object id="{oid}" type="model"><components>'
                   + "".join(f'<component objectid="{p}"/>' for p in ids) + '</components></object>')
        x, y = plate_xy(i)
        build.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {x:.3f} {y:.3f} 0" printable="1"/>')
        cfg.append(f'<object id="{oid}"><metadata key="name" value="{name}"/><metadata key="extruder" value="1"/>'
                   + "".join(f'<part id="{p}" subtype="normal_part"><metadata key="name" value="{name}_{part}"/>'
                             f'<metadata key="extruder" value="{fil}"/></part>'
                             for p, (part, (_, fil)) in zip(ids, parts.items()))
                   + '</object>')
        oid += 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", f'<?xml version="1.0" encoding="UTF-8"?>\n<config>{"".join(cfg)}</config>')

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cards = []
    for r in RANKS:
        parts = trainer(r)
        cards.append((f"{r}_of_diamonds", parts))
        print(f"{r} of diamonds: " + ", ".join(f"{k} {m.volume():.0f} mm3 (filament {f})" for k, (m, f) in parts.items()))
    export_3mf(os.path.join(OUT, "trainers.3mf"), cards)
    print("wrote stl/trainers.3mf")
