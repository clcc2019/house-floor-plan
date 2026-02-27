"""
两层轻奢别墅 — 3D透视渲染效果图
使用 Pillow + numpy 实现简易3D渲染：
  - 真实透视投影
  - 材质纹理（墙面、玻璃、金属、石材）
  - 光照模型（环境光 + 方向光 + 阴影）
  - 天空、景观
参考 view.jpg 风格：现代简约，白墙+深色线条+大面积玻璃+玻璃栏杆阳台
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math, os, random

OUT = os.path.join(os.getcwd(), "docs", "images")
os.makedirs(OUT, exist_ok=True)
W, H = 2400, 1600


class Camera:
    def __init__(self, pos, target, up=(0,1,0), fov=50, w=W, h=H):
        self.pos = np.array(pos, dtype=float)
        self.target = np.array(target, dtype=float)
        self.up = np.array(up, dtype=float)
        self.fov = fov
        self.w = w; self.h = h
        f = self.target - self.pos
        f = f / np.linalg.norm(f)
        r = np.cross(f, self.up); r = r / np.linalg.norm(r)
        u = np.cross(r, f)
        self.f = f; self.r = r; self.u = u
        self.aspect = self.w / self.h
        self.tan_half = math.tan(math.radians(self.fov / 2))

    def project(self, p3d):
        d = np.array(p3d, dtype=float) - self.pos
        z = np.dot(d, self.f)
        if z < 0.01:
            return None
        x = np.dot(d, self.r)
        y = np.dot(d, self.u)
        sx = (x / (z * self.tan_half * self.aspect) + 1) * 0.5 * self.w
        sy = (1 - y / (z * self.tan_half)) * 0.5 * self.h
        return (sx, sy, z)


def project_quad(cam, pts_3d):
    pts2d = []
    for p in pts_3d:
        r = cam.project(p)
        if r is None:
            return None
        pts2d.append((r[0], r[1]))
    return pts2d


def make_sky(w, h):
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(120 + 100*t); g = int(155 + 80*t); b = int(210 + 40*t)
        draw.line([(0, y), (w, y)], fill=(min(r,255), min(g,255), min(b,255)))
    cloud_img = Image.new("RGBA", (w, h), (0,0,0,0))
    cd = ImageDraw.Draw(cloud_img)
    random.seed(42)
    for _ in range(8):
        cx = random.randint(100, w-100); cy = random.randint(50, int(h*0.35))
        for __ in range(5):
            rx = random.randint(40, 120); ry = random.randint(20, 50)
            dx = random.randint(-80, 80); dy = random.randint(-20, 20)
            cd.ellipse([cx+dx-rx, cy+dy-ry, cx+dx+rx, cy+dy+ry],
                       fill=(255, 255, 255, random.randint(30, 70)))
    cloud_img = cloud_img.filter(ImageFilter.GaussianBlur(15))
    img.paste(Image.alpha_composite(img.convert("RGBA"), cloud_img).convert("RGB"))
    return img


def make_wall_texture(w, h, base_color=(240, 235, 225), noise_level=5):
    arr = np.full((h, w, 3), base_color, dtype=np.uint8)
    noise = np.random.randint(-noise_level, noise_level+1, (h, w, 3))
    arr = np.clip(arr.astype(int) + noise, 0, 255).astype(np.uint8)
    for y in range(h):
        factor = 1.0 - (y / h) * 0.08
        arr[y] = np.clip(arr[y] * factor, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def make_glass_texture(w, h, tint=(80, 130, 170)):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / h
        for c in range(3):
            v = tint[c] + int(40 * (1-t)) + int(30 * math.sin(t * math.pi))
            arr[y, :, c] = min(255, max(0, v))
    hl_x = int(w * 0.15); hl_w = max(1, int(w * 0.08))
    for x in range(hl_x, min(hl_x + hl_w, w)):
        t = (x - hl_x) / hl_w
        alpha = 0.15 * math.sin(t * math.pi)
        arr[:, x] = np.clip(arr[:, x].astype(float) + 255 * alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def make_dark_texture(w, h, base_color=(55, 52, 48)):
    arr = np.full((h, w, 3), base_color, dtype=np.uint8)
    noise = np.random.randint(-3, 4, (h, w, 3))
    return Image.fromarray(np.clip(arr.astype(int) + noise, 0, 255).astype(np.uint8))


def draw_textured_quad(img, pts2d, texture, alpha=255):
    if pts2d is None or len(pts2d) < 4:
        return
    xs = [p[0] for p in pts2d]; ys = [p[1] for p in pts2d]
    x0, x1 = max(0, int(min(xs))), min(img.width, int(max(xs))+1)
    y0, y1 = max(0, int(min(ys))), min(img.height, int(max(ys))+1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    poly = [(int(p[0]), int(p[1])) for p in pts2d]
    md.polygon(poly, fill=alpha)
    tex_resized = texture.resize((x1-x0, y1-y0), Image.LANCZOS)
    tex_full = Image.new("RGB", img.size, (0,0,0))
    tex_full.paste(tex_resized, (x0, y0))
    img.paste(Image.composite(tex_full, img, mask))


def draw_solid_quad(draw, pts2d, color, outline=None, width=1):
    if pts2d is None or len(pts2d) < 4:
        return
    poly = [(int(p[0]), int(p[1])) for p in pts2d]
    draw.polygon(poly, fill=color, outline=outline, width=width)


# 建筑尺寸（米）
BW = 14.0; BD = 11.0
F1H = 3.6; F2H = 3.3; SLAB = 0.18; PARAPET = 0.6; BASE_H = 0.45
F1_TOP = F1H; F2_BOT = F1_TOP + SLAB; F2_TOP = F2_BOT + F2H
ROOF = F2_TOP + SLAB; TOP = ROOF + PARAPET
RH_START = BW * 0.62; RH_EXTRA = 1.3; RH_TOP = TOP + RH_EXTRA


def south_face(x0, y0, x1, y1):
    return [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)]

def east_face(z0, y0, z1, y1):
    return [(BW, y0, z0), (BW, y0, z1), (BW, y1, z1), (BW, y1, z0)]

def roof_face(x0, z0, x1, z1, y):
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def _draw_window(cam, img, x, y, w, h, face_fn, divs_v=2, divs_h=1, glass_tint=(75,125,165)):
    ft = 0.06
    frame = project_quad(cam, face_fn(x-ft, y-ft, x+w+ft, y+h+ft))
    draw = ImageDraw.Draw(img)
    draw_solid_quad(draw, frame, (55, 52, 48))
    glass = project_quad(cam, face_fn(x, y, x+w, y+h))
    draw_textured_quad(img, glass, make_glass_texture(200, 300, glass_tint))
    draw = ImageDraw.Draw(img)
    for i in range(1, divs_v):
        frac = i * w / divs_v
        p3a = list(face_fn(x+frac, y, x+frac, y+h))
        p1 = cam.project(p3a[0]); p2 = cam.project(p3a[3])
        if p1 and p2:
            draw.line([(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1]))], fill=(55,52,48), width=2)
    for i in range(1, divs_h):
        frac = i * h / divs_h
        p3a = list(face_fn(x, y+frac, x+w, y+frac))
        p1 = cam.project(p3a[0]); p2 = cam.project(p3a[1])
        if p1 and p2:
            draw.line([(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1]))], fill=(55,52,48), width=2)


def _draw_tree(draw, cam, pos3d, trunk_h=2.5, crown_r=1.2, color=(55,110,45)):
    base = cam.project(pos3d)
    top_p = cam.project((pos3d[0], pos3d[1]+trunk_h, pos3d[2]))
    if not base or not top_p:
        return
    bx, by = int(base[0]), int(base[1])
    tx, ty = int(top_p[0]), int(top_p[1])
    trunk_w = max(4, int(abs(bx-tx)*0.08+4))
    draw.rectangle([bx-trunk_w, ty, bx+trunk_w, by], fill=(100, 75, 55))
    scale = max(20, int(crown_r * 600 / base[2]))
    for dy, r, cs in [(0, scale, 0), (-int(scale*0.3), int(scale*0.9), 12),
                       (-int(scale*0.6), int(scale*0.65), 22)]:
        c = tuple(min(255, color[i]+cs) for i in range(3))
        draw.ellipse([tx-int(r*1.1), ty+dy-int(r*0.8), tx+int(r*1.1), ty+dy+int(r*0.8)], fill=c)


def _draw_bush(draw, cam, pos3d, size=0.5, color=(65,125,55)):
    bp = cam.project(pos3d)
    if not bp:
        return
    bpx, bpy = int(bp[0]), int(bp[1])
    s = max(10, int(size * 500 / bp[2]))
    for dx, rx, ry, cs in [(-s//2, s//2, s//3, -5), (0, int(s*0.6), int(s*0.4), 0),
                            (s//2, s//2, s//3, -5)]:
        c = tuple(min(255, max(0, color[i]+cs)) for i in range(3))
        draw.ellipse([bpx+dx-rx, bpy-ry, bpx+dx+rx, bpy+ry//2], fill=c)


def _add_glow(img, x, y, radius=25, color=(255,240,200), alpha=30):
    glow = Image.new("RGBA", img.size, (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([x-radius, y-radius, x+radius, y+radius], fill=(*color, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(radius//2))
    return Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")


def _get_fonts():
    try:
        ft = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 42)
        fs = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
    except:
        ft = ImageFont.load_default()
        fs = ImageFont.load_default()
    return ft, fs


# ═══════════════════════════════════════════════════════════
#  南立面正面透视效果图
# ═══════════════════════════════════════════════════════════

def generate_south_perspective():
    cam = Camera(pos=(BW/2, F1H*0.8, -22), target=(BW/2, F1H*0.9, 0), fov=42)
    img = make_sky(W, H)
    draw = ImageDraw.Draw(img)

    # 远山
    for layer, (base, amp, freq, phase, color) in enumerate([
        (H*0.32, 80, [6,10,15], [0,1,2], (140,155,140)),
        (H*0.36, 60, [5,8], [0.5,2], (160,172,158)),
    ]):
        pts = []
        for i in range(W+1):
            t = i / W
            y_off = sum(a * math.sin(t*f+p) for a, f, p in
                        zip([amp*0.6/(j+1) for j in range(len(freq))], freq, phase))
            pts.append((i, int(base - y_off)))
        pts += [(W, H//2), (0, H//2)]
        draw.polygon(pts, fill=color)

    # 地面 — 先画一个大区域
    # 建筑底部位置
    base_pt = cam.project((BW/2, 0, 0))
    gy = int(base_pt[1]) if base_pt else int(H*0.7)
    draw.rectangle([0, gy, W, H], fill=(110, 145, 95))

    # 院子
    yard = project_quad(cam, south_face(-2, -0.01, BW+2, 0))
    if yard:
        draw_solid_quad(draw, yard, (195, 185, 165))

    # ── 建筑 ──
    # 一层底座
    draw_textured_quad(img, project_quad(cam, south_face(0, 0, BW, BASE_H)),
                       make_dark_texture(600, 100, (55, 52, 48)))
    # 一层墙
    draw_textured_quad(img, project_quad(cam, south_face(0, BASE_H, BW, F1_TOP)),
                       make_wall_texture(600, 400, (242, 237, 228)))
    # 腰线
    draw_textured_quad(img, project_quad(cam, south_face(-0.05, F1_TOP-0.05, BW+0.05, F2_BOT+0.05)),
                       make_dark_texture(600, 50, (65, 60, 55)))
    # 二层墙
    draw_textured_quad(img, project_quad(cam, south_face(0, F2_BOT, BW, F2_TOP)),
                       make_wall_texture(600, 400, (245, 240, 230)))
    # 女儿墙
    draw_textured_quad(img, project_quad(cam, south_face(0, ROOF, BW, TOP)),
                       make_wall_texture(600, 100, (235, 230, 220)))
    draw = ImageDraw.Draw(img)
    # 压顶
    draw_solid_quad(draw, project_quad(cam, south_face(-0.08, TOP-0.1, BW+0.08, TOP)), (60, 56, 52))
    # 右侧挑高
    draw_textured_quad(img, project_quad(cam, south_face(RH_START, TOP, BW, RH_TOP)),
                       make_wall_texture(300, 200, (238, 233, 223)))
    draw = ImageDraw.Draw(img)
    draw_solid_quad(draw, project_quad(cam, south_face(RH_START-0.05, RH_TOP-0.08, BW+0.05, RH_TOP)),
                    (60, 56, 52))

    # ── 窗户（优化布局：南面大落地窗左侧 + 玄关石材门右侧）──
    # 一层：超大落地窗（客厅，X=1.0~6.0m）
    _draw_window(cam, img, 1.0, BASE_H+0.1, 5.0, 2.4, south_face, divs_v=4)
    # 二层窗户
    _draw_window(cam, img, 1.2, F2_BOT+0.3, 2.0, F2H-0.6, south_face, divs_v=2)
    _draw_window(cam, img, 5.0, F2_BOT+0.3, 3.0, F2H-0.6, south_face, divs_v=3)
    _draw_window(cam, img, 9.3, F2_BOT+0.3, 2.0, F2H-0.6, south_face, divs_v=2)
    # 挑高窗
    _draw_window(cam, img, RH_START+0.4, TOP+0.2, BW-RH_START-0.8, RH_EXTRA-0.4,
                 south_face, divs_v=4)

    draw = ImageDraw.Draw(img)

    # ── 右侧深色石材区域（参考view.jpg）──
    draw_textured_quad(img, project_quad(cam, south_face(8.2, BASE_H, BW, F1_TOP)),
                       make_dark_texture(400, 400, (50, 45, 38)))
    draw = ImageDraw.Draw(img)

    # ── 大门（玄关石材门，右侧）──
    door_x, door_w, door_h = 9.5, 1.2, 2.8
    draw_solid_quad(draw, project_quad(cam, south_face(door_x-0.1, BASE_H, door_x+door_w+0.1, BASE_H+door_h+0.1)),
                    (45, 42, 38))
    draw_textured_quad(img, project_quad(cam, south_face(door_x, BASE_H, door_x+door_w, BASE_H+door_h)),
                       make_dark_texture(150, 300, (50, 45, 40)))
    draw = ImageDraw.Draw(img)
    for i in range(4):
        py = BASE_H + 0.2 + i * 0.65
        for j in range(2):
            px = door_x + 0.08 + j * 0.68
            draw_solid_quad(draw, project_quad(cam, south_face(px, py, px+0.58, py+0.55)),
                            (60, 55, 50), outline=(50, 45, 40))
    hp = cam.project((door_x + door_w - 0.2, BASE_H + door_h*0.45, 0))
    if hp:
        draw.ellipse([int(hp[0])-4, int(hp[1])-8, int(hp[0])+4, int(hp[1])+8], fill=(200, 175, 120))

    # 雨棚
    canopy_x, canopy_w = door_x - 0.8, 3.0
    canopy_y = BASE_H + door_h + 0.15
    draw_solid_quad(draw, project_quad(cam, south_face(canopy_x, canopy_y, canopy_x+canopy_w, canopy_y+0.12)),
                    (55, 52, 48))
    for px in [canopy_x+0.1, canopy_x+canopy_w-0.2]:
        draw_solid_quad(draw, project_quad(cam, south_face(px, BASE_H, px+0.1, canopy_y)), (55, 52, 48))

    # 台阶
    for i in range(4):
        sx = door_x - 0.3 - i*0.15; sw = door_w + 0.6 + i*0.3
        sy = -i * 0.12
        c = 195 - i*10
        draw_solid_quad(draw, project_quad(cam, south_face(sx, sy, sx+sw, sy+0.12)), (c, c-5, c-12))

    # ── 阳台玻璃栏杆 ──
    railing_bot = F1_TOP + 0.25; railing_top = F2_BOT
    draw_solid_quad(draw, project_quad(cam, south_face(0.2, railing_top-0.04, BW-0.2, railing_top)),
                    (100, 100, 100))
    n_panels = 8
    for i in range(n_panels+1):
        px = 0.3 + i * (BW-0.6) / n_panels
        draw_solid_quad(draw, project_quad(cam, south_face(px-0.02, railing_bot, px+0.02, railing_top)),
                        (90, 90, 90))
    for i in range(n_panels):
        px0 = 0.3 + i * (BW-0.6) / n_panels + 0.04
        px1 = 0.3 + (i+1) * (BW-0.6) / n_panels - 0.04
        gp = project_quad(cam, south_face(px0, railing_bot+0.04, px1, railing_top-0.06))
        if gp:
            draw_textured_quad(img, gp, make_glass_texture(100, 80, (160, 190, 210)), alpha=100)
    draw = ImageDraw.Draw(img)

    # ── 景观 ──
    _draw_tree(draw, cam, (-3, 0, -1), 3.0, 1.5, (50, 105, 40))
    _draw_tree(draw, cam, (-1.5, 0, -2), 2.0, 0.9, (60, 115, 48))
    _draw_tree(draw, cam, (BW+3, 0, -1), 3.5, 1.8, (48, 100, 38))
    _draw_tree(draw, cam, (BW+1.5, 0, -2), 2.0, 1.0, (55, 110, 45))
    for bpos in [(1,0,-0.5), (5,0,-0.5), (9,0,-0.5), (13,0,-0.5)]:
        _draw_bush(draw, cam, bpos, 0.5, (65, 125, 55))

    # 花盆
    for fx in [2.0, 4.5, 7.0, 9.5, 12.0]:
        fp = cam.project((fx, railing_bot-0.05, 0))
        if fp:
            px, py = int(fp[0]), int(fp[1])
            draw.rectangle([px-8, py-12, px+8, py], fill=(170, 110, 75))
            draw.ellipse([px-12, py-22, px+12, py-8], fill=(70, 140, 55))

    # 门灯光晕
    for lx in [door_x - 0.3, door_x + door_w + 0.3]:
        lp = cam.project((lx, BASE_H + door_h * 0.7, 0))
        if lp:
            px, py = int(lp[0]), int(lp[1])
            img = _add_glow(img, px, py, 25, (255,240,200), 30)
            draw = ImageDraw.Draw(img)
            draw.rectangle([px-4, py-8, px+4, py+2], fill=(220, 200, 160), outline=(180,160,120))

    # 地面阴影
    shadow = Image.new("RGBA", (W, H), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.polygon([(0, gy), (int(W*0.05), H), (int(W*0.95), H), (W, gy)], fill=(0,0,0,20))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 标题
    ft, fs = _get_fonts()
    draw.text((W//2, 50), "南立面透视效果图", fill=(50, 65, 80), font=ft, anchor="mt")
    draw.text((W//2, 100), "现代简约别墅  |  14m × 11m  |  3主卧+2次卧  |  建筑面积 308㎡",
              fill=(120, 135, 150), font=fs, anchor="mt")

    img = img.filter(ImageFilter.SHARPEN)
    img.save(f"{OUT}/南立面透视效果图.png", quality=95)
    print("  ✓ 南立面透视效果图")


# ═══════════════════════════════════════════════════════════
#  东南角透视效果图
# ═══════════════════════════════════════════════════════════

def generate_southeast_perspective():
    cam = Camera(pos=(-8, F1H*1.0, -18), target=(BW*0.45, F1H*0.7, BD*0.3), fov=48)
    img = make_sky(W, H)
    draw = ImageDraw.Draw(img)

    # 远山
    mpts = [(0, H//2)]
    for i in range(W+1):
        t = i / W
        y_off = 0.5*math.sin(t*5+0.5)*70 + 0.3*math.sin(t*9+2)*60
        mpts.append((i, int(H*0.33 - y_off)))
    mpts.append((W, H//2))
    draw.polygon(mpts, fill=(150, 162, 148))

    # 地面
    base_pt = cam.project((BW/2, 0, BD/2))
    gy = int(base_pt[1]) if base_pt else int(H*0.65)
    draw.rectangle([0, gy-30, W, H], fill=(110, 145, 95))

    # 院子
    yard = project_quad(cam, [(-1, 0.01, -2), (BW+1, 0.01, -2), (BW+1, 0.01, 0), (-1, 0.01, 0)])
    if yard:
        draw_solid_quad(draw, yard, (195, 185, 165))

    # ── 南面 ──
    draw_textured_quad(img, project_quad(cam, south_face(0, 0, BW, BASE_H)),
                       make_dark_texture(600, 80, (55, 52, 48)))
    draw_textured_quad(img, project_quad(cam, south_face(0, BASE_H, BW, F1_TOP)),
                       make_wall_texture(600, 400, (242, 237, 228)))
    draw_textured_quad(img, project_quad(cam, south_face(-0.05, F1_TOP-0.05, BW+0.05, F2_BOT+0.05)),
                       make_dark_texture(600, 40, (62, 58, 53)))
    draw_textured_quad(img, project_quad(cam, south_face(0, F2_BOT, BW, F2_TOP)),
                       make_wall_texture(600, 400, (245, 240, 230)))
    draw_textured_quad(img, project_quad(cam, south_face(0, ROOF, BW, TOP)),
                       make_wall_texture(600, 80, (235, 230, 220)))
    draw = ImageDraw.Draw(img)
    draw_solid_quad(draw, project_quad(cam, south_face(-0.06, TOP-0.08, BW+0.06, TOP)), (58, 55, 50))
    draw_textured_quad(img, project_quad(cam, south_face(RH_START, TOP, BW, RH_TOP)),
                       make_wall_texture(300, 200, (238, 233, 223)))
    draw = ImageDraw.Draw(img)
    draw_solid_quad(draw, project_quad(cam, south_face(RH_START-0.05, RH_TOP-0.06, BW+0.05, RH_TOP)),
                    (58, 55, 50))

    # ── 东面 ──
    draw_textured_quad(img, project_quad(cam, east_face(0, 0, BD, BASE_H)),
                       make_dark_texture(500, 80, (50, 47, 43)))
    draw_textured_quad(img, project_quad(cam, east_face(0, BASE_H, BD, F1_TOP)),
                       make_wall_texture(500, 400, (228, 223, 215)))
    draw_textured_quad(img, project_quad(cam, east_face(-0.05, F1_TOP-0.05, BD+0.05, F2_BOT+0.05)),
                       make_dark_texture(500, 40, (58, 54, 49)))
    draw_textured_quad(img, project_quad(cam, east_face(0, F2_BOT, BD, F2_TOP)),
                       make_wall_texture(500, 400, (232, 227, 218)))
    draw_textured_quad(img, project_quad(cam, east_face(0, ROOF, BD, TOP)),
                       make_wall_texture(500, 80, (225, 220, 212)))
    draw = ImageDraw.Draw(img)
    draw_solid_quad(draw, project_quad(cam, east_face(-0.05, TOP-0.08, BD+0.05, TOP)), (55, 52, 47))
    draw_textured_quad(img, project_quad(cam, east_face(0, TOP, BD*0.4, RH_TOP)),
                       make_wall_texture(200, 200, (230, 225, 216)))
    draw = ImageDraw.Draw(img)
    draw_solid_quad(draw, project_quad(cam, east_face(-0.05, RH_TOP-0.06, BD*0.4+0.05, RH_TOP)),
                    (55, 52, 47))

    # 屋顶
    draw_solid_quad(draw, project_quad(cam, roof_face(0, 0, BW, BD, TOP)), (200, 195, 185),
                    outline=(180,175,165))
    draw_solid_quad(draw, project_quad(cam, roof_face(RH_START, 0, BW, BD*0.4, RH_TOP)),
                    (195, 190, 180), outline=(175,170,160))

    # ── 南面窗户（优化布局）──
    _draw_window(cam, img, 1.0, BASE_H+0.1, 5.0, 2.4, south_face, divs_v=4)
    _draw_window(cam, img, 1.2, F2_BOT+0.3, 2.0, F2H-0.6, south_face, divs_v=2)
    _draw_window(cam, img, 5.0, F2_BOT+0.3, 3.0, F2H-0.6, south_face, divs_v=3)
    _draw_window(cam, img, 9.3, F2_BOT+0.3, 2.0, F2H-0.6, south_face, divs_v=2)

    # 右侧深色石材区域
    draw_textured_quad(img, project_quad(cam, south_face(8.2, BASE_H, BW, F1_TOP)),
                       make_dark_texture(400, 400, (50, 45, 38)))

    # ── 东面窗户（主卧1窗+楼梯窗）──
    def east_face_win(z0, y0, z1, y1):
        return [(BW, y0, z0), (BW, y0, z1), (BW, y1, z1), (BW, y1, z0)]
    # 一层：主卧1东窗(2.5~6.0m) + 楼梯间窗(7.7~9.7m)
    _draw_window(cam, img, 2.5, 0.7, 3.5, 2.0, east_face_win, divs_v=3, glass_tint=(70,118,155))
    _draw_window(cam, img, 7.7, 0.7, 2.0, 1.8, east_face_win, divs_v=2, glass_tint=(70,118,155))
    # 二层：次卧2东窗(1.5~3.5m) + 主卧3东窗(8.5~10.5m)
    _draw_window(cam, img, 1.5, F2_BOT+0.3, 2.0, F2H-0.8, east_face_win, divs_v=2, glass_tint=(70,118,155))
    _draw_window(cam, img, 8.5, F2_BOT+0.3, 2.0, F2H-0.6, east_face_win, divs_v=2, glass_tint=(70,118,155))

    draw = ImageDraw.Draw(img)

    # 大门（玄关石材门，右侧 X=9.5~10.7m）
    draw_solid_quad(draw, project_quad(cam, south_face(9.5-0.1, BASE_H, 9.5+1.2+0.1, BASE_H+2.8+0.1)),
                    (42, 40, 36))
    draw_textured_quad(img, project_quad(cam, south_face(9.5, BASE_H, 10.7, BASE_H+2.8)),
                       make_dark_texture(120, 250, (48, 43, 38)))
    draw = ImageDraw.Draw(img)

    # 阳台栏杆
    railing_bot = F1_TOP + 0.25; railing_top = F2_BOT
    draw_solid_quad(draw, project_quad(cam, south_face(0.2, railing_top-0.04, BW-0.2, railing_top)),
                    (95, 95, 95))
    for i in range(9):
        px = 0.3 + i * (BW-0.6) / 8
        draw_solid_quad(draw, project_quad(cam, south_face(px-0.02, railing_bot, px+0.02, railing_top)),
                        (85, 85, 85))
    for i in range(8):
        px0 = 0.3 + i * (BW-0.6) / 8 + 0.04
        px1 = 0.3 + (i+1) * (BW-0.6) / 8 - 0.04
        gp = project_quad(cam, south_face(px0, railing_bot+0.04, px1, railing_top-0.06))
        if gp:
            draw_textured_quad(img, gp, make_glass_texture(80, 60, (155, 185, 205)), alpha=90)
    draw = ImageDraw.Draw(img)

    # 轮廓线
    edge_pairs = [
        ((0,0,0), (0,TOP,0)), ((BW,0,0), (BW,TOP,0)),
        ((0,TOP,0), (BW,TOP,0)), ((0,0,0), (BW,0,0)),
        ((BW,0,0), (BW,0,BD)), ((BW,TOP,0), (BW,TOP,BD)),
        ((BW,0,BD), (BW,TOP,BD)), ((BW,TOP,0), (BW,TOP,BD)),
    ]
    for a, b in edge_pairs:
        p1 = cam.project(a); p2 = cam.project(b)
        if p1 and p2:
            draw.line([(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1]))], fill=(60,58,55), width=2)

    # 景观
    _draw_tree(draw, cam, (-3, 0, -1), 3.0, 1.5, (50, 105, 40))
    _draw_tree(draw, cam, (-1.5, 0, -2), 2.0, 0.9, (60, 115, 48))
    _draw_tree(draw, cam, (BW+3, 0, BD+2), 3.5, 1.8, (48, 100, 38))
    _draw_tree(draw, cam, (BW+1, 0, BD+3), 2.0, 1.0, (55, 110, 45))
    _draw_tree(draw, cam, (-2, 0, BD+1), 2.5, 1.2, (52, 108, 42))
    for bpos in [(1,0,-0.5),(5,0,-0.5),(9,0,-0.5),(13,0,-0.5),
                  (BW+0.5,0,2),(BW+0.5,0,5),(BW+0.5,0,8)]:
        _draw_bush(draw, cam, bpos, 0.5, (65, 125, 55))

    # 标题
    ft, fs = _get_fonts()
    draw.text((W//2, 50), "东南角透视效果图", fill=(50, 65, 80), font=ft, anchor="mt")
    draw.text((W//2, 100), "Southeast Perspective  |  现代简约别墅  |  14m × 11m  |  建筑面积 308㎡",
              fill=(120, 135, 150), font=fs, anchor="mt")

    img = img.filter(ImageFilter.SHARPEN)
    img.save(f"{OUT}/东南角透视效果图.png", quality=95)
    print("  ✓ 东南角透视效果图")


if __name__ == "__main__":
    print("=" * 55)
    print("  3D透视渲染效果图")
    print("=" * 55)
    generate_south_perspective()
    generate_southeast_perspective()
    print("=" * 55)
    print("  完成！")
    print("=" * 55)
