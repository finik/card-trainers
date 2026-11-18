"""
Renders the README images (z-buffered software rasterizer, no GPU or OpenGL needed).
Run:  python3 source/render.py      -> images/
"""
import os, numpy as np, trimesh
from math import radians
import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import trainers as t

PKG = t.PKG
IMG = os.path.join(PKG, "images")
COL = {"body": "#2b2b2e", "logo": "#d1202b", "pips": "#a4a6aa"}

def hexrgb(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)]) / 255.0

# ---------------------------------------------------------------- rasterizer (from kallax-deck-carousel)
def render(items, eye, target, out, W=1600, H=1200, fov=30.0, ss=2, up=(0, 0, 1), bg=(1, 1, 1)):
    """items: list of (trimesh, rgb)"""
    V = []; F = []; C = []; off = 0
    for tm, col in items:
        V.append(tm.vertices); F.append(tm.faces + off); off += len(tm.vertices)
        C.append(np.tile(col, (len(tm.faces), 1)))
    V = np.vstack(V); F = np.vstack(F); C = np.vstack(C)
    tri = V[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1); keep = ln > 1e-12
    tri, n, C = tri[keep], n[keep] / ln[keep, None], C[keep]

    eye = np.array(eye, float); target = np.array(target, float); up = np.array(up, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    flip = np.einsum("ij,ij->i", n, tri.mean(1) - eye) > 0        # two-sided shading
    n[flip] *= -1
    lights = [(np.array([-0.45, -0.75, 0.9]), 0.60), (np.array([0.8, 0.3, 0.5]), 0.25), (-f, 0.20)]
    inten = np.full(len(n), 0.30)
    for L, w in lights:
        L = L / np.linalg.norm(L); inten += w * np.clip(n @ L, 0, None)
    shade = np.clip(C * inten[:, None], 0, 1)

    Ws, Hs = W * ss, H * ss
    P = tri - eye
    x = P @ r; y = P @ u; dep = P @ f
    foc = (Hs / 2) / np.tan(radians(fov) / 2)
    sx = x / dep * foc + Ws / 2; sy = -y / dep * foc + Hs / 2
    zbuf = np.full((Hs, Ws), np.inf); fid = np.full((Hs, Ws), -1, np.int64)
    xmin = np.clip(np.floor(sx.min(1)).astype(int), 0, Ws - 1); xmax = np.clip(np.ceil(sx.max(1)).astype(int), 0, Ws - 1)
    ymin = np.clip(np.floor(sy.min(1)).astype(int), 0, Hs - 1); ymax = np.clip(np.ceil(sy.max(1)).astype(int), 0, Hs - 1)
    vis = (dep.min(1) > 1) & (xmax >= xmin) & (ymax >= ymin)
    for k in np.nonzero(vis)[0]:
        x0, x1, y0, y1 = xmin[k], xmax[k], ymin[k], ymax[k]
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        X = sx[k]; Y = sy[k]
        d = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
        if abs(d) < 1e-9: continue
        w0 = ((Y[1] - Y[2]) * (gx - X[2]) + (X[2] - X[1]) * (gy - Y[2])) / d
        w1 = ((Y[2] - Y[0]) * (gx - X[2]) + (X[0] - X[2]) * (gy - Y[2])) / d
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not m.any(): continue
        zz = 1 / (w0 / dep[k, 0] + w1 / dep[k, 1] + w2 / dep[k, 2])
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = m & (zz < sub)
        if upd.any():
            sub[upd] = zz[upd]
            fid[y0:y1 + 1, x0:x1 + 1][upd] = k
    img = np.ones((Hs, Ws, 3)) * np.array(bg)
    hit = fid >= 0
    img[hit] = shade[fid[hit]]
    # outlines: silhouettes, depth jumps and creases
    nb = np.zeros((Hs, Ws, 3)); nb[hit] = n[fid[hit]]
    edge = np.zeros((Hs, Ws), bool)
    zf = np.where(hit, zbuf, 1e9)
    for dy, dx in ((0, 1), (1, 0)):
        a_h = hit[:Hs - dy, :Ws - dx]; b_h = hit[dy:, dx:]
        za = zf[:Hs - dy, :Ws - dx]; zb = zf[dy:, dx:]
        na = nb[:Hs - dy, :Ws - dx]; nb_ = nb[dy:, dx:]
        jump = np.abs(za - zb) > 0.004 * np.minimum(za, zb) + 0.6
        crease = (np.einsum("ijk,ijk->ij", na, nb_) < 0.82) & a_h & b_h
        e = (a_h != b_h) | ((a_h & b_h) & (jump | crease))
        edge[:Hs - dy, :Ws - dx] |= e
    img[edge] = img[edge] * 0.35
    img = img.reshape(H, ss, W, ss, 3).mean((1, 3))
    fg = np.abs(img - np.array(bg)).sum(2) > 0.02                  # crop to content
    ys, xs = np.nonzero(fg)
    if len(ys):
        pad = int(0.04 * max(H, W))
        img = img[max(ys.min() - pad, 0):min(ys.max() + pad, H), max(xs.min() - pad, 0):min(xs.max() + pad, W)]
    mpimg.imsave(out, np.clip(img, 0, 1))
    print("wrote", os.path.relpath(out, PKG))

# ---------------------------------------------------------------- scenes
def card_items(rank, M):
    """coloured parts of one trainer, moved by the 4x4 matrix M"""
    items = []
    for name, (m, _) in t.trainer(rank).items():
        tm = t.to_tm(m); tm.apply_transform(M)
        items.append((tm, hexrgb(COL[name])))
    return items

def T(x=0, y=0, z=0, rz=0, rx=0):
    R = trimesh.transformations
    return R.translation_matrix((x, y, z)) @ R.rotation_matrix(radians(rz), (0, 0, 1)) @ R.rotation_matrix(radians(rx), (1, 0, 0))

def flat_faces(out):
    """exact 2D artwork: the five fronts and the back"""
    def draw(ax, g, c, bg):
        for p in ([g] if g.geom_type == "Polygon" else g.geoms):
            ax.fill(*p.exterior.xy, color=c, lw=0)
            for i in p.interiors: ax.fill(*i.xy, color=bg, lw=0)
    fig, axs = plt.subplots(1, 6, figsize=(18, 4.6))
    for ax, r in zip(axs, t.RANKS):
        draw(ax, t.card_outline(), COL["body"], COL["body"]); draw(ax, t.pips_face(r), COL["pips"], COL["body"])
    draw(axs[5], t.card_outline(), COL["body"], COL["body"]); draw(axs[5], t.logo(), COL["logo"], COL["body"])
    for ax in axs: ax.set_aspect("equal"); ax.axis("off")
    plt.savefig(out, dpi=220, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print("wrote", os.path.relpath(out, PKG))

if __name__ == "__main__":
    os.makedirs(IMG, exist_ok=True)
    flat_faces(os.path.join(IMG, "faces.png"))

    # hero: the 2..6 laid out face-up, a sixth card flipped to show the back
    items = []
    tilt = (3, -2, 2, -3, 1)
    for i, r in enumerate(t.RANKS):
        items += card_items(r, T(x=(i - 2.5)*74, rz=tilt[i]))
    items += card_items(2, T(x=2.5*74 + 4, rz=-3) @ T(z=t.T, rx=180, rz=180))   # rx flips it, rz turns the logo upright
    render(items, (0, -330, 480), (0, -5, 0), os.path.join(IMG, "hero.png"), W=1800, H=900, fov=34)

    # the five packets squared up into one deck
    items = []
    for i, r in enumerate(t.RANKS):
        items += card_items(r, T(z=i*t.T))
    render(items, (170, -190, 120), (0, 0, 8), os.path.join(IMG, "stack.png"), W=1200, H=1000, fov=26)
