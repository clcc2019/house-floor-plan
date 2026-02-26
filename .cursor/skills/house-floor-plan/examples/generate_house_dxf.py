"""
两层轻奢别墅 AutoCAD DXF 图纸 + 高质量预览图
参考风格：白底 + 淡蓝灰填充 + 黑色实心墙体 + 黑色细线家具
配置：3主卧 + 2次卧 | 占地 14m × 11m | 建筑面积 ≈308㎡
"""

import os
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, FancyArrowPatch
import numpy as np

plt.rcParams["font.sans-serif"] = ["PingFang HK", "Hiragino Sans GB", "Heiti TC", "STHeiti", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ACI colors for DXF
BLACK = 250
WHITE = 7
LIGHT_FILL = 150
RED = 1
GRAY = 8


# ══════════════════════════════════════════════
#  DXF 生成部分
# ══════════════════════════════════════════════

def setup_layers(doc):
    doc.layers.add("WALL", color=BLACK)
    doc.layers.add("WALL-FILL", color=BLACK)
    doc.layers.add("ROOM-FILL", color=LIGHT_FILL)
    doc.layers.add("DOOR", color=BLACK)
    doc.layers.add("WINDOW", color=BLACK)
    doc.layers.add("STAIRS", color=GRAY)
    doc.layers.add("TEXT", color=BLACK)
    doc.layers.add("DIM", color=RED)
    doc.layers.add("FIXTURE", color=GRAY)
    doc.layers.add("FURNITURE", color=GRAY)
    doc.layers.add("TITLE", color=BLACK)
    doc.layers.add("INFO", color=BLACK)


def wall_filled_h(msp, x, y, length, t=240):
    pts = [(x, y), (x+length, y), (x+length, y+t), (x, y+t)]
    h = msp.add_hatch(color=BLACK, dxfattribs={"layer": "WALL-FILL"})
    h.paths.add_polyline_path(pts + [pts[0]], is_closed=True)
    msp.add_lwpolyline(pts + [pts[0]], close=True, dxfattribs={"layer": "WALL", "lineweight": 50, "color": BLACK})


def wall_filled_v(msp, x, y, length, t=240):
    pts = [(x, y), (x+t, y), (x+t, y+length), (x, y+length)]
    h = msp.add_hatch(color=BLACK, dxfattribs={"layer": "WALL-FILL"})
    h.paths.add_polyline_path(pts + [pts[0]], is_closed=True)
    msp.add_lwpolyline(pts + [pts[0]], close=True, dxfattribs={"layer": "WALL", "lineweight": 50, "color": BLACK})


def outer_walls(msp, w, h, t=240):
    wall_filled_h(msp, 0, 0, w, t)
    wall_filled_h(msp, 0, h-t, w, t)
    wall_filled_v(msp, 0, 0, h, t)
    wall_filled_v(msp, w-t, 0, h, t)


def iwall_h(msp, x, y, length, t=120):
    wall_filled_h(msp, x, y, length, t)


def iwall_v(msp, x, y, length, t=120):
    wall_filled_v(msp, x, y, length, t)


def room_fill(msp, x, y, w, h):
    pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
    hatch = msp.add_hatch(color=LIGHT_FILL, dxfattribs={"layer": "ROOM-FILL"})
    hatch.paths.add_polyline_path(pts + [pts[0]], is_closed=True)


def build_dxf_floor(floor_data, filename):
    doc = ezdxf.new("R2010")
    doc.units = units.MM
    setup_layers(doc)
    msp = doc.modelspace()
    W = 14000; H = 11000; OW = 240; IW = 120

    for rf in floor_data.get("room_fills", []):
        room_fill(msp, *rf)
    outer_walls(msp, W, H, OW)
    for wall in floor_data.get("hwalls", []):
        iwall_h(msp, *wall)
    for wall in floor_data.get("vwalls", []):
        iwall_v(msp, *wall)

    doc.saveas(f"{OUT}/{filename}")
    print(f"✓ DXF: {filename}")


# ══════════════════════════════════════════════
#  Matplotlib 高质量预览图
# ══════════════════════════════════════════════

# 参考图配色
C_BG = "#FFFFFF"
C_ROOM = "#D6E8F0"       # 淡蓝灰（参考图的房间填充色）
C_WALL = "#1A1A1A"       # 黑色墙体
C_LINE = "#333333"       # 深灰家具线
C_TEXT = "#1A1A1A"        # 黑色文字
C_TEXT2 = "#666666"       # 灰色副文字
C_DIM = "#CC0000"         # 红色标注
C_DOOR = "#333333"        # 门
C_WIN = "#4A90D9"         # 窗户蓝色
C_STAIR = "#888888"       # 楼梯灰色


class FloorPlan:
    def __init__(self, title, subtitle, w=14000, h=11000, ow=240, iw=120):
        self.title = title
        self.subtitle = subtitle
        self.W = w; self.H = h; self.OW = ow; self.IW = iw
        self.fig, self.ax = plt.subplots(1, 1, figsize=(16, 13), dpi=150, facecolor=C_BG)
        self.ax.set_facecolor(C_BG)
        self.ax.set_aspect("equal")
        self.ax.axis("off")

    def _s(self, v):
        return v / 1000.0

    def fill_room(self, x, y, w, h):
        self.ax.add_patch(patches.Rectangle(
            (self._s(x), self._s(y)), self._s(w), self._s(h),
            facecolor=C_ROOM, edgecolor="none", zorder=1))

    def draw_outer_walls(self):
        s = self._s
        t = self.OW
        for (x, y, w, h) in [
            (0, 0, self.W, t), (0, self.H-t, self.W, t),
            (0, 0, t, self.H), (self.W-t, 0, t, self.H)
        ]:
            self.ax.add_patch(patches.Rectangle(
                (s(x), s(y)), s(w), s(h), facecolor=C_WALL, edgecolor=C_WALL, linewidth=0.5, zorder=5))

    def draw_iwall_h(self, x, y, length, t=None):
        t = t or self.IW
        self.ax.add_patch(patches.Rectangle(
            (self._s(x), self._s(y)), self._s(length), self._s(t),
            facecolor=C_WALL, edgecolor=C_WALL, linewidth=0.3, zorder=5))

    def draw_iwall_v(self, x, y, length, t=None):
        t = t or self.IW
        self.ax.add_patch(patches.Rectangle(
            (self._s(x), self._s(y)), self._s(t), self._s(length),
            facecolor=C_WALL, edgecolor=C_WALL, linewidth=0.3, zorder=5))

    def room_label(self, cx, cy, cn, en="", size_text=""):
        s = self._s
        self.ax.text(s(cx), s(cy)+0.25, cn, ha="center", va="center",
                     fontsize=11, fontweight="bold", color=C_TEXT, zorder=10,
                     fontfamily="sans-serif")
        if en:
            self.ax.text(s(cx), s(cy)-0.1, en, ha="center", va="center",
                         fontsize=7, color=C_TEXT2, zorder=10)
        if size_text:
            self.ax.text(s(cx), s(cy)-0.42, size_text, ha="center", va="center",
                         fontsize=6.5, color=C_TEXT2, zorder=10)

    def door_h(self, x, y, w=900, up=True):
        s = self._s
        sa, ea = (0, 90) if up else (270, 360)
        arc = Arc((s(x), s(y)), s(w)*2, s(w)*2, angle=0, theta1=sa, theta2=ea,
                  color=C_DOOR, linewidth=0.8, zorder=6)
        self.ax.add_patch(arc)

    def door_v(self, x, y, w=900, right=True):
        s = self._s
        sa, ea = (0, 90) if right else (90, 180)
        arc = Arc((s(x), s(y)), s(w)*2, s(w)*2, angle=0, theta1=sa, theta2=ea,
                  color=C_DOOR, linewidth=0.8, zorder=6)
        self.ax.add_patch(arc)

    def window_h(self, x, y, length):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)-0.06), s(length), 0.12,
            facecolor=C_BG, edgecolor=C_WIN, linewidth=1.5, zorder=6))
        self.ax.plot([s(x), s(x+length)], [s(y), s(y)], color=C_WIN, linewidth=0.5, zorder=7)

    def window_v(self, x, y, length):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x)-0.06, s(y)), 0.12, s(length),
            facecolor=C_BG, edgecolor=C_WIN, linewidth=1.5, zorder=6))
        self.ax.plot([s(x), s(x)], [s(y), s(y+length)], color=C_WIN, linewidth=0.5, zorder=7)

    def stairs(self, x, y, w, h, n=13, direction="up"):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_STAIR, linewidth=0.6, zorder=4))
        step = h / n
        for i in range(1, n):
            sy = y + i * step
            self.ax.plot([s(x), s(x+w)], [s(sy), s(sy)], color=C_STAIR, linewidth=0.4, zorder=4)
        mx = s(x + w/2)
        if direction == "up":
            self.ax.annotate("", xy=(mx, s(y+h)-0.1), xytext=(mx, s(y)+0.1),
                             arrowprops=dict(arrowstyle="->", color=C_DIM, lw=1.2), zorder=8)
        else:
            self.ax.annotate("", xy=(mx, s(y)+0.1), xytext=(mx, s(y+h)-0.1),
                             arrowprops=dict(arrowstyle="->", color=C_DIM, lw=1.2), zorder=8)

    def bed_double(self, x, y, w=1800, h=2000):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_LINE, linewidth=0.6, zorder=4))
        self.ax.add_patch(patches.Rectangle(
            (s(x+60), s(y+h-350)), s(w/2-90), s(280), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))
        self.ax.add_patch(patches.Rectangle(
            (s(x+w/2+30), s(y+h-350)), s(w/2-90), s(280), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def bed_single(self, x, y, w=1200, h=2000):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_LINE, linewidth=0.6, zorder=4))
        self.ax.add_patch(patches.Rectangle(
            (s(x+60), s(y+h-350)), s(w-120), s(280), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def sofa_L(self, x, y):
        s = self._s
        for (rx, ry, rw, rh) in [
            (x, y, 2800, 700), (x+50, y+50, 850, 580), (x+950, y+50, 850, 580),
            (x+2800, y-100, 700, 800), (x+2850, y-50, 580, 680)
        ]:
            self.ax.add_patch(patches.Rectangle(
                (s(rx), s(ry)), s(rw), s(rh), facecolor="none", edgecolor=C_LINE, linewidth=0.5, zorder=4))

    def dining_round(self, cx, cy, r=550):
        s = self._s
        self.ax.add_patch(patches.Circle(
            (s(cx), s(cy)), s(r), facecolor="none", edgecolor=C_LINE, linewidth=0.6, zorder=4))
        for a in range(0, 360, 45):
            px = cx + (r+200) * math.cos(math.radians(a))
            py = cy + (r+200) * math.sin(math.radians(a))
            self.ax.add_patch(patches.Circle(
                (s(px), s(py)), s(120), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def kitchen_L(self, x, y, w, h, d=550):
        s = self._s
        pts = [(s(x), s(y)), (s(x+w), s(y)), (s(x+w), s(y+d)), (s(x+d), s(y+d)),
               (s(x+d), s(y+h)), (s(x), s(y+h)), (s(x), s(y))]
        poly = plt.Polygon(pts, facecolor="none", edgecolor=C_LINE, linewidth=0.6, zorder=4)
        self.ax.add_patch(poly)
        self.ax.add_patch(patches.Circle((s(x+w*0.4), s(y+d/2)), s(80), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))
        self.ax.add_patch(patches.Circle((s(x+w*0.6), s(y+d/2)), s(80), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def toilet(self, x, y):
        s = self._s
        self.ax.add_patch(patches.Ellipse(
            (s(x), s(y)), s(300), s(240), facecolor="none", edgecolor=C_LINE, linewidth=0.5, zorder=4))
        self.ax.add_patch(patches.Rectangle(
            (s(x-170), s(y-200)), s(340), s(140), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def sink(self, x, y, w=450, h=350):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))
        self.ax.add_patch(patches.Circle((s(x+w/2), s(y+h/2)), s(70), facecolor="none", edgecolor=C_LINE, linewidth=0.3, zorder=4))

    def shower_room(self, x, y, sz=900):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(sz), s(sz), facecolor="none", edgecolor=C_LINE, linewidth=0.5, zorder=4))
        self.ax.add_patch(patches.Circle((s(x+sz/2), s(y+sz/2)), s(160), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def bathtub(self, x, y, w=750, h=1600):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_LINE, linewidth=0.5, zorder=4))
        self.ax.add_patch(patches.Ellipse(
            (s(x+w/2), s(y+h/2)), s(w-100), s(h-100), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def wardrobe(self, x, y, w, h=550):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_LINE, linewidth=0.5, zorder=4))
        self.ax.plot([s(x+w/2), s(x+w/2)], [s(y), s(y+h)], color=C_LINE, linewidth=0.3, zorder=4)

    def desk_chair(self, x, y, w=1400, h=600):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(h), facecolor="none", edgecolor=C_LINE, linewidth=0.5, zorder=4))
        self.ax.add_patch(patches.Circle((s(x+w/2), s(y-300)), s(180), facecolor="none", edgecolor=C_LINE, linewidth=0.4, zorder=4))

    def tv_wall(self, x, y, w=2200):
        s = self._s
        self.ax.add_patch(patches.Rectangle(
            (s(x), s(y)), s(w), s(120), facecolor=C_LINE, edgecolor=C_LINE, linewidth=0.3, zorder=4))

    def car_symbol(self, x, y):
        s = self._s
        pts = [(s(x+150), s(y)), (s(x+1650), s(y)), (s(x+1800), s(y+350)), (s(x+1800), s(y+3800)),
               (s(x+1650), s(y+4200)), (s(x+150), s(y+4200)), (s(x), s(y+3800)), (s(x), s(y+350))]
        poly = plt.Polygon(pts, facecolor="none", edgecolor=C_LINE, linewidth=0.6, zorder=4, closed=True)
        self.ax.add_patch(poly)

    def dim_h(self, x1, x2, y, offset=-700):
        s = self._s
        yo = s(y + offset)
        self.ax.plot([s(x1), s(x2)], [yo, yo], color=C_DIM, linewidth=0.6, zorder=8)
        self.ax.plot([s(x1), s(x1)], [s(y), yo-0.08], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.plot([s(x2), s(x2)], [s(y), yo-0.08], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.text((s(x1)+s(x2))/2, yo+0.06, f"{abs(x2-x1)}", ha="center", va="bottom",
                     fontsize=6.5, color=C_DIM, zorder=8)

    def dim_v(self, y1, y2, x, offset=700):
        s = self._s
        xo = s(x + offset)
        self.ax.plot([xo, xo], [s(y1), s(y2)], color=C_DIM, linewidth=0.6, zorder=8)
        self.ax.plot([s(x), xo+0.08], [s(y1), s(y1)], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.plot([s(x), xo+0.08], [s(y2), s(y2)], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.text(xo+0.06, (s(y1)+s(y2))/2, f"{abs(y2-y1)}", ha="left", va="center",
                     fontsize=6.5, color=C_DIM, rotation=90, zorder=8)

    def dim_total_h(self, x1, x2, y, offset=-1400):
        s = self._s
        yo = s(y + offset)
        self.ax.plot([s(x1), s(x2)], [yo, yo], color=C_DIM, linewidth=0.8, zorder=8)
        self.ax.plot([s(x1), s(x1)], [s(y), yo-0.08], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.plot([s(x2), s(x2)], [s(y), yo-0.08], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.text((s(x1)+s(x2))/2, yo+0.08, f"{abs(x2-x1)}", ha="center", va="bottom",
                     fontsize=7.5, fontweight="bold", color=C_DIM, zorder=8)

    def dim_total_v(self, y1, y2, x, offset=1400):
        s = self._s
        xo = s(x + offset)
        self.ax.plot([xo, xo], [s(y1), s(y2)], color=C_DIM, linewidth=0.8, zorder=8)
        self.ax.plot([s(x), xo+0.08], [s(y1), s(y1)], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.plot([s(x), xo+0.08], [s(y2), s(y2)], color=C_DIM, linewidth=0.4, zorder=8)
        self.ax.text(xo+0.08, (s(y1)+s(y2))/2, f"{abs(y2-y1)}", ha="left", va="center",
                     fontsize=7.5, fontweight="bold", color=C_DIM, rotation=90, zorder=8)

    def info_block(self, floor_name):
        s = self._s
        x = s(self.W) + 2.0
        y = s(self.H) - 0.5
        items = [
            "项目简介：",
            f"楼层：{floor_name}",
            "基地尺寸：14m × 11m",
            "建筑面积：308 平米",
            "建筑层数：二层",
            "建筑风格：现代轻奢",
            "卧室配置：3主卧+2次卧",
        ]
        for i, item in enumerate(items):
            fw = "bold" if i == 0 else "normal"
            self.ax.text(x, y - i*0.5, item, fontsize=8, color=C_TEXT, fontweight=fw, zorder=10)

    def north_arrow(self):
        s = self._s
        x, y = -1.2, s(self.H) - 1.5
        self.ax.annotate("", xy=(x, y+0.7), xytext=(x, y),
                         arrowprops=dict(arrowstyle="-|>", color=C_TEXT, lw=1.5), zorder=10)
        self.ax.text(x, y+0.85, "N", ha="center", va="bottom", fontsize=10, fontweight="bold", color=C_TEXT, zorder=10)

    def save(self, filename):
        margin = 2.5
        s = self._s
        self.ax.set_xlim(-margin, s(self.W) + margin + 5)
        self.ax.set_ylim(-margin, s(self.H) + margin * 0.6)
        self.ax.set_title(self.title, fontsize=16, fontweight="bold", color=C_TEXT, pad=10)
        self.fig.savefig(f"{OUT}/{filename}", bbox_inches="tight", pad_inches=0.3, dpi=150, facecolor=C_BG)
        plt.close(self.fig)
        print(f"✓ 预览: {filename}")


# ══════════════════════════════════════════════
#  一层平面图
# ══════════════════════════════════════════════

def generate_floor1():
    W = 14000; H = 11000; OW = 240; IW = 120
    X1 = 4800; X2 = 7000; X3 = 8600
    Y0 = 1500; Y1 = 4500; Y2 = 7000

    # --- DXF ---
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    fills = [
        (OW, OW, W-2*OW, Y0-OW), (OW, Y0+IW, X1-OW, Y1-Y0-IW),
        (X1+IW, Y0+IW, X2-X1-IW, Y1-Y0-IW), (X2+IW, Y0+IW, X3-X2-IW, Y1-Y0-IW),
        (OW, Y1+IW, X3-OW, Y2-Y1-IW), (OW, Y2+IW, X1-OW, H-OW-Y2-IW),
        (X1+IW, Y2+IW, X2-X1-IW, H-OW-Y2-IW), (X3+IW, Y2+IW, W-OW-X3-IW, H-OW-Y2-IW),
        (X3+IW, OW, W-OW-X3-IW, Y2-OW),
    ]
    for rf in fills:
        room_fill(msp, *rf)
    outer_walls(msp, W, H, OW)
    for w in [(OW, Y0, W-2*OW), (OW, Y1, X3-OW), (OW, Y2, X3-OW), (X3+IW, Y2, W-OW-X3-IW)]:
        iwall_h(msp, *w)
    for w in [(X1, Y0+IW, Y1-Y0-IW), (X2, Y0+IW, Y1-Y0-IW), (X1, Y2+IW, H-OW-Y2-IW), (X3, OW, H-2*OW)]:
        iwall_v(msp, *w)
    doc.saveas(f"{OUT}/house_floor1.dxf")
    print("✓ DXF: house_floor1.dxf")

    # --- Preview ---
    fp = FloorPlan("一层平面图  Ground Floor Plan", "3主卧+2次卧 现代轻奢别墅")
    for rf in fills:
        fp.fill_room(*rf)
    fp.draw_outer_walls()
    for w in [(OW, Y0, W-2*OW), (OW, Y1, X3-OW), (OW, Y2, X3-OW), (X3+IW, Y2, W-OW-X3-IW)]:
        fp.draw_iwall_h(*w)
    for w in [(X1, Y0+IW, Y1-Y0-IW), (X2, Y0+IW, Y1-Y0-IW), (X1, Y2+IW, H-OW-Y2-IW), (X3, OW, H-2*OW)]:
        fp.draw_iwall_v(*w)

    fp.room_label((OW+W-OW)/2, Y0/2, "玄关", "Entrance")
    fp.room_label((OW+X1)/2, (Y0+Y1)/2, "餐厅", "Dining", "3.5m×3.0m")
    fp.room_label((X1+X2)/2, (Y0+Y1)/2, "厨房", "Kitchen", "2.2m×3.0m")
    fp.room_label((X2+X3)/2, (Y0+Y1)/2, "客卫", "WC")
    fp.room_label((OW+X3)/2, (Y1+Y2)/2, "客厅", "Living Room", "8.4m×2.5m")
    fp.room_label((OW+X1)/2, (Y2+H)/2, "主卧室1（老人房）", "Master BR.1", "4.6m×4.0m")
    fp.room_label((X1+X2)/2, (Y2+H)/2, "主卫1", "En-suite")
    fp.room_label((X3+W)/2, (Y2+H)/2, "休闲区", "Lounge", "5.2m×4.0m")
    fp.room_label((X3+W)/2, (OW+Y2)/2, "车库", "Garage", "5.2m×5.5m")
    fp.room_label((X2+X3)/2+200, Y2+2000, "楼梯间", "Stairs")

    fp.bed_double(1200, 7800, 1800, 2000)
    fp.wardrobe(400, 10100, 4000, 500)
    fp.sofa_L(800, 5200)
    fp.tv_wall(1200, Y2-300, 2200)
    fp.dining_round(2400, 2800)
    fp.kitchen_L(X1+IW+80, Y0+IW+80, X2-X1-IW-160, Y1-Y0-IW-160, 500)
    fp.toilet(X2+800, 3000)
    fp.sink(X2+500, 3800)
    fp.toilet(X1+800, 8200)
    fp.sink(X1+500, 9800)
    fp.shower_room(X2-1100, 7500, 900)
    fp.car_symbol(X3+1500, 1800)
    fp.stairs(X3+IW+80, Y2+IW+200, 1350, 3200, 13, "up")

    fp.door_h(2500, Y2+IW, 900, True)
    fp.door_v(X1+IW, 8200, 800, True)
    fp.door_h(2000, Y1+IW, 900, True)
    fp.door_h(X1+500, Y1, 800, False)
    fp.door_h(X2+300, Y1, 700, False)
    fp.door_h(6000, OW+IW, 1000, True)

    fp.window_h(1200, H, 2200)
    fp.window_h(10000, H, 2500)
    fp.window_v(0, 5000, 1800)
    fp.window_v(0, 8200, 2000)
    fp.window_h(1200, 0, 2000)
    fp.window_h(5000, 0, 1500)
    fp.window_v(W, 8500, 2000)
    fp.window_v(W, 2000, 2500)
    fp.window_h(10500, 0, 2000)

    fp.dim_h(0, X1, 0)
    fp.dim_h(X1, X2, 0)
    fp.dim_h(X2, X3, 0)
    fp.dim_h(X3, W, 0)
    fp.dim_total_h(0, W, 0)
    fp.dim_v(0, Y0, W)
    fp.dim_v(Y0, Y1, W)
    fp.dim_v(Y1, Y2, W)
    fp.dim_v(Y2, H, W)
    fp.dim_total_v(0, H, W)

    fp.info_block("一层")
    fp.north_arrow()
    fp.save("house_floor1_preview.png")


# ══════════════════════════════════════════════
#  二层平面图
# ══════════════════════════════════════════════

def generate_floor2():
    W = 14000; H = 11000; OW = 240; IW = 120
    X1 = 4800; X2 = 7000; X3 = 8600; X4 = 11000
    Y0 = 1500; Y1 = 4500; Y2 = 7000

    # --- DXF ---
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    fills = [
        (OW, OW, W-2*OW, Y0-OW),
        (OW, Y0+IW, X1-OW, Y1-Y0-IW), (X1+IW, Y0+IW, X2-X1-IW, Y1-Y0-IW),
        (X2+IW, Y0+IW, X4-X2-IW, Y1-Y0-IW), (X4+IW, Y0+IW, W-OW-X4-IW, H-OW-Y0-IW),
        (OW, Y1+IW, X3-OW, Y2-Y1-IW), (X3+IW, Y1+IW, X4-X3-IW, Y2-Y1-IW),
        (OW, Y2+IW, X1-OW, H-OW-Y2-IW), (X1+IW, Y2+IW, X3-X1-IW, H-OW-Y2-IW),
        (X3+IW, Y2+IW, W-OW-X3-IW, H-OW-Y2-IW),
    ]
    for rf in fills:
        room_fill(msp, *rf)
    outer_walls(msp, W, H, OW)
    hwalls = [(OW, Y0, W-2*OW), (OW, Y1, X3-OW), (X2+IW, Y1, X4-X2-IW), (OW, Y2, W-2*OW)]
    vwalls = [(X1, Y0+IW, Y1-Y0-IW), (X2, Y0+IW, Y1-Y0-IW), (X4, Y0+IW, Y2-Y0-IW),
              (X3, Y1+IW, H-OW-Y1-IW), (X1, Y2+IW, H-OW-Y2-IW)]
    for w in hwalls:
        iwall_h(msp, *w)
    for w in vwalls:
        iwall_v(msp, *w)
    doc.saveas(f"{OUT}/house_floor2.dxf")
    print("✓ DXF: house_floor2.dxf")

    # --- Preview ---
    fp = FloorPlan("二层平面图  Second Floor Plan", "3主卧+2次卧 现代轻奢别墅")
    for rf in fills:
        fp.fill_room(*rf)
    fp.draw_outer_walls()
    for w in hwalls:
        fp.draw_iwall_h(*w)
    for w in vwalls:
        fp.draw_iwall_v(*w)

    fp.room_label(W/2, Y0/2, "南向大阳台", "Balcony", "14.0m×1.5m")
    fp.room_label((OW+X1)/2, (Y0+Y1)/2, "次卧室1", "Bedroom 4", "4.6m×3.0m")
    fp.room_label((X1+X2)/2, (Y0+Y1)/2, "次卧室2", "Bedroom 5", "2.1m×3.0m")
    fp.room_label((X2+X4)/2, (Y0+Y1)/2, "公共卫生间", "Bathroom", "4.0m×3.0m")
    fp.room_label((X4+W)/2, (Y0+H)/2, "书房", "Study", "3.0m×9.5m")
    fp.room_label((OW+X3)/2, (Y1+Y2)/2, "走廊/起居厅", "Hallway", "8.4m×2.5m")
    fp.room_label((X3+X4)/2, (Y1+Y2)/2, "主卫3", "En-suite 3")
    fp.room_label((OW+X1)/2, (Y2+H)/2, "主卧室2", "Master BR.2", "4.6m×4.0m")
    fp.room_label((X1+X3)/2, (Y2+H)/2, "主卫2", "En-suite 2", "3.8m×4.0m")
    fp.room_label((X3+W)/2, (Y2+H)/2, "主卧室3", "Master BR.3", "5.2m×4.0m")
    fp.room_label((X2+X3)/2+200, Y2+2000, "楼梯间", "Stairs")

    fp.bed_double(1200, 7800, 1800, 2000)
    fp.wardrobe(400, 10100, 4000, 500)
    fp.bed_double(X3+IW+800, 7800, 1800, 2000)
    fp.wardrobe(X3+IW+300, 10100, W-OW-X3-IW-600, 500)
    fp.bed_single(1500, Y0+IW+300, 1200, 2000)
    fp.bed_single(X1+IW+300, Y0+IW+300, 1200, 2000)
    fp.desk_chair(X4+IW+400, 5500, 1400, 600)
    fp.desk_chair(X4+IW+400, 2500, 1400, 600)

    fp.toilet(X1+800, 8500)
    fp.sink(X1+500, 9800)
    fp.bathtub(X2-1200, 7500, 750, 1600)
    fp.toilet(X3+500, 5500)
    fp.sink(X3+500, 6200)
    fp.toilet(X2+800, 2500)
    fp.sink(X2+500, 3500)
    fp.shower_room(X4-1200, Y0+IW+200, 900)

    fp.stairs(X3+IW+80, Y2+IW+200, 1350, 3200, 13, "down")

    fp.door_h(2500, Y2+IW, 900, True)
    fp.door_v(X1+IW, 8500, 800, True)
    fp.door_h(X3+IW+500, Y2+IW, 900, True)
    fp.door_v(X4, 5500, 700, False)
    fp.door_h(2000, Y1, 800, False)
    fp.door_h(X1+IW+300, Y1, 800, False)
    fp.door_h(X2+IW+300, Y1, 700, False)
    fp.door_v(X4+IW, 4000, 800, True)

    fp.window_h(1200, H, 2200)
    fp.window_h(10000, H, 2500)
    fp.window_v(0, 8200, 2000)
    fp.window_v(0, Y0+500, 2000)
    fp.window_h(1200, Y0, 2000)
    fp.window_h(X1+300, Y0, 1500)
    fp.window_v(W, 8500, 2000)
    fp.window_v(W, 2500, 2000)
    fp.window_h(X4+300, Y0, 2000)

    fp.dim_h(0, X1, 0)
    fp.dim_h(X1, X2, 0)
    fp.dim_h(X2, X3, 0)
    fp.dim_h(X3, X4, 0)
    fp.dim_h(X4, W, 0)
    fp.dim_total_h(0, W, 0)
    fp.dim_v(0, Y0, W)
    fp.dim_v(Y0, Y1, W)
    fp.dim_v(Y1, Y2, W)
    fp.dim_v(Y2, H, W)
    fp.dim_total_v(0, H, W)

    fp.info_block("二层")
    fp.north_arrow()
    fp.save("house_floor2_preview.png")


# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  两层轻奢别墅 — 参考效果图配色风格")
    print("  白底 + 淡蓝灰填充 + 黑色实心墙体")
    print("=" * 55)
    generate_floor1()
    generate_floor2()
    print("=" * 55)
    print("  完成！")
    print("=" * 55)
