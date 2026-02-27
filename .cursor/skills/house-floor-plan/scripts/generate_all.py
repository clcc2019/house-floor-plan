"""
两层轻奢别墅 — 全套图纸生成（中文命名 + 分类目录）
输出到 图纸/ 目录，按类别分文件夹
每张图纸同时生成 DXF 源文件 + PNG 预览图

所有建筑参数从 building_config.py 导入（唯一数据源），
确保平面图↔立面图↔剖面图↔效果图的结构、尺寸、窗户位置严格一致。
"""

import os
import sys
import math
import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from building_config import (
    BW, BH, OW, IW, BW_M, BD_M,
    GROUND, F1H, F2H, SLAB, PARAPET, WALL_T,
    GL, F1_FL, F1_CL, F2_FL, F2_CL, ROOF, TOP,
    F1_X1, F1_Y0, F1_Y1, F1_NX1, F1_NX2, F1_MX1, F1_MY1,
    F2_X1, F2_Y0, F2_Y1, F2_Y2, F2_NX1, F2_NX2, F2_NX3,
    SOUTH_WIN, SOUTH_DOOR, NORTH_WIN, EAST_WIN, WEST_WIN,
    SILL_STD, DARK_STONE_X,
)

W_m = BW_M; D_m = BD_M

import matplotlib.font_manager as fm
_CJK_FONTS_ADDED = False
for _p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"]:
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
        _CJK_FONTS_ADDED = True
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK JP",        # TTC default index (covers CJK SC glyphs too)
    "Noto Sans CJK SC",        # Linux
    "WenQuanYi Micro Hei",     # Linux fallback
    "PingFang SC",              # macOS
    "Microsoft YaHei",          # Windows
    "SimHei",                   # Windows fallback
    "Arial Unicode MS",         # Cross-platform
]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.join(os.getcwd(), "图纸")
IMG_DIR = os.path.join(os.getcwd(), "docs", "images")
DIRS = {
    "平面图": f"{BASE}/01-建筑设计/平面图",
    "立面图": f"{BASE}/01-建筑设计/立面图",
    "剖面图": f"{BASE}/01-建筑设计/剖面图",
    "屋顶":   f"{BASE}/01-建筑设计/屋顶平面图",
    "给排水": f"{BASE}/02-给排水设计",
    "电气":   f"{BASE}/03-电气设计",
    "效果图": f"{BASE}/04-效果图",
}
for d in list(DIRS.values()) + [IMG_DIR]:
    os.makedirs(d, exist_ok=True)

# ── 颜色 ──
BLACK = 250; WHITE = 7; LIGHT_FILL = 150; RED = 1; GRAY = 8; BLUE = 4
C_BG = "#FFFFFF"; C_ROOM = "#D6E8F0"; C_WALL = "#1A1A1A"; C_LINE = "#333333"
C_TEXT = "#1A1A1A"; C_TEXT2 = "#666666"; C_DIM = "#CC0000"; C_WIN = "#4A90D9"
C_DOOR = "#333333"; C_STAIR = "#888888"
C_GROUND = "#D2B48C"; C_GLASS = "#B8D4E8"
C_WATER_SUPPLY = "#2196F3"; C_WATER_DRAIN = "#795548"; C_HOTWATER = "#FF5722"
C_ELEC_LIGHT = "#FFC107"; C_ELEC_DOWNLIGHT = "#FFD54F"
C_ELEC_SOCKET = "#4CAF50"; C_ELEC_SWITCH = "#FF9800"; C_ELEC_SPECIAL = "#E91E63"


def _s(v):
    return v / 1000.0


# ══════════════════════════════════════════════
#  DXF 工具
# ══════════════════════════════════════════════

def setup_layers(doc):
    layers = [
        ("WALL", BLACK), ("WALL-FILL", BLACK), ("ROOM-FILL", LIGHT_FILL),
        ("DOOR", BLACK), ("WINDOW", BLUE), ("STAIRS", GRAY), ("TEXT", BLACK),
        ("DIM", RED), ("FIXTURE", GRAY), ("FURNITURE", GRAY),
        ("TITLE", BLACK), ("INFO", BLACK),
        ("PIPE-SUPPLY", 5), ("PIPE-DRAIN", 42), ("PIPE-HOT", 1),
        ("ELEC-LIGHT", 2), ("ELEC-SOCKET", 3), ("ELEC-SWITCH", 30),
        ("ELEC-WIRE", 8), ("GROUND", 42), ("GLASS", 4),
        ("HATCH", GRAY), ("SECTION", BLACK),
    ]
    for name, color in layers:
        if name not in doc.layers:
            doc.layers.add(name, color=color)


def wall_h(msp, x, y, length, t=240):
    pts = [(x, y), (x+length, y), (x+length, y+t), (x, y+t)]
    h = msp.add_hatch(color=BLACK, dxfattribs={"layer": "WALL-FILL"})
    h.paths.add_polyline_path(pts + [pts[0]], is_closed=True)
    msp.add_lwpolyline(pts + [pts[0]], close=True, dxfattribs={"layer": "WALL", "lineweight": 50, "color": BLACK})


def wall_v(msp, x, y, length, t=240):
    pts = [(x, y), (x+t, y), (x+t, y+length), (x, y+length)]
    h = msp.add_hatch(color=BLACK, dxfattribs={"layer": "WALL-FILL"})
    h.paths.add_polyline_path(pts + [pts[0]], is_closed=True)
    msp.add_lwpolyline(pts + [pts[0]], close=True, dxfattribs={"layer": "WALL", "lineweight": 50, "color": BLACK})


def outer_walls(msp, w, h, t=240):
    wall_h(msp, 0, 0, w, t); wall_h(msp, 0, h-t, w, t)
    wall_v(msp, 0, 0, h, t); wall_v(msp, w-t, 0, h, t)


def room_fill(msp, x, y, w, h):
    pts = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
    hatch = msp.add_hatch(color=LIGHT_FILL, dxfattribs={"layer": "ROOM-FILL"})
    hatch.paths.add_polyline_path(pts + [pts[0]], is_closed=True)


def dxf_text(msp, x, y, text, height=200, layer="TEXT"):
    msp.add_text(text, height=height, dxfattribs={"layer": layer, "color": BLACK}).set_placement(
        (x, y), align=TextEntityAlignment.MIDDLE_CENTER)


def dxf_dim_h(msp, x1, x2, y, offset=-800):
    yo = y + offset
    msp.add_line((x1, yo), (x2, yo), dxfattribs={"layer": "DIM", "color": RED})
    msp.add_line((x1, y), (x1, yo), dxfattribs={"layer": "DIM", "color": RED})
    msp.add_line((x2, y), (x2, yo), dxfattribs={"layer": "DIM", "color": RED})
    msp.add_text(str(abs(x2-x1)), height=150, dxfattribs={"layer": "DIM", "color": RED}).set_placement(
        ((x1+x2)/2, yo+100), align=TextEntityAlignment.MIDDLE_CENTER)


def dxf_dim_v(msp, y1, y2, x, offset=800):
    xo = x + offset
    msp.add_line((xo, y1), (xo, y2), dxfattribs={"layer": "DIM", "color": RED})
    msp.add_line((x, y1), (xo, y1), dxfattribs={"layer": "DIM", "color": RED})
    msp.add_line((x, y2), (xo, y2), dxfattribs={"layer": "DIM", "color": RED})
    msp.add_text(str(abs(y2-y1)), height=150, dxfattribs={"layer": "DIM", "color": RED}).set_placement(
        (xo+100, (y1+y2)/2), align=TextEntityAlignment.MIDDLE_CENTER)


def dxf_window_h(msp, x, y, length, t=240):
    msp.add_lwpolyline([(x, y), (x+length, y), (x+length, y+t), (x, y+t), (x, y)],
                        close=True, dxfattribs={"layer": "WINDOW", "color": BLUE})
    msp.add_line((x, y+t/2), (x+length, y+t/2), dxfattribs={"layer": "WINDOW", "color": BLUE})


def dxf_window_v(msp, x, y, length, t=240):
    msp.add_lwpolyline([(x, y), (x+t, y), (x+t, y+length), (x, y+length), (x, y)],
                        close=True, dxfattribs={"layer": "WINDOW", "color": BLUE})
    msp.add_line((x+t/2, y), (x+t/2, y+length), dxfattribs={"layer": "WINDOW", "color": BLUE})


def dxf_door_arc(msp, x, y, r=900, start=0, end=90):
    msp.add_arc(center=(x, y), radius=r, start_angle=start, end_angle=end,
                dxfattribs={"layer": "DOOR", "color": BLACK})


# ══════════════════════════════════════════════
#  Matplotlib 预览工具（复用之前的 FloorPlan 类）
# ══════════════════════════════════════════════

class FloorPlan:
    def __init__(self, title, subtitle, w=14000, h=11000, ow=240, iw=120):
        self.title = title; self.subtitle = subtitle
        self.W = w; self.H = h; self.OW = ow; self.IW = iw
        self.fig, self.ax = plt.subplots(1, 1, figsize=(16, 13), dpi=150, facecolor=C_BG)
        self.ax.set_facecolor(C_BG); self.ax.set_aspect("equal"); self.ax.axis("off")

    def _s(self, v): return v / 1000.0
    def fill_room(self, x, y, w, h):
        self.ax.add_patch(patches.Rectangle((self._s(x), self._s(y)), self._s(w), self._s(h), facecolor=C_ROOM, edgecolor="none", zorder=1))
    def draw_outer_walls(self):
        s = self._s; t = self.OW
        for (x, y, w, h) in [(0,0,self.W,t),(0,self.H-t,self.W,t),(0,0,t,self.H),(self.W-t,0,t,self.H)]:
            self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    def draw_iwall_h(self, x, y, length, t=None):
        t = t or self.IW
        self.ax.add_patch(patches.Rectangle((self._s(x),self._s(y)),self._s(length),self._s(t),facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.3,zorder=5))
    def draw_iwall_v(self, x, y, length, t=None):
        t = t or self.IW
        self.ax.add_patch(patches.Rectangle((self._s(x),self._s(y)),self._s(t),self._s(length),facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.3,zorder=5))
    def room_label(self, cx, cy, cn, en="", size_text=""):
        s = self._s
        self.ax.text(s(cx),s(cy)+0.25,cn,ha="center",va="center",fontsize=11,fontweight="bold",color=C_TEXT,zorder=10)
        if en: self.ax.text(s(cx),s(cy)-0.1,en,ha="center",va="center",fontsize=7,color=C_TEXT2,zorder=10)
        if size_text: self.ax.text(s(cx),s(cy)-0.42,size_text,ha="center",va="center",fontsize=6.5,color=C_TEXT2,zorder=10)
    def door_h(self, x, y, w=900, up=True):
        sa, ea = (0,90) if up else (270,360)
        self.ax.add_patch(Arc((self._s(x),self._s(y)),self._s(w)*2,self._s(w)*2,angle=0,theta1=sa,theta2=ea,color=C_DOOR,linewidth=0.8,zorder=6))
    def door_v(self, x, y, w=900, right=True):
        sa, ea = (0,90) if right else (90,180)
        self.ax.add_patch(Arc((self._s(x),self._s(y)),self._s(w)*2,self._s(w)*2,angle=0,theta1=sa,theta2=ea,color=C_DOOR,linewidth=0.8,zorder=6))
    def window_h(self, x, y, length):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)-0.06),s(length),0.12,facecolor=C_BG,edgecolor=C_WIN,linewidth=1.5,zorder=6))
        self.ax.plot([s(x),s(x+length)],[s(y),s(y)],color=C_WIN,linewidth=0.5,zorder=7)
    def window_v(self, x, y, length):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x)-0.06,s(y)),0.12,s(length),facecolor=C_BG,edgecolor=C_WIN,linewidth=1.5,zorder=6))
        self.ax.plot([s(x),s(x)],[s(y),s(y+length)],color=C_WIN,linewidth=0.5,zorder=7)
    def stairs(self, x, y, w, h, n=13, direction="up"):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="none",edgecolor=C_STAIR,linewidth=0.6,zorder=4))
        step = h / n
        for i in range(1, n):
            sy = y + i * step; self.ax.plot([s(x),s(x+w)],[s(sy),s(sy)],color=C_STAIR,linewidth=0.4,zorder=4)
        mx = s(x + w/2)
        if direction == "up":
            self.ax.annotate("",xy=(mx,s(y+h)-0.1),xytext=(mx,s(y)+0.1),arrowprops=dict(arrowstyle="->",color=C_DIM,lw=1.2),zorder=8)
        else:
            self.ax.annotate("",xy=(mx,s(y)+0.1),xytext=(mx,s(y+h)-0.1),arrowprops=dict(arrowstyle="->",color=C_DIM,lw=1.2),zorder=8)
    def bed_double(self, x, y, w=1800, h=2000):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="none",edgecolor=C_LINE,linewidth=0.6,zorder=4))
        self.ax.add_patch(patches.Rectangle((s(x+60),s(y+h-350)),s(w/2-90),s(280),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
        self.ax.add_patch(patches.Rectangle((s(x+w/2+30),s(y+h-350)),s(w/2-90),s(280),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
    def bed_single(self, x, y, w=1200, h=2000):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="none",edgecolor=C_LINE,linewidth=0.6,zorder=4))
        self.ax.add_patch(patches.Rectangle((s(x+60),s(y+h-350)),s(w-120),s(280),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
    def sofa_L(self, x, y):
        s = self._s
        for (rx,ry,rw,rh) in [(x,y,2800,700),(x+50,y+50,850,580),(x+950,y+50,850,580),(x+2800,y-100,700,800),(x+2850,y-50,580,680)]:
            self.ax.add_patch(patches.Rectangle((s(rx),s(ry)),s(rw),s(rh),facecolor="none",edgecolor=C_LINE,linewidth=0.5,zorder=4))
    def dining_round(self, cx, cy, r=550):
        s = self._s
        self.ax.add_patch(patches.Circle((s(cx),s(cy)),s(r),facecolor="none",edgecolor=C_LINE,linewidth=0.6,zorder=4))
        for a in range(0,360,45):
            px = cx + (r+200)*math.cos(math.radians(a)); py = cy + (r+200)*math.sin(math.radians(a))
            self.ax.add_patch(patches.Circle((s(px),s(py)),s(120),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
    def kitchen_L(self, x, y, w, h, d=550):
        s = self._s
        pts = [(s(x),s(y)),(s(x+w),s(y)),(s(x+w),s(y+d)),(s(x+d),s(y+d)),(s(x+d),s(y+h)),(s(x),s(y+h)),(s(x),s(y))]
        self.ax.add_patch(plt.Polygon(pts,facecolor="none",edgecolor=C_LINE,linewidth=0.6,zorder=4))
    def toilet(self, x, y):
        s = self._s
        self.ax.add_patch(patches.Ellipse((s(x),s(y)),s(300),s(240),facecolor="none",edgecolor=C_LINE,linewidth=0.5,zorder=4))
        self.ax.add_patch(patches.Rectangle((s(x-170),s(y-200)),s(340),s(140),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
    def sink(self, x, y, w=450, h=350):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
        self.ax.add_patch(patches.Circle((s(x+w/2),s(y+h/2)),s(70),facecolor="none",edgecolor=C_LINE,linewidth=0.3,zorder=4))
    def shower_room(self, x, y, sz=900):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(sz),s(sz),facecolor="none",edgecolor=C_LINE,linewidth=0.5,zorder=4))
        self.ax.add_patch(patches.Circle((s(x+sz/2),s(y+sz/2)),s(160),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
    def wardrobe(self, x, y, w, h=550):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="none",edgecolor=C_LINE,linewidth=0.5,zorder=4))
        self.ax.plot([s(x+w/2),s(x+w/2)],[s(y),s(y+h)],color=C_LINE,linewidth=0.3,zorder=4)
    def desk_chair(self, x, y, w=1400, h=600):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="none",edgecolor=C_LINE,linewidth=0.5,zorder=4))
        self.ax.add_patch(patches.Circle((s(x+w/2),s(y-300)),s(180),facecolor="none",edgecolor=C_LINE,linewidth=0.4,zorder=4))
    def tv_wall(self, x, y, w=2200):
        s = self._s
        self.ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(120),facecolor=C_LINE,edgecolor=C_LINE,linewidth=0.3,zorder=4))
    def car_symbol(self, x, y):
        s = self._s
        pts = [(s(x+150),s(y)),(s(x+1650),s(y)),(s(x+1800),s(y+350)),(s(x+1800),s(y+3800)),
               (s(x+1650),s(y+4200)),(s(x+150),s(y+4200)),(s(x),s(y+3800)),(s(x),s(y+350))]
        self.ax.add_patch(plt.Polygon(pts,facecolor="none",edgecolor=C_LINE,linewidth=0.6,zorder=4,closed=True))
    def dim_h(self, x1, x2, y, offset=-700):
        s = self._s; yo = s(y+offset)
        self.ax.plot([s(x1),s(x2)],[yo,yo],color=C_DIM,linewidth=0.6,zorder=8)
        self.ax.plot([s(x1),s(x1)],[s(y),yo-0.08],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.plot([s(x2),s(x2)],[s(y),yo-0.08],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.text((s(x1)+s(x2))/2,yo+0.06,f"{abs(x2-x1)}",ha="center",va="bottom",fontsize=6.5,color=C_DIM,zorder=8)
    def dim_v(self, y1, y2, x, offset=700):
        s = self._s; xo = s(x+offset)
        self.ax.plot([xo,xo],[s(y1),s(y2)],color=C_DIM,linewidth=0.6,zorder=8)
        self.ax.plot([s(x),xo+0.08],[s(y1),s(y1)],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.plot([s(x),xo+0.08],[s(y2),s(y2)],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.text(xo+0.06,(s(y1)+s(y2))/2,f"{abs(y2-y1)}",ha="left",va="center",fontsize=6.5,color=C_DIM,rotation=90,zorder=8)
    def dim_total_h(self, x1, x2, y, offset=-1400):
        s = self._s; yo = s(y+offset)
        self.ax.plot([s(x1),s(x2)],[yo,yo],color=C_DIM,linewidth=0.8,zorder=8)
        self.ax.plot([s(x1),s(x1)],[s(y),yo-0.08],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.plot([s(x2),s(x2)],[s(y),yo-0.08],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.text((s(x1)+s(x2))/2,yo+0.08,f"{abs(x2-x1)}",ha="center",va="bottom",fontsize=7.5,fontweight="bold",color=C_DIM,zorder=8)
    def dim_total_v(self, y1, y2, x, offset=1400):
        s = self._s; xo = s(x+offset)
        self.ax.plot([xo,xo],[s(y1),s(y2)],color=C_DIM,linewidth=0.8,zorder=8)
        self.ax.plot([s(x),xo+0.08],[s(y1),s(y1)],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.plot([s(x),xo+0.08],[s(y2),s(y2)],color=C_DIM,linewidth=0.4,zorder=8)
        self.ax.text(xo+0.08,(s(y1)+s(y2))/2,f"{abs(y2-y1)}",ha="left",va="center",fontsize=7.5,fontweight="bold",color=C_DIM,rotation=90,zorder=8)
    def info_block(self, floor_name):
        s = self._s; x = s(self.W)+2.0; y = s(self.H)-0.5
        for i, item in enumerate(["项目简介：",f"楼层：{floor_name}","基地尺寸：14m × 11m","建筑面积：308 平米","建筑层数：二层","建筑风格：现代简约","卧室配置：3主卧+2次卧"]):
            self.ax.text(x,y-i*0.5,item,fontsize=8,color=C_TEXT,fontweight="bold" if i==0 else "normal",zorder=10)
    def north_arrow(self):
        s = self._s; x, y = -1.2, s(self.H)-1.5
        self.ax.annotate("",xy=(x,y+0.7),xytext=(x,y),arrowprops=dict(arrowstyle="-|>",color=C_TEXT,lw=1.5),zorder=10)
        self.ax.text(x,y+0.85,"N",ha="center",va="bottom",fontsize=10,fontweight="bold",color=C_TEXT,zorder=10)
    def save(self, filepath):
        s = self._s; margin = 2.5
        self.ax.set_xlim(-margin, s(self.W)+margin+5)
        self.ax.set_ylim(-margin, s(self.H)+margin*0.6)
        self.ax.set_title(self.title, fontsize=16, fontweight="bold", color=C_TEXT, pad=10)
        self.fig.savefig(filepath, bbox_inches="tight", pad_inches=0.3, dpi=150, facecolor=C_BG)
        plt.close(self.fig)


# ══════════════════════════════════════════════
#  一层平面图
# ══════════════════════════════════════════════

def gen_floor1():
    X1 = F1_X1; Y0 = F1_Y0; Y1 = F1_Y1
    NX1 = F1_NX1; NX2 = F1_NX2
    MX1 = F1_MX1; MY1 = F1_MY1

    fills = [
        (OW, OW, X1-OW, Y0-OW),                            # 客厅
        (X1+IW, OW, BW-OW-X1-IW, Y0-OW),                  # 玄关
        (OW, Y0+IW, X1-OW, Y1-Y0-IW),                     # 客餐厅 LDK
        (X1+IW, Y0+IW, MX1-X1-IW, Y1-Y0-IW),              # 主卧1（含衣柜区）
        (MX1+IW, Y0+IW, BW-OW-MX1-IW, MY1-Y0-IW),         # 主卫1（东北角）
        (MX1+IW, MY1+IW, BW-OW-MX1-IW, Y1-MY1-IW),        # 主卧1衣帽间
        (OW, Y1+IW, NX1-OW, BH-OW-Y1-IW),                 # 厨房
        (NX1+IW, Y1+IW, NX2-NX1-IW, BH-OW-Y1-IW),        # 客卫
        (NX2+IW, Y1+IW, BW-OW-NX2-IW, BH-OW-Y1-IW),      # 楼梯间
    ]
    hwalls = [
        (OW, Y0, X1-OW),                                   # 客厅|LDK 顶墙
        (X1+IW, Y0, BW-OW-X1-IW),                          # 玄关|主卧 顶墙
        (OW, Y1, BW-2*OW),                                 # LDK|厨房 北侧带底墙
        (MX1+IW, MY1, BW-OW-MX1-IW),                       # 主卫1|衣帽间
    ]
    vwalls = [
        (X1, OW, Y1-OW),                                   # 公共区 | 私密区
        (MX1, Y0+IW, Y1-Y0-IW),                            # 主卧1 | 主卫1+衣帽间
        (NX1, Y1+IW, BH-OW-Y1-IW),                         # 厨房 | 客卫
        (NX2, Y1+IW, BH-OW-Y1-IW),                         # 客卫 | 楼梯间
    ]

    # DXF
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    for rf in fills: room_fill(msp, *rf)
    outer_walls(msp, BW, BH, OW)
    for w in hwalls: wall_h(msp, *w, t=IW)
    for w in vwalls: wall_v(msp, *w, t=IW)
    dxf_text(msp, (OW+X1)/2, (OW+Y0)/2, "客厅", 300)
    dxf_text(msp, (X1+BW)/2, (OW+Y0)/2, "玄关", 200)
    dxf_text(msp, (OW+X1)/2, (Y0+Y1)/2, "客餐厅 LDK", 300)
    dxf_text(msp, (X1+MX1)/2, (Y0+Y1)/2, "主卧室1", 250)
    dxf_text(msp, (MX1+BW)/2, (Y0+MY1)/2, "主卫1", 200)
    dxf_text(msp, (MX1+BW)/2, (MY1+Y1)/2, "衣帽间", 200)
    dxf_text(msp, (OW+NX1)/2, (Y1+BH)/2, "厨房", 250)
    dxf_text(msp, (NX1+NX2)/2, (Y1+BH)/2, "客卫", 200)
    dxf_text(msp, (NX2+BW)/2, (Y1+BH)/2, "楼梯间", 200)
    dxf_dim_h(msp, 0, X1, 0); dxf_dim_h(msp, X1, BW, 0)
    dxf_dim_v(msp, 0, Y0, BW); dxf_dim_v(msp, Y0, Y1, BW); dxf_dim_v(msp, Y1, BH, BW)
    doc.saveas(f"{DIRS['平面图']}/一层平面图.dxf")

    # PNG
    fp = FloorPlan("一层平面图  Ground Floor Plan", "3主卧+2次卧 现代简约别墅")
    for rf in fills: fp.fill_room(*rf)
    fp.draw_outer_walls()
    for w in hwalls: fp.draw_iwall_h(*w)
    for w in vwalls: fp.draw_iwall_v(*w)

    fp.room_label((OW+X1)/2, (OW+Y0)/2, "客厅", "Living Room", "8.0m×2.0m")
    fp.room_label((X1+BW)/2, (OW+Y0)/2, "玄关", "Entrance", "5.6m×2.0m")
    fp.room_label((OW+X1)/2, (Y0+Y1)/2, "客餐厅 LDK", "Living+Dining", "8.0m×5.0m")
    fp.room_label((X1+MX1)/2, (Y0+Y1)/2, "主卧室1（老人房）", "Master BR.1", "3.8m×5.0m")
    fp.room_label((MX1+BW)/2, (Y0+MY1)/2, "主卫1", "En-suite 1", "1.8m×2.0m")
    fp.room_label((MX1+BW)/2, (MY1+Y1)/2, "衣帽间", "Walk-in Closet", "1.8m×3.0m")
    fp.room_label((OW+NX1)/2, (Y1+BH)/2, "厨房", "Kitchen", "4.6m×3.6m")
    fp.room_label((NX1+NX2)/2, (Y1+BH)/2, "客卫", "Guest WC", "1.8m×3.6m")
    fp.room_label((NX2+BW)/2, (Y1+BH)/2, "楼梯间", "Stairs", "7.2m×3.6m")

    # 家具
    fp.sofa_L(800, 3000)
    fp.tv_wall(1000, Y0+IW+200, 2500)
    fp.dining_round(5500, 4800)
    fp.kitchen_L(OW+100, Y1+IW+100, 4300, BH-OW-Y1-IW-200, 550)
    fp.bed_double(X1+IW+500, Y0+IW+1200, 1800, 2000)       # 主卧1双人床（3.8m宽够放）
    fp.wardrobe(MX1+IW+100, MY1+IW+200, BW-OW-MX1-IW-200, 500)  # 衣帽间衣柜
    fp.toilet(MX1+IW+400, Y0+IW+500)                        # 主卫1马桶
    fp.sink(MX1+IW+300, MY1-500)                             # 主卫1洗手台
    fp.shower_room(MX1+IW+800, Y0+IW+200, 800)              # 主卫1淋浴
    fp.toilet(NX1+IW+400, Y1+IW+500)                        # 客卫马桶
    fp.sink(NX1+IW+300, BH-OW-600)                          # 客卫洗手台
    fp.stairs(NX2+IW+400, Y1+IW+300, 2800, 3000, 14, "up")

    # 门 — 确保每个房间都有合理的进出门
    fp.door_h(X1+IW+1200, OW, 1200, True)                  # 1. 大门（南面玄关石材门）
    fp.door_h(3500, Y0, 900, False)                         # 2. 客厅→LDK（开放连通）
    fp.door_v(X1+IW, Y0+IW+500, 900, True)                 # 3. 玄关→主卧1（从玄关进入主卧）
    fp.door_v(MX1, Y0+IW+800, 800, False)                  # 4. 主卧1→主卫1（主卫从卧室内进入）
    fp.door_v(MX1, MY1+IW+500, 800, True)                  # 5. 主卧1→衣帽间
    fp.door_h(2500, Y1+IW, 900, True)                       # 6. LDK→厨房
    fp.door_h(NX1+IW+200, Y1, 700, False)                   # 7. 客卫→LDK
    fp.door_h(NX2+IW+500, Y1, 900, False)                   # 8. 楼梯间→LDK

    # 窗户
    fp.window_h(1000, 0, 5000)                              # 南面客厅超大落地窗
    fp.window_h(800, BH, 2500)                              # 北面厨房窗
    fp.window_h(NX1+IW+200, BH, 1000)                      # 北面客卫窗（通风）
    fp.window_h(NX2+IW+1500, BH, 3500)                     # 北面楼梯间窗
    fp.window_v(0, 3000, 3500)                              # 西面LDK大窗
    fp.window_v(0, Y1+IW+500, 2500)                         # 西面厨房窗
    fp.window_v(BW, Y0+IW+500, 3500)                        # 东面主卧1窗
    fp.window_v(BW, Y1+IW+500, 2000)                        # 东面楼梯间窗

    # 尺寸标注
    fp.dim_h(0, X1, 0); fp.dim_h(X1, BW, 0)
    fp.dim_h(0, NX1, BH); fp.dim_h(NX1, NX2, BH); fp.dim_h(NX2, BW, BH)
    fp.dim_total_h(0, BW, 0)
    fp.dim_v(0, Y0, BW); fp.dim_v(Y0, Y1, BW); fp.dim_v(Y1, BH, BW)
    fp.dim_total_v(0, BH, BW)
    fp.info_block("一层"); fp.north_arrow()
    fp.save(f"{IMG_DIR}/一层平面图.png")
    print("  ✓ 一层平面图 (DXF + PNG)")


def gen_floor2():
    X1 = F2_X1; Y0 = F2_Y0; Y1 = F2_Y1; Y2 = F2_Y2
    NX1 = F2_NX1; NX2 = F2_NX2; NX3 = F2_NX3

    fills = [
        (OW,OW,BW-2*OW,Y0-OW),                             # 阳台
        (OW,Y0+IW,X1-OW,Y1-Y0-IW),                         # 次卧1
        (X1+IW,Y0+IW,BW-OW-X1-IW,Y1-Y0-IW),               # 次卧2
        (OW,Y1+IW,BW-2*OW,Y2-Y1-IW),                       # 走廊/起居厅
        (OW,Y2+IW,NX1-OW,BH-OW-Y2-IW),                     # 主卧2
        (NX1+IW,Y2+IW,NX2-NX1-IW,BH-OW-Y2-IW),            # 主卫2
        (NX2+IW,Y2+IW,NX3-NX2-IW,BH-OW-Y2-IW),            # 主卧3
        (NX3+IW,Y2+IW,BW-OW-NX3-IW,(BH-OW-Y2-IW)//2),     # 公卫
        (NX3+IW,Y2+IW+(BH-OW-Y2-IW)//2+IW,BW-OW-NX3-IW,(BH-OW-Y2-IW)//2-IW),  # 楼梯间
    ]
    YM = Y2+IW+(BH-OW-Y2-IW)//2  # 公卫|楼梯分界Y
    hwalls = [
        (OW,Y0,BW-2*OW),                                    # 阳台顶墙
        (OW,Y1,BW-2*OW),                                    # 走廊底墙
        (OW,Y2,BW-2*OW),                                    # 主卧区底墙
        (NX3+IW,YM,BW-OW-NX3-IW),                           # 公卫|楼梯
    ]
    vwalls = [
        (X1,Y0+IW,Y1-Y0-IW),                                # 次卧1|次卧2
        (NX1,Y2+IW,BH-OW-Y2-IW),                            # 主卧2|主卫2
        (NX2,Y2+IW,BH-OW-Y2-IW),                            # 主卫2|主卧3
        (NX3,Y2+IW,BH-OW-Y2-IW),                            # 主卧3|公卫+楼梯
    ]

    # DXF
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    for rf in fills: room_fill(msp, *rf)
    outer_walls(msp, BW, BH, OW)
    for w in hwalls: wall_h(msp, *w, t=IW)
    for w in vwalls: wall_v(msp, *w, t=IW)
    dxf_text(msp, BW/2, Y0/2, "南向大阳台", 250)
    dxf_text(msp, (OW+X1)/2, (Y0+Y1)/2, "次卧室1", 250)
    dxf_text(msp, (X1+BW)/2, (Y0+Y1)/2, "次卧室2", 250)
    dxf_text(msp, BW/2, (Y1+Y2)/2, "走廊", 250)
    dxf_text(msp, (OW+NX1)/2, (Y2+BH)/2, "主卧室2", 300)
    dxf_text(msp, (NX1+NX2)/2, (Y2+BH)/2, "主卫2", 200)
    dxf_text(msp, (NX2+NX3)/2, (Y2+BH)/2, "主卧室3", 250)
    dxf_text(msp, (NX3+BW)/2, (Y2+YM)/2, "公卫", 200)
    dxf_text(msp, (NX3+BW)/2, (YM+BH)/2, "楼梯间", 200)
    doc.saveas(f"{DIRS['平面图']}/二层平面图.dxf")

    # PNG
    fp = FloorPlan("二层平面图  Second Floor Plan", "3主卧+2次卧 现代简约别墅")
    for rf in fills: fp.fill_room(*rf)
    fp.draw_outer_walls()
    for w in hwalls: fp.draw_iwall_h(*w)
    for w in vwalls: fp.draw_iwall_v(*w)
    fp.room_label(BW/2,Y0/2,"南向大阳台","Balcony","14.0m×1.5m")
    fp.room_label((OW+X1)/2,(Y0+Y1)/2,"次卧室1","Bedroom 4","4.6m×3.7m")
    fp.room_label((X1+BW)/2,(Y0+Y1)/2,"次卧室2","Bedroom 5","9.0m×3.7m")
    fp.room_label(BW/2,(Y1+Y2)/2,"走廊/起居厅","Hallway","13.5m×2.0m")
    fp.room_label((OW+NX1)/2,(Y2+BH)/2,"主卧室2（夫妻房）","Master BR.2","5.6m×3.6m")
    fp.room_label((NX1+NX2)/2,(Y2+BH)/2,"主卫2","En-suite 2","2.2m×3.6m")
    fp.room_label((NX2+NX3)/2,(Y2+BH)/2,"主卧室3","Master BR.3","3.2m×3.6m")
    fp.room_label((NX3+BW)/2,(Y2+YM)/2,"公卫","WC","2.6m×1.8m")
    fp.room_label((NX3+BW)/2,(YM+BH)/2,"楼梯间","Stairs","2.6m×1.7m")

    # 家具
    fp.bed_double(1500,7800,1800,2000); fp.wardrobe(400,10100,5000,500)
    fp.toilet(NX1+IW+500,8000); fp.sink(NX1+IW+400,9600); fp.shower_room(NX1+IW+200,7500,900)
    fp.bed_double(NX2+IW+400,7800,1800,2000); fp.wardrobe(NX2+IW+200,10100,NX3-NX2-IW-400,500)
    fp.bed_single(1200,Y0+IW+300,1200,2000)
    fp.bed_double(X1+IW+1500,Y0+IW+300,1800,2000)
    fp.desk_chair(X1+IW+5500,Y0+IW+800,1400,550)
    fp.toilet(NX3+IW+400,Y2+IW+400); fp.sink(NX3+IW+300,YM-500)
    fp.stairs(NX3+IW+200,YM+IW+200,2200,BH-OW-YM-IW-400,13,"down")

    # 门 — 每个房间都有门
    fp.door_h(2000,Y1,800,False)                            # 1. 次卧1→走廊
    fp.door_h(X1+IW+2000,Y1,800,False)                     # 2. 次卧2→走廊
    fp.door_h(2500,Y2+IW,900,True)                          # 3. 走廊→主卧2
    fp.door_v(NX1+IW,8800,800,True)                         # 4. 主卫2→主卧2（从卧室内进入）
    fp.door_h(NX2+IW+500,Y2+IW,900,True)                   # 5. 走廊→主卧3
    fp.door_v(NX3+IW,Y2+IW+500,700,False)                  # 6. 公卫→走廊
    fp.door_h(NX3+IW+500,YM,700,True)                      # 7. 楼梯间门

    # 窗户
    fp.window_h(1000,BH,2500)                               # 主卧2北窗
    fp.window_h(NX1+300,BH,1500)                            # 主卫2北窗
    fp.window_h(NX2+500,BH,2000)                            # 主卧3北窗
    fp.window_v(0,8000,2000)                                # 主卧2西窗
    fp.window_v(0,Y0+500,2000)                              # 次卧1西窗
    fp.window_h(1200,Y0,2000)                               # 次卧1阳台窗
    fp.window_h(X1+500,Y0,3000)                             # 次卧2阳台窗
    fp.window_h(X1+4500,Y0,2000)                            # 次卧2阳台窗2
    fp.window_v(BW,8500,2000)                               # 主卧3东窗（或楼梯窗）
    fp.window_v(BW,Y0+500,2000)                             # 次卧2东窗

    # 尺寸
    fp.dim_h(0,X1,0); fp.dim_h(X1,BW,0); fp.dim_total_h(0,BW,0)
    fp.dim_v(0,Y0,BW); fp.dim_v(Y0,Y1,BW); fp.dim_v(Y1,Y2,BW); fp.dim_v(Y2,BH,BW); fp.dim_total_v(0,BH,BW)
    fp.dim_h(0,NX1,BH); fp.dim_h(NX1,NX2,BH); fp.dim_h(NX2,NX3,BH); fp.dim_h(NX3,BW,BH)
    fp.info_block("二层"); fp.north_arrow()
    fp.save(f"{IMG_DIR}/二层平面图.png")
    print("  ✓ 二层平面图 (DXF + PNG)")


# ══════════════════════════════════════════════
#  立面图 DXF + PNG
# ══════════════════════════════════════════════

def _elev_dxf(name, width_m, windows, doors, filename):
    """生成立面图DXF"""
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    S = 1000  # 1m = 1000mm

    w = width_m * S; gl = 0; f1fl = int(F1_FL*S); f1cl = int(F1_CL*S)
    f2fl = int(F2_FL*S); f2cl = int(F2_CL*S); roof = int(ROOF*S); top = int(TOP*S)
    wt = int(WALL_T*S)

    # 外轮廓
    msp.add_lwpolyline([(0,gl),(0,top),(w,top),(w,gl),(0,gl)], close=True,
                        dxfattribs={"layer": "WALL", "lineweight": 50, "color": BLACK})
    # 楼层线
    for y in [f1cl, f2fl, f2cl, roof]:
        msp.add_line((0,y),(w,y), dxfattribs={"layer": "WALL", "color": GRAY, "linetype": "DASHED"})
    # 地面线
    msp.add_line((-1000,gl),(w+1000,gl), dxfattribs={"layer": "GROUND", "lineweight": 30})

    # 窗户
    for (x,y,ww,wh,divs) in windows:
        xi=int(x*S); yi=int(y*S); wi=int(ww*S); hi=int(wh*S)
        msp.add_lwpolyline([(xi,yi),(xi+wi,yi),(xi+wi,yi+hi),(xi,yi+hi),(xi,yi)],
                            close=True, dxfattribs={"layer": "WINDOW", "color": BLUE})
        msp.add_line((xi,yi+hi//2),(xi+wi,yi+hi//2), dxfattribs={"layer": "WINDOW", "color": BLUE})
        for d in range(1, divs):
            dx = xi + d*wi//divs
            msp.add_line((dx,yi),(dx,yi+hi), dxfattribs={"layer": "WINDOW", "color": BLUE})

    # 门
    for (x,y,dw,dh) in doors:
        xi=int(x*S); yi=int(y*S); di=int(dw*S); hi=int(dh*S)
        msp.add_lwpolyline([(xi,yi),(xi+di,yi),(xi+di,yi+hi),(xi,yi+hi),(xi,yi)],
                            close=True, dxfattribs={"layer": "DOOR", "color": BLACK})

    # 标高
    for (y, txt) in [(gl,"±0.000"),(f1fl,f"+{F1_FL:.3f}"),(f2fl,f"+{F2_FL:.3f}"),(roof,f"+{ROOF:.3f}"),(top,f"+{TOP:.3f}")]:
        msp.add_line((-200,y),(0,y), dxfattribs={"layer": "DIM", "color": RED})
        msp.add_text(txt, height=100, dxfattribs={"layer": "DIM", "color": RED}).set_placement(
            (-300, y), align=TextEntityAlignment.MIDDLE_RIGHT)

    dxf_dim_h(msp, 0, w, gl)
    dxf_dim_v(msp, gl, top, w)
    dxf_text(msp, w/2, top+500, name, 300)
    doc.saveas(f"{DIRS['立面图']}/{filename}.dxf")


def _elev_png(title, width_m, windows, doors, filename, has_balcony=False):
    """生成立面图PNG"""
    fig, ax = plt.subplots(1,1,figsize=(16,9),dpi=150,facecolor=C_BG)
    ax.set_facecolor(C_BG); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", color=C_TEXT, pad=12)

    w = width_m
    ax.fill_between([-1,w+1],[-0.3,-0.3],[0,0],color=C_GROUND,alpha=0.3,zorder=1)
    ax.plot([-1,w+1],[0,0],color=C_LINE,linewidth=1.5,zorder=3)
    ax.plot([0,0,w,w],[GL,TOP,TOP,GL],color=C_WALL,linewidth=2,zorder=5)
    ax.plot([0,w],[GL,GL],color=C_WALL,linewidth=2,zorder=5)
    for yl in [F1_CL,F2_FL,F2_CL,ROOF]:
        ax.plot([0,w],[yl,yl],color=C_LINE,linewidth=0.5,linestyle="--",zorder=3)

    for (x,y,ww,wh,divs) in windows:
        ax.add_patch(patches.Rectangle((x,y),ww,wh,facecolor=C_GLASS,edgecolor=C_LINE,linewidth=1,zorder=4))
        for d in range(1,divs):
            ax.plot([x+d*ww/divs,x+d*ww/divs],[y,y+wh],color=C_LINE,linewidth=0.5,zorder=4)
        ax.plot([x,x+ww],[y+wh/2,y+wh/2],color=C_LINE,linewidth=0.3,zorder=4)

    for (x,y,dw,dh) in doors:
        ax.add_patch(patches.Rectangle((x,y),dw,dh,facecolor="#E8DCC8",edgecolor=C_LINE,linewidth=1,zorder=4))

    if has_balcony:
        ax.add_patch(patches.Rectangle((0.24,F2_FL-1.1),w-0.48,1.1,facecolor="none",edgecolor=C_LINE,linewidth=0.8,zorder=4))
        for i in range(1,28):
            bx = 0.24 + i*(w-0.48)/28
            ax.plot([bx,bx],[F2_FL-1.1,F2_FL],color=C_LINE,linewidth=0.3,zorder=4)

    # 标高
    for (yy,txt) in [(GL,"±0.000"),(F1_FL,f"+{F1_FL:.3f}"),(F2_FL,f"+{F2_FL:.3f}"),(ROOF,f"+{ROOF:.3f}"),(TOP,f"+{TOP:.3f}")]:
        ax.plot([-0.15,0],[yy,yy],color=C_DIM,linewidth=0.4,zorder=8)
        ax.text(-0.2,yy,txt,ha="right",va="center",fontsize=5.5,color=C_DIM,zorder=8)

    def dim_h(x1,x2,y,off=-0.6):
        yo=y+off; ax.plot([x1,x2],[yo,yo],color=C_DIM,linewidth=0.6,zorder=8)
        ax.plot([x1,x1],[y,yo],color=C_DIM,linewidth=0.4,zorder=8); ax.plot([x2,x2],[y,yo],color=C_DIM,linewidth=0.4,zorder=8)
        ax.text((x1+x2)/2,yo+0.04,f"{abs(x2-x1)*1000:.0f}",ha="center",va="bottom",fontsize=6,color=C_DIM,zorder=8)
    def dim_v(y1,y2,x,off=0.6):
        xo=x+off; ax.plot([xo,xo],[y1,y2],color=C_DIM,linewidth=0.6,zorder=8)
        ax.plot([x,xo],[y1,y1],color=C_DIM,linewidth=0.4,zorder=8); ax.plot([x,xo],[y2,y2],color=C_DIM,linewidth=0.4,zorder=8)
        ax.text(xo+0.04,(y1+y2)/2,f"{abs(y2-y1)*1000:.0f}",ha="left",va="center",fontsize=6,color=C_DIM,rotation=90,zorder=8)

    dim_h(0,w,GL); dim_v(GL,F1_FL,-0.2,offset=-0.8) if False else None
    dim_v(GL,TOP,w)

    ax.set_xlim(-2.5,w+1.5); ax.set_ylim(-1.5,TOP+1.0)
    fig.savefig(f"{IMG_DIR}/{filename}.png",bbox_inches="tight",pad_inches=0.3,dpi=150,facecolor=C_BG)
    plt.close(fig)


def gen_elevations():
    _elev_dxf("南立面图", W_m, SOUTH_WIN, SOUTH_DOOR, "南立面图")
    _elev_png("南立面图  South Elevation", W_m, SOUTH_WIN, SOUTH_DOOR, "南立面图", has_balcony=True)
    print("  ✓ 南立面图 (DXF + PNG)")

    _elev_dxf("北立面图", W_m, NORTH_WIN, [], "北立面图")
    _elev_png("北立面图  North Elevation", W_m, NORTH_WIN, [], "北立面图")
    print("  ✓ 北立面图 (DXF + PNG)")

    _elev_dxf("东立面图", D_m, EAST_WIN, [], "东立面图")
    _elev_png("东立面图  East Elevation", D_m, EAST_WIN, [], "东立面图")
    print("  ✓ 东立面图 (DXF + PNG)")

    _elev_dxf("西立面图", D_m, WEST_WIN, [], "西立面图")
    _elev_png("西立面图  West Elevation", D_m, WEST_WIN, [], "西立面图")
    print("  ✓ 西立面图 (DXF + PNG)")


# ══════════════════════════════════════════════
#  剖面图 DXF + PNG
# ══════════════════════════════════════════════

def gen_section():
    S = 1000; d = int(D_m*S)
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    wt = int(WALL_T*S); gl=0; f1fl=int(F1_FL*S); f1cl=int(F1_CL*S); f2fl=int(F2_FL*S)
    f2cl=int(F2_CL*S); roof_i=int(ROOF*S); top_i=int(TOP*S); slab_i=int(SLAB*S)

    # 外墙
    wall_v(msp, 0, gl, top_i-gl, wt)
    wall_v(msp, d-wt, gl, top_i-gl, wt)
    # 楼板
    wall_h(msp, 0, f1cl, d, slab_i)
    wall_h(msp, 0, f2cl, d, slab_i)
    # 女儿墙
    wall_v(msp, 0, roof_i, int(PARAPET*S), wt)
    wall_v(msp, d-wt, roof_i, int(PARAPET*S), wt)
    # 地面线
    msp.add_line((-1000,gl),(d+1000,gl), dxfattribs={"layer": "GROUND", "lineweight": 30})
    # 基础
    msp.add_lwpolyline([(-300,-500),(d+300,-500),(d+300,gl),(-300,gl),(-300,-500)],
                        close=True, dxfattribs={"layer": "HATCH", "color": GRAY})
    # 内墙（一层Y1=7200处，二层Y2=7200处）
    iw_i = int(0.12*S)
    wall_v(msp, 7200-iw_i//2, f1fl, int(F1H*S), iw_i)
    wall_v(msp, 7200-iw_i//2, f2fl, int(F2H*S), iw_i)
    # 楼梯（位于Y=7.2~10.8m区域北侧）
    n=14; stx=7200; stw=3600
    for i in range(n):
        sx=stx+i*stw//n; sy=f1fl+i*(f2fl-f1fl)//n
        sw=stw//n; sh=(f2fl-f1fl)//n
        msp.add_lwpolyline([(sx,sy),(sx+sw,sy),(sx+sw,sy+sh),(sx,sy+sh),(sx,sy)],
                            close=True, dxfattribs={"layer": "STAIRS", "color": GRAY})
    # 标注
    dxf_text(msp, 3500, f1fl+int(F1H*S)//2, "一层 F1", 300)
    dxf_text(msp, 3500, f2fl+int(F2H*S)//2, "二层 F2", 300)
    dxf_dim_h(msp, 0, d, gl)
    dxf_dim_v(msp, gl, top_i, d)
    dxf_text(msp, d//2, top_i+600, "1-1 剖面图", 350)
    doc.saveas(f"{DIRS['剖面图']}/1-1剖面图.dxf")

    # PNG（复用之前的逻辑）
    fig, ax = plt.subplots(1,1,figsize=(14,10),dpi=150,facecolor=C_BG)
    ax.set_facecolor(C_BG); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("1-1 剖面图  Section 1-1",fontsize=16,fontweight="bold",color=C_TEXT,pad=12)
    ax.fill_between([-1,D_m+1],[-0.5,-0.5],[0,0],color=C_GROUND,alpha=0.3,zorder=1)
    ax.plot([-1,D_m+1],[0,0],color=C_LINE,linewidth=1.5,zorder=3)
    ax.add_patch(patches.Rectangle((-0.3,-0.5),D_m+0.6,0.5,facecolor="#E0D8C8",edgecolor=C_LINE,linewidth=0.8,zorder=2))
    ax.add_patch(patches.Rectangle((0,GL),WALL_T,TOP-GL,facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    ax.add_patch(patches.Rectangle((D_m-WALL_T,GL),WALL_T,TOP-GL,facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    ax.add_patch(patches.Rectangle((0,F1_CL),D_m,SLAB,facecolor="#C0C0C0",edgecolor=C_LINE,linewidth=0.8,zorder=5))
    ax.add_patch(patches.Rectangle((0,F2_CL),D_m,SLAB,facecolor="#C0C0C0",edgecolor=C_LINE,linewidth=0.8,zorder=5))
    ax.add_patch(patches.Rectangle((0,ROOF),WALL_T,PARAPET,facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    ax.add_patch(patches.Rectangle((D_m-WALL_T,ROOF),WALL_T,PARAPET,facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    ax.add_patch(patches.Rectangle((WALL_T,F1_FL),D_m-2*WALL_T,F1H,facecolor=C_ROOM,edgecolor="none",alpha=0.3,zorder=1))
    ax.add_patch(patches.Rectangle((WALL_T,F2_FL),D_m-2*WALL_T,F2H,facecolor=C_ROOM,edgecolor="none",alpha=0.3,zorder=1))
    iw=0.12
    ax.add_patch(patches.Rectangle((7.2-iw/2,F1_FL),iw,F1H,facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    ax.add_patch(patches.Rectangle((7.2-iw/2,F2_FL),iw,F2H,facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    n=14; stx=7.2; stw=3.6
    for i in range(n):
        sx=stx+i*stw/n; sy=F1_FL+i*(F2_FL-F1_FL)/n; sw=stw/n; sh=(F2_FL-F1_FL)/n
        ax.add_patch(patches.Rectangle((sx,sy),sw,sh,facecolor="none",edgecolor=C_STAIR,linewidth=0.5,zorder=4))
    for wy in [F1_FL+0.9,F2_FL+0.9]:
        ax.add_patch(patches.Rectangle((0,wy),WALL_T,1.5,facecolor=C_GLASS,edgecolor=C_LINE,linewidth=0.8,zorder=6))
        ax.add_patch(patches.Rectangle((D_m-WALL_T,wy),WALL_T,1.5,facecolor=C_GLASS,edgecolor=C_LINE,linewidth=0.8,zorder=6))
    for (yy,txt) in [(GL,"±0.000"),(F1_FL,f"+{F1_FL:.3f}"),(F2_FL,f"+{F2_FL:.3f}"),(ROOF,f"+{ROOF:.3f}"),(TOP,f"+{TOP:.3f}")]:
        ax.plot([-0.5,0],[yy,yy],color=C_DIM,linewidth=0.4,zorder=8)
        ax.text(-0.6,yy,txt,ha="right",va="center",fontsize=5.5,color=C_DIM,zorder=8)
    ax.text(3.5,F1_FL+F1H/2,"一层 F1",ha="center",va="center",fontsize=12,color=C_TEXT2,zorder=10)
    ax.text(3.5,F2_FL+F2H/2,"二层 F2",ha="center",va="center",fontsize=12,color=C_TEXT2,zorder=10)
    ax.set_xlim(-2.5,D_m+2.5); ax.set_ylim(-1.2,TOP+1.0)
    fig.savefig(f"{IMG_DIR}/1-1剖面图.png",bbox_inches="tight",pad_inches=0.3,dpi=150,facecolor=C_BG)
    plt.close(fig)
    print("  ✓ 1-1剖面图 (DXF + PNG)")


# ══════════════════════════════════════════════
#  屋顶平面图 DXF + PNG
# ══════════════════════════════════════════════

def gen_roof():
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    outer_walls(msp, BW, BH, OW)
    # 排水沟
    inset = 600
    msp.add_lwpolyline([(inset,inset),(BW-inset,inset),(BW-inset,BH-inset),(inset,BH-inset),(inset,inset)],
                        close=True, dxfattribs={"layer": "DIM", "color": GRAY, "linetype": "DASHED"})
    # 落水管
    for (px,py) in [(500,500),(BW-500,500),(500,BH-500),(BW-500,BH-500)]:
        msp.add_circle((px,py), 55, dxfattribs={"layer": "FIXTURE", "color": BLACK})
    # 检修口
    msp.add_lwpolyline([(6500,5000),(7300,5000),(7300,5800),(6500,5800),(6500,5000)],
                        close=True, dxfattribs={"layer": "FIXTURE", "color": BLACK})
    dxf_text(msp, BW//2, BH//2, "屋面找坡层 i=3%", 300)
    dxf_text(msp, 6900, 5400, "检修口 800×800", 150)
    dxf_dim_h(msp, 0, BW, 0); dxf_dim_v(msp, 0, BH, BW)
    dxf_text(msp, BW//2, BH+800, "屋顶平面图", 350)
    doc.saveas(f"{DIRS['屋顶']}/屋顶平面图.dxf")

    # PNG（复用之前逻辑）
    fig, ax = plt.subplots(1,1,figsize=(16,13),dpi=150,facecolor=C_BG)
    ax.set_facecolor(C_BG); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("屋顶平面图  Roof Plan",fontsize=16,fontweight="bold",color=C_TEXT,pad=12)
    s = _s
    ax.add_patch(patches.Rectangle((s(OW),s(OW)),s(BW-2*OW),s(BH-2*OW),facecolor="#E8E8E8",edgecolor="none",zorder=1))
    for (x,y,w,h) in [(0,0,BW,OW),(0,BH-OW,BW,OW),(0,0,OW,BH),(BW-OW,0,OW,BH)]:
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor=C_WALL,edgecolor=C_WALL,linewidth=0.5,zorder=5))
    cx,cy = s(BW/2),s(BH/2)
    for dx,dy,lb in [(0,-1,"i=3%"),(0,1,"i=3%"),(-1,0,"i=3%"),(1,0,"i=3%")]:
        ex=cx+dx*2.0; ey=cy+dy*2.0
        ax.annotate("",xy=(ex,ey),xytext=(cx,cy),arrowprops=dict(arrowstyle="->",color=C_DIM,lw=1),zorder=8)
        ax.text(cx+dx*2.3,cy+dy*2.3,lb,ha="center",va="center",fontsize=7,color=C_DIM,rotation=90 if dx!=0 else 0,zorder=8)
    ax.add_patch(patches.Rectangle((s(600),s(600)),s(BW-1200),s(BH-1200),facecolor="none",edgecolor=C_LINE,linewidth=0.5,linestyle="--",zorder=3))
    for px,py in [(s(500),s(500)),(s(BW-500),s(500)),(s(500),s(BH-500)),(s(BW-500),s(BH-500))]:
        ax.add_patch(patches.Circle((px,py),0.08,facecolor=C_WALL,edgecolor=C_WALL,zorder=6))
        ax.text(px,py-0.2,"落水管\nφ110",ha="center",va="top",fontsize=5,color=C_TEXT2,zorder=10)
    ax.add_patch(patches.Rectangle((s(6500),s(5000)),s(800),s(800),facecolor="none",edgecolor=C_LINE,linewidth=0.8,zorder=4))
    ax.text(s(6900),s(5400),"检修口\n800×800",ha="center",va="center",fontsize=6,color=C_TEXT2,zorder=10)
    ax.text(s(BW/2),s(BH/2)-0.3,"屋面找坡层",ha="center",va="center",fontsize=11,color=C_TEXT2,zorder=10)
    nx,ny = -1.0,s(BH)-1.0
    ax.annotate("",xy=(nx,ny+0.7),xytext=(nx,ny),arrowprops=dict(arrowstyle="-|>",color=C_TEXT,lw=1.5),zorder=10)
    ax.text(nx,ny+0.85,"N",ha="center",va="bottom",fontsize=10,fontweight="bold",color=C_TEXT,zorder=10)
    ax.set_xlim(-2.0,s(BW)+2.0); ax.set_ylim(-1.5,s(BH)+1.5)
    fig.savefig(f"{IMG_DIR}/屋顶平面图.png",bbox_inches="tight",pad_inches=0.3,dpi=150,facecolor=C_BG)
    plt.close(fig)
    print("  ✓ 屋顶平面图 (DXF + PNG)")


# ══════════════════════════════════════════════
#  给排水 DXF + PNG（简化DXF，详细PNG）
# ══════════════════════════════════════════════

def _plumbing_dxf(floor_name, pipes_supply, pipes_drain, pipes_hot, fixtures, filename):
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    outer_walls(msp, BW, BH, OW)
    for pts in pipes_supply:
        msp.add_lwpolyline(pts, dxfattribs={"layer": "PIPE-SUPPLY", "color": 5})
    for pts in pipes_drain:
        msp.add_lwpolyline(pts, dxfattribs={"layer": "PIPE-DRAIN", "color": 42, "linetype": "DASHED"})
    for pts in pipes_hot:
        msp.add_lwpolyline(pts, dxfattribs={"layer": "PIPE-HOT", "color": 1})
    for (x,y,txt) in fixtures:
        msp.add_circle((x,y), 80, dxfattribs={"layer": "FIXTURE", "color": 5})
        dxf_text(msp, x, y-200, txt, 120)
    dxf_text(msp, BW//2, BH+600, f"{floor_name}给排水平面图", 350)
    doc.saveas(f"{DIRS['给排水']}/{filename}.dxf")


def _plumbing_png(title, floor_name, walls, pipes_s, pipes_d, pipes_h, fixtures, filename):
    """给排水 PNG 专业预览：管径标注、立管编号、阀门水表、房间名称、增强图例"""
    fig, ax = plt.subplots(1,1,figsize=(16,13),dpi=150,facecolor=C_BG)
    ax.set_facecolor(C_BG); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", color=C_TEXT, pad=12)
    s = _s
    # 墙体
    for (x,y,w,h) in [(0,0,BW,OW),(0,BH-OW,BW,OW),(0,0,OW,BH),(BW-OW,0,OW,BH)]:
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#E0E0E0",edgecolor=C_LINE,linewidth=0.3,zorder=2))
    ax.add_patch(patches.Rectangle((s(OW),s(OW)),s(BW-2*OW),s(BH-2*OW),facecolor=C_BG,edgecolor="none",zorder=1))
    for (x,y,w,h) in walls:
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#E0E0E0",edgecolor=C_LINE,linewidth=0.2,zorder=2))

    # 绘制给水管（蓝色实线 2.5）
    for pts in pipes_s:
        for i in range(len(pts)-1):
            p1,p2=pts[i],pts[i+1]
            mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2
            ax.plot([s(p[0]) for p in [p1,p2]],[s(p[1]) for p in [p1,p2]],color=C_WATER_SUPPLY,linewidth=2.5,zorder=7)
            rot=math.degrees(math.atan2(p2[1]-p1[1],p2[0]-p1[0]))
            ax.text(s(mx),s(my),"DN25" if i==0 or (p1[0]==p2[0] and abs(p2[1]-p1[1])>3000) else "DN20",ha="center",va="center",fontsize=5,color=C_TEXT,bbox=dict(boxstyle="round,pad=0.15",facecolor="white",edgecolor="none"),rotation=rot if -90<rot<90 else rot+180,zorder=9)
    # 绘制排水管（棕色虚线 2.5）
    for pts in pipes_d:
        for i in range(len(pts)-1):
            p1,p2=pts[i],pts[i+1]
            mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2
            ax.plot([s(p[0]) for p in [p1,p2]],[s(p[1]) for p in [p1,p2]],color=C_WATER_DRAIN,linewidth=2.5,linestyle="--",zorder=7)
            rot=math.degrees(math.atan2(p2[1]-p1[1],p2[0]-p1[0]))
            ax.text(s(mx),s(my),"DN110" if abs(p2[0]-p1[0])<100 or abs(p2[1]-p1[1])>4000 else "DN50",ha="center",va="center",fontsize=5,color=C_TEXT,bbox=dict(boxstyle="round,pad=0.15",facecolor="white",edgecolor="none"),rotation=rot if -90<rot<90 else rot+180,zorder=9)
    # 绘制热水管（红色实线 2.0）
    for pts in pipes_h:
        for i in range(len(pts)-1):
            p1,p2=pts[i],pts[i+1]
            mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2
            ax.plot([s(p[0]) for p in [p1,p2]],[s(p[1]) for p in [p1,p2]],color=C_HOTWATER,linewidth=2.0,zorder=7)
            rot=math.degrees(math.atan2(p2[1]-p1[1],p2[0]-p1[0]))
            ax.text(s(mx),s(my),"DN20",ha="center",va="center",fontsize=5,color=C_TEXT,bbox=dict(boxstyle="round,pad=0.15",facecolor="white",edgecolor="none"),rotation=rot if -90<rot<90 else rot+180,zorder=9)

    # 立管编号：收集给水/排水立管位置（建筑边界的端点，去重）
    riser_supply, riser_drain = [], []
    def _near_edge(x,y):
        return x<=600 or x>=BW-600 or y<=600 or y>=BH-600
    def _key(p):
        return (round(p[0]/500)*500, round(p[1]/500)*500)
    seen_s = set()
    for pts in pipes_s:
        for pt in [pts[0], pts[-1]]:
            if _near_edge(pt[0],pt[1]) and _key(pt) not in seen_s:
                seen_s.add(_key(pt)); riser_supply.append(pt)
    seen_d = set()
    for pts in pipes_d:
        for pt in [pts[0], pts[-1]]:
            if _near_edge(pt[0],pt[1]) and _key(pt) not in seen_d:
                seen_d.add(_key(pt)); riser_drain.append(pt)
    for i, pt in enumerate(riser_supply):
        ax.add_patch(patches.Circle((s(pt[0]),s(pt[1])),0.12,facecolor="white",edgecolor=C_WATER_SUPPLY,linewidth=1.5,zorder=10))
        ax.text(s(pt[0]),s(pt[1]),f"JL-{i+1}",ha="center",va="center",fontsize=6,fontweight="bold",color=C_WATER_SUPPLY,zorder=11)
    for i, pt in enumerate(riser_drain):
        ax.add_patch(patches.Circle((s(pt[0]),s(pt[1])),0.12,facecolor="white",edgecolor=C_WATER_DRAIN,linewidth=1.5,zorder=10))
        ax.text(s(pt[0]),s(pt[1]),f"WL-{i+1}",ha="center",va="center",fontsize=6,fontweight="bold",color=C_WATER_DRAIN,zorder=11)

    # 阀门符号（蝴蝶形 ▷◁）：在每个 fixture 入口及主管分支处
    def draw_valve(ax, x, y, color, zorder):
        r = 0.06
        t1 = plt.Polygon([(s(x)-r,s(y)), (s(x)+r*0.3,s(y)-r*0.6), (s(x)+r*0.3,s(y)+r*0.6)], facecolor="white", edgecolor=color, linewidth=1.2, zorder=zorder)
        t2 = plt.Polygon([(s(x)+r,s(y)), (s(x)-r*0.3,s(y)-r*0.6), (s(x)-r*0.3,s(y)+r*0.6)], facecolor="white", edgecolor=color, linewidth=1.2, zorder=zorder)
        ax.add_patch(t1); ax.add_patch(t2)
    for (x,y,txt,c) in fixtures:
        draw_valve(ax, x, y, c, 9)
    if pipes_s:
        for pt in pipes_s[0][:2]:
            draw_valve(ax, pt[0], pt[1], C_WATER_SUPPLY, 9)

    # 水表符号（菱形+W）：入户处
    if pipes_s:
        inlet = pipes_s[0][0]
        dx, dy = 0.1, 0.1
        diamond = [(s(inlet[0]),s(inlet[1])+dy), (s(inlet[0])+dx,s(inlet[1])), (s(inlet[0]),s(inlet[1])-dy), (s(inlet[0])-dx,s(inlet[1]))]
        ax.add_patch(plt.Polygon(diamond, facecolor="white", edgecolor=C_WATER_SUPPLY, linewidth=1.2, zorder=10))
        ax.text(s(inlet[0]),s(inlet[1]),"W",ha="center",va="center",fontsize=7,fontweight="bold",color=C_WATER_SUPPLY,zorder=11)

    # 房间名称（浅灰大字号，与平面图一致）
    C_ROOM_LABEL = "#AAAAAA"
    if floor_name == "一层":
        rooms = [((OW+F1_X1)/2,(OW+F1_Y0)/2,"客厅"),((F1_X1+BW)/2,(OW+F1_Y0)/2,"玄关"),((OW+F1_X1)/2,(F1_Y0+F1_Y1)/2,"客餐厅 LDK"),
                 ((F1_X1+F1_MX1)/2,(F1_Y0+F1_Y1)/2,"主卧室1"),((F1_MX1+BW)/2,(F1_Y0+F1_MY1)/2,"主卫1"),((F1_MX1+BW)/2,(F1_MY1+F1_Y1)/2,"衣帽间"),
                 ((OW+F1_NX1)/2,(F1_Y1+BH)/2,"厨房"),((F1_NX1+F1_NX2)/2,(F1_Y1+BH)/2,"客卫"),((F1_NX2+BW)/2,(F1_Y1+BH)/2,"楼梯间")]
    else:
        YM = F2_Y2+IW+(BH-OW-F2_Y2-IW)//2
        rooms = [(BW/2,F2_Y0/2,"南向大阳台"),((OW+F2_X1)/2,(F2_Y0+F2_Y1)/2,"次卧室1"),((F2_X1+BW)/2,(F2_Y0+F2_Y1)/2,"次卧室2"),
                 (BW/2,(F2_Y1+F2_Y2)/2,"走廊"),((OW+F2_NX1)/2,(F2_Y2+BH)/2,"主卧室2"),((F2_NX1+F2_NX2)/2,(F2_Y2+BH)/2,"主卫2"),
                 ((F2_NX2+F2_NX3)/2,(F2_Y2+BH)/2,"主卧室3"),((F2_NX3+BW)/2,(F2_Y2+YM)/2,"公卫"),((F2_NX3+BW)/2,(YM+BH)/2,"楼梯间")]
    for cx,cy,name in rooms:
        ax.text(s(cx),s(cy),name,ha="center",va="center",fontsize=14,color=C_ROOM_LABEL,zorder=4)

    # 给水器具符号：淋浴头/水龙头/地漏轮廓
    def fixture_shower(ax, x, y, color):
        ax.add_patch(patches.Circle((s(x),s(y)),0.06,facecolor="white",edgecolor=color,linewidth=1,zorder=8))
        for i in range(6):
            ang = i*60 * math.pi/180
            ax.plot([s(x),s(x)+0.08*math.cos(ang)],[s(y),s(y)+0.08*math.sin(ang)],color=color,linewidth=0.8,zorder=8)
    def fixture_faucet(ax, x, y, color):
        ax.add_patch(patches.Rectangle((s(x)-0.04,s(y)-0.03),0.08,0.06,facecolor="none",edgecolor=color,linewidth=1,zorder=8))
        ax.plot([s(x)-0.02,s(x)+0.02],[s(y),s(y)],color=color,linewidth=1,zorder=8)
    def fixture_drain(ax, x, y, color):
        ax.add_patch(patches.Circle((s(x),s(y)),0.05,facecolor="white",edgecolor=color,linewidth=1,zorder=8))
        ax.plot([s(x)-0.04,s(x)+0.04],[s(y),s(y)],color=color,linewidth=0.8,zorder=8)
    for (x,y,txt,c) in fixtures:
        if "主卫" in txt and "给水" in txt:
            fixture_shower(ax, x, y, c)
        elif "排水" in txt:
            fixture_drain(ax, x, y, c)
        else:
            fixture_faucet(ax, x, y, c)
        ax.text(s(x),s(y)-0.22,txt,ha="center",va="top",fontsize=5,color=c,zorder=10)

    # 增强图例
    lx, ly = s(BW)+1.0, s(BH)-0.2
    ax.text(lx,ly+0.5,"图例",fontsize=9,fontweight="bold",color=C_TEXT,zorder=10)
    items = [(C_WATER_SUPPLY,"给水管 DN20/25","line",2.5,False),(C_WATER_DRAIN,"排水管 DN50/110","line",2.5,True),(C_HOTWATER,"热水管 DN20","line",2.0,False)]
    for i,(c,txt,kind,lw,dash) in enumerate(items):
        yy = ly - i*0.35
        ax.plot([lx,lx+0.45],[yy,yy],color=c,linewidth=lw,linestyle="--" if dash else "-",zorder=10)
        ax.text(lx+0.5,yy,txt,va="center",fontsize=6,color=C_TEXT,zorder=10)
    ax.add_patch(patches.Circle((lx+0.22,ly-1.2),0.08,facecolor="white",edgecolor=C_WATER_SUPPLY,zorder=10))
    ax.text(lx+0.35,ly-1.2,"立管 JL/WL",va="center",fontsize=6,color=C_TEXT,zorder=10)
    draw_valve(ax, (lx+0.22)*1000, (ly-1.55)*1000, C_LINE, 10)
    ax.text(lx+0.35,ly-1.55,"阀门",va="center",fontsize=6,color=C_TEXT,zorder=10)
    dx2,dy2=0.08,0.08; dm=[(0,dy2),(dx2,0),(0,-dy2),(-dx2,0)]
    ax.add_patch(plt.Polygon([(lx+0.22+d,ly-1.9+e) for d,e in dm],facecolor="white",edgecolor=C_WATER_SUPPLY,linewidth=1,zorder=10))
    ax.text(lx+0.35,ly-1.9,"水表",va="center",fontsize=6,color=C_TEXT,zorder=10)

    nx,ny = -1.0,s(BH)-1.0
    ax.annotate("",xy=(nx,ny+0.7),xytext=(nx,ny),arrowprops=dict(arrowstyle="-|>",color=C_TEXT,lw=1.5),zorder=10)
    ax.text(nx,ny+0.85,"N",ha="center",va="bottom",fontsize=10,fontweight="bold",color=C_TEXT,zorder=10)
    ax.set_xlim(-2.0,s(BW)+4.0); ax.set_ylim(-1.5,s(BH)+1.5)
    fig.savefig(f"{IMG_DIR}/{filename}.png",bbox_inches="tight",pad_inches=0.3,dpi=150,facecolor=C_BG)
    plt.close(fig)


def gen_plumbing():
    # 新布局: X1=8200, Y0=2200, Y1=7200, NX1=4800, NX2=6600, MX1=12000, MY1=4200
    f1_walls = [(240,2200,7960,120),(8320,2200,BW-240-8320,120),(240,7200,BW-480,120),
                (8200,240,120,6960),(12000,2320,120,4880),(12120,4200,BW-240-12120,120),
                (4800,7320,120,BH-240-7320),(6600,7320,120,BH-240-7320)]
    f1_ps = [[(2500,10500),(2500,8000),(4200,8000)],
             [(12500,4500),(12500,3500)],
             [(5200,8000),(5200,9500)]]
    f1_pd = [[(2000,9000),(2000,10500),(500,10500)],
             [(5500,9500),(5500,10500),(3000,10500)],
             [(12300,3200),(12300,200),(500,200)]]
    f1_ph = [[(2500,10500),(2500,8200),(4200,8200)],
             [(12500,4500),(12500,3800)]]
    f1_fix = [(2500,8000,"厨房给水",C_WATER_SUPPLY),(12500,3500,"主卫1给水",C_WATER_SUPPLY),(5200,9500,"客卫给水",C_WATER_SUPPLY),
              (2000,9000,"厨房排水",C_WATER_DRAIN),(12300,3200,"主卫1排水",C_WATER_DRAIN),(5500,9500,"客卫排水",C_WATER_DRAIN)]

    _plumbing_dxf("一层", f1_ps, f1_pd, f1_ph,
        [(x,y,t) for (x,y,t,c) in f1_fix], "一层给排水平面图")
    _plumbing_png("一层给排水平面图  1F Plumbing Plan", "一层", f1_walls, f1_ps, f1_pd, f1_ph, f1_fix, "一层给排水平面图")

    # 二层墙体: X1=4500,X2=9800,X3=11800,Y0=1500,Y1=4800,Y2=7200
    f2_walls = [(240,1500,BW-480,120),(240,5200,BW-480,120),
                (240,7200,BW-480,120),(4800,1620,120,3580),
                (5800,7320,120,3440),(8000,7320,120,3440),
                (11200,7320,120,3440)]
    f2_ps = [[(6500,8500),(6200,8500),(6200,9500)],
             [(9000,8500),(9000,9500)],
             [(11800,7500),(11800,7000)]]
    f2_pd = [[(5900,9000),(5900,10500),(500,10500)],
             [(9200,9000),(13500,9000),(13500,200)],
             [(12000,7200),(12000,200),(10000,200)]]
    f2_ph = [[(6500,8500),(6200,8500),(6200,9500)],
             [(9000,8500),(9200,8500),(9200,9500)]]
    f2_fix = [(6200,9500,"主卫2给水",C_WATER_SUPPLY),(9000,9500,"主卧3给水",C_WATER_SUPPLY),(11800,7000,"公卫给水",C_WATER_SUPPLY),
              (5900,9000,"主卫2排水",C_WATER_DRAIN),(9200,9000,"主卧3排水",C_WATER_DRAIN),(12000,7200,"公卫排水",C_WATER_DRAIN)]

    _plumbing_dxf("二层", f2_ps, f2_pd, f2_ph,
        [(x,y,t) for (x,y,t,c) in f2_fix], "二层给排水平面图")
    _plumbing_png("二层给排水平面图  2F Plumbing Plan", "二层", f2_walls, f2_ps, f2_pd, f2_ph, f2_fix, "二层给排水平面图")
    print("  ✓ 给排水图 (DXF + PNG) × 2")


# ══════════════════════════════════════════════
#  电气 DXF + PNG
# ══════════════════════════════════════════════

def _elec_dxf(floor_name, lights, sockets, switches, filename):
    doc = ezdxf.new("R2010"); doc.units = units.MM; setup_layers(doc); msp = doc.modelspace()
    outer_walls(msp, BW, BH, OW)
    for (x,y,txt) in lights:
        msp.add_circle((x,y), 100, dxfattribs={"layer": "ELEC-LIGHT", "color": 2})
        msp.add_line((x-70,y-70),(x+70,y+70), dxfattribs={"layer": "ELEC-LIGHT", "color": 2})
        msp.add_line((x-70,y+70),(x+70,y-70), dxfattribs={"layer": "ELEC-LIGHT", "color": 2})
        dxf_text(msp, x, y-200, txt, 100)
    for (x,y,txt) in sockets:
        msp.add_lwpolyline([(x-60,y-40),(x+60,y-40),(x+60,y+40),(x-60,y+40),(x-60,y-40)],
                            close=True, dxfattribs={"layer": "ELEC-SOCKET", "color": 3})
        dxf_text(msp, x, y-150, txt, 80)
    for (x,y,txt) in switches:
        msp.add_circle((x,y), 60, dxfattribs={"layer": "ELEC-SWITCH", "color": 30})
        msp.add_line((x,y),(x+120,y+60), dxfattribs={"layer": "ELEC-SWITCH", "color": 30})
        dxf_text(msp, x, y-150, txt, 80)
    dxf_text(msp, BW//2, BH+600, f"{floor_name}电气平面图", 350)
    doc.saveas(f"{DIRS['电气']}/{filename}.dxf")


def gen_electrical():
    # 一层电气: X1=8200, Y0=2200, Y1=7200, NX1=4800, NX2=6600, MX1=12000
    f1_lights = [
        (11000,1200,"玄关筒灯"),(4000,1200,"客厅筒灯"),
        (4000,4700,"LDK主灯"),(5500,4200,"餐厅灯"),
        (2500,9000,"厨房主灯"),(5700,9000,"客卫灯"),
        (10000,4700,"主卧1主灯"),(13000,3200,"主卫1灯"),
        (10500,9000,"楼梯灯"),
    ]
    f1_sockets = [
        (800,8000,"冰箱"),(2000,10500,"油烟机16A"),(3500,10500,"微波炉"),(4200,10500,"小家电"),
        (800,10200,"净水器"),(5400,10200,"吹风机"),
        (500,3500,"电视"),(500,4200,"路由器"),
        (500,5500,"沙发USB"),(3500,5500,"沙发USB"),(7500,6500,"空调16A"),
        (8500,3500,"床头L"),(8500,4200,"USB充电L"),(11500,3500,"床头R"),(11500,4200,"USB充电R"),
        (8500,6800,"空调16A"),(13200,3800,"吹风机"),
    ]
    f1_switches = [
        (2800,7200,"厨房灯"),(5000,7200,"客卫灯"),(10500,500,"玄关"),
        (7500,2400,"客厅(门口)"),(4000,4500,"LDK(沙发)"),(5500,4500,"餐厅"),
        (8500,2800,"主卧(门口)"),(11500,2800,"主卧(床头)"),(12500,4500,"主卫"),
        (7500,7200,"楼梯↑"),
    ]
    _elec_dxf("一层", f1_lights, f1_sockets, f1_switches, "一层电气平面图")

    # 二层电气: X1=4800,Y0=1500,Y1=5200,Y2=7200,NX1=5800,NX2=8000,NX3=11200
    f2_lights = [
        (3000,8800,"主卧2主灯"),(6900,8500,"主卫2灯"),(9600,8800,"主卧3主灯"),
        (12200,7800,"公卫灯"),(2000,3500,"次卧1灯"),(7500,3500,"次卧2灯"),
        (11000,3000,"次卧2书桌灯"),
        (2000,6200,"走廊灯1"),(5000,6200,"走廊灯2"),(8000,6200,"走廊灯3"),
        (12200,9500,"楼梯灯"),(3000,800,"阳台灯1"),(7000,800,"阳台灯2"),(12000,800,"阳台灯3"),
    ]
    f2_sockets = [
        (600,8000,"床头USB L"),(600,8600,"床头L"),(4500,8000,"床头USB R"),(4500,8600,"床头R"),
        (600,10500,"空调16A"),
        (8200,8000,"床头USB L"),(10500,8000,"床头USB R"),
        (8200,8600,"床头L"),(10500,8600,"床头R"),(10500,10500,"空调16A"),
        (600,2000,"床头"),(600,2600,"USB"),(3500,2500,"书桌"),(600,4600,"空调16A"),
        (5200,2000,"床头"),(5200,2600,"USB"),(8500,2500,"书桌"),(5200,4600,"空调16A"),
        (10500,2000,"电脑"),(12000,2000,"显示器"),(13000,2000,"USB"),
        (12000,7500,"吹风机"),(6500,10000,"吹风机"),
        (5000,500,"阳台"),(9000,500,"洗衣机"),
    ]
    f2_switches = [
        (2800,7200,"主卧2(门口)"),(600,7600,"主卧2(床头)"),(8500,7200,"主卧3(门口)"),
        (10500,7600,"主卧3(床头)"),(6200,7200,"主卫2"),(11500,7200,"公卫"),
        (2000,5000,"次卧1(门口)"),(600,1800,"次卧1(床头)"),
        (5500,5000,"次卧2(门口)"),(5200,1800,"次卧2(床头)"),
        (2000,5500,"走廊(次卧侧)"),(8000,7000,"走廊(主卧侧)"),
        (11800,7200,"楼梯↓"),(3000,1700,"阳台"),
    ]
    _elec_dxf("二层", f2_lights, f2_sockets, f2_switches, "二层电气平面图")

    # 生成电气 PNG（专业电气符号 + 回路线 + 配电箱 +  room labels）
    C_WIRE = "#AAAAAA"  # 回路控制线（浅灰虚线）
    F1_ROOM_LABELS = [
        ((OW+F1_X1)/2, (OW+F1_Y0)/2, "客厅"), ((F1_X1+BW)/2, (OW+F1_Y0)/2, "玄关"),
        ((OW+F1_X1)/2, (F1_Y0+F1_Y1)/2, "LDK"), ((F1_X1+F1_MX1)/2, (F1_Y0+F1_Y1)/2, "主卧"),
        ((F1_MX1+BW)/2, (F1_Y0+F1_MY1)/2, "主卫"), ((F1_MX1+BW)/2, (F1_MY1+F1_Y1)/2, "衣帽间"),
        ((OW+F1_NX1)/2, (F1_Y1+BH)/2, "厨房"), ((F1_NX1+F1_NX2)/2, (F1_Y1+BH)/2, "客卫"),
        ((F1_NX2+BW)/2, (F1_Y1+BH)/2, "楼梯间"),
    ]
    F2_YM = F2_Y2 + IW + (BH - OW - F2_Y2 - IW) // 2  # 公卫|楼梯分界Y
    F2_ROOM_LABELS = [
        (BW/2, F2_Y0/2, "阳台"), ((OW+F2_X1)/2, (F2_Y0+F2_Y1)/2, "次卧1"), ((F2_X1+BW)/2, (F2_Y0+F2_Y1)/2, "次卧2"),
        (BW/2, (F2_Y1+F2_Y2)/2, "走廊"), ((OW+F2_NX1)/2, (F2_Y2+BH)/2, "主卧2"), ((F2_NX1+F2_NX2)/2, (F2_Y2+BH)/2, "主卫2"),
        ((F2_NX2+F2_NX3)/2, (F2_Y2+BH)/2, "主卧3"), ((F2_NX3+BW)/2, (F2_Y2+F2_YM)/2, "公卫"),
        ((F2_NX3+BW)/2, (F2_YM+BH)/2, "楼梯间"),
    ]
    def light_is_downlight(txt): return "筒灯" in txt or "射灯" in txt
    def socket_is_16a(txt): return "16A" in txt or "空调" in txt or "油烟机" in txt

    for floor_n, lights, sockets, switches, walls, fname, room_labels, db_x, db_y, circuit_pairs in [
        ("一层", f1_lights, f1_sockets, f1_switches,
         [(240,2200,7960,120),(8320,2200,BW-240-8320,120),(240,7200,BW-480,120),
          (8200,240,120,6960),(12000,2320,120,4880),(12120,4200,BW-240-12120,120),
          (4800,7320,120,BH-240-7320),(6600,7320,120,BH-240-7320)],
         "一层电气平面图", F1_ROOM_LABELS, F1_X1+IW+200, F1_Y0+IW+200,
         [(2800,7200,2500,9000),(5000,7200,5700,9000),(7500,2400,4000,1200),
          (4000,4500,4000,4700),(8500,2800,10000,4700),(12500,4500,13000,3200)]),
        ("二层", f2_lights, f2_sockets, f2_switches,
         [(240,1500,BW-480,120),(240,5200,BW-480,120),
          (240,7200,BW-480,120),(4800,1620,120,3580),
          (5800,7320,120,3440),(8000,7320,120,3440),(11200,7320,120,3440)],
         "二层电气平面图", F2_ROOM_LABELS, BW/2, F2_Y2+IW+200,
         [(2800,7200,3000,8800),(8500,7200,9600,8800),(6200,7200,6900,8500),(11500,7200,12200,7800),
          (2000,5000,2000,3500),(5500,5000,7500,3500),(2000,5505,3500,6200),(8000,7000,8000,6200),
          (11800,7200,12200,9500),(3000,1700,5000,800)]),
    ]:
        fig, ax = plt.subplots(1,1,figsize=(18,14),dpi=150,facecolor=C_BG)
        ax.set_facecolor(C_BG); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{fname}  {floor_n} Electrical Plan", fontsize=16, fontweight="bold", color=C_TEXT, pad=12)
        s = _s
        for (x,y,w,h) in [(0,0,BW,OW),(0,BH-OW,BW,OW),(0,0,OW,BH),(BW-OW,0,OW,BH)]:
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#E0E0E0",edgecolor=C_LINE,linewidth=0.3,zorder=2))
        ax.add_patch(patches.Rectangle((s(OW),s(OW)),s(BW-2*OW),s(BH-2*OW),facecolor=C_BG,edgecolor="none",zorder=1))
        for (x,y,w,h) in walls:
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#E0E0E0",edgecolor=C_LINE,linewidth=0.2,zorder=2))

        # 房间名称标注（大号浅灰字 8pt）
        for rx, ry, rname in room_labels:
            ax.text(s(rx), s(ry), rname, ha="center", va="center", fontsize=8, color="#999999", alpha=0.85, zorder=3)

        # 回路线：开关→灯具 浅灰虚线
        for sx, sy, lx, ly in circuit_pairs:
            ax.plot([s(sx), s(lx)], [s(sy), s(ly)], color=C_WIRE, linestyle="--", linewidth=0.6, alpha=0.8, zorder=4)

        # 配电箱符号
        ax.add_patch(patches.Rectangle((s(db_x)-0.08, s(db_y)-0.06), 0.16, 0.12, facecolor="#E8E8E8", edgecolor=C_LINE, linewidth=0.5, zorder=7))
        ax.text(s(db_x), s(db_y), "DB", ha="center", va="center", fontsize=6, fontweight="bold", color=C_TEXT, zorder=8)
        ax.text(s(db_x)+0.22, s(db_y)+0.02, "总进线 BV10\n照明 BV2.5\n插座 BV2.5/4", ha="left", va="top", fontsize=5, color=C_TEXT2, zorder=8)

        # 灯具：主灯⊕(空心圆+十字 r=0.15)、筒灯(实心小圆)
        for (x,y,txt) in lights:
            if light_is_downlight(txt):
                ax.add_patch(patches.Circle((s(x), s(y)), 0.08, facecolor="#FFD54F", edgecolor=C_LINE, linewidth=0.3, zorder=8))
            else:
                ax.add_patch(patches.Circle((s(x), s(y)), 0.15, facecolor="none", edgecolor="#FFC107", linewidth=0.6, zorder=8))
                ax.plot([s(x)-0.12, s(x)+0.12], [s(y), s(y)], color=C_LINE, linewidth=0.4, zorder=9)
                ax.plot([s(x), s(x)], [s(y)-0.12, s(y)+0.12], color=C_LINE, linewidth=0.4, zorder=9)
            ax.text(s(x), s(y)-0.28, txt, ha="center", va="top", fontsize=5, color=C_TEXT2, zorder=10)

        # 插座：普通10A(半圆+竖线)、专用16A(方框+16A)
        for (x,y,txt) in sockets:
            if socket_is_16a(txt):
                ax.add_patch(patches.Rectangle((s(x)-0.06, s(y)-0.05), 0.12, 0.10, facecolor="#4CAF50", edgecolor=C_LINE, linewidth=0.5, alpha=0.8, zorder=8))
                ax.text(s(x), s(y), "16A", ha="center", va="center", fontsize=4.5, fontweight="bold", color="white", zorder=9)
            else:
                ax.add_patch(patches.Arc((s(x)-0.04, s(y)), 0.08, 0.12, theta1=270, theta2=90, color=C_LINE, linewidth=0.5, zorder=8))
                ax.add_patch(patches.Arc((s(x)+0.04, s(y)), 0.08, 0.12, theta1=90, theta2=270, color=C_LINE, linewidth=0.5, zorder=8))
                ax.plot([s(x), s(x)], [s(y)-0.06, s(y)+0.06], color=C_LINE, linewidth=0.5, zorder=8)
                ax.add_patch(patches.Wedge((s(x)-0.04, s(y)), 0.06, 270, 90, facecolor="#4CAF50", edgecolor=C_LINE, linewidth=0.3, alpha=0.8, zorder=8))
            ax.text(s(x), s(y)-0.22, txt, ha="center", va="top", fontsize=5, color=C_TEXT2, zorder=10)

        # 开关：圆+斜线（单控/双控符号）
        for (x,y,txt) in switches:
            ax.add_patch(patches.Circle((s(x), s(y)), 0.08, facecolor="none", edgecolor="#FF9800", linewidth=0.6, zorder=8))
            ax.plot([s(x)-0.05, s(x)+0.08], [s(y)+0.05, s(y)-0.06], color="#FF9800", linewidth=0.5, zorder=9)
            if "床头" in txt:
                ax.plot([s(x)+0.04, s(x)+0.10], [s(y)-0.02, s(y)+0.04], color="#FF9800", linewidth=0.4, zorder=9)
            ax.text(s(x), s(y)-0.22, txt, ha="center", va="top", fontsize=5, color=C_TEXT2, zorder=10)

        # 增强图例
        lx, ly = s(BW)+1.2, s(BH)-0.2
        ax.text(lx, ly+0.5, "图例", fontsize=9, fontweight="bold", color=C_TEXT, zorder=10)
        ax.add_patch(patches.Circle((lx+0.12, ly+0.1), 0.12, facecolor="none", edgecolor="#FFC107", linewidth=0.5, zorder=8))
        ax.plot([lx+0.0, lx+0.24], [ly+0.1, ly+0.1], color=C_LINE, linewidth=0.3, zorder=9)
        ax.plot([lx+0.12, lx+0.12], [ly-0.02, ly+0.22], color=C_LINE, linewidth=0.3, zorder=9)
        ax.text(lx+0.38, ly+0.1, "吸顶灯/主灯", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.add_patch(patches.Circle((lx+0.12, ly-0.35), 0.06, facecolor="#FFD54F", edgecolor=C_LINE, linewidth=0.3, zorder=8))
        ax.text(lx+0.38, ly-0.35, "筒灯/射灯", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.add_patch(patches.Arc((lx+0.02, ly-0.78), 0.12, 0.18, theta1=270, theta2=90, color=C_LINE, linewidth=0.4, zorder=8))
        ax.add_patch(patches.Wedge((lx+0.02, ly-0.78), 0.09, 270, 90, facecolor="#4CAF50", edgecolor=C_LINE, linewidth=0.2, alpha=0.8, zorder=8))
        ax.plot([lx+0.02, lx+0.02], [ly-0.9, ly-0.66], color=C_LINE, linewidth=0.4, zorder=8)
        ax.text(lx+0.38, ly-0.78, "普通插座 10A", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.add_patch(patches.Rectangle((lx+0.04, ly-1.18), 0.14, 0.10, facecolor="#4CAF50", edgecolor=C_LINE, linewidth=0.4, zorder=8))
        ax.text(lx+0.11, ly-1.13, "16A", ha="center", va="center", fontsize=4.5, fontweight="bold", color="white", zorder=9)
        ax.text(lx+0.38, ly-1.13, "专用插座 16A", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.add_patch(patches.Circle((lx+0.12, ly-1.53), 0.08, facecolor="none", edgecolor="#FF9800", linewidth=0.5, zorder=8))
        ax.plot([lx+0.07, lx+0.20], [ly-1.47, ly-1.59], color="#FF9800", linewidth=0.4, zorder=9)
        ax.text(lx+0.38, ly-1.53, "单控开关", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.add_patch(patches.Circle((lx+0.12, ly-1.88), 0.08, facecolor="none", edgecolor="#FF9800", linewidth=0.5, zorder=8))
        ax.plot([lx+0.07, lx+0.20], [ly-1.82, ly-1.94], color="#FF9800", linewidth=0.4, zorder=9)
        ax.plot([lx+0.16, lx+0.22], [ly-1.9, ly-1.86], color="#FF9800", linewidth=0.3, zorder=9)
        ax.text(lx+0.38, ly-1.88, "双控开关", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.plot([lx+0.04, lx+0.22], [ly-2.18, ly-2.18], color=C_WIRE, linestyle="--", linewidth=0.5, zorder=8)
        ax.text(lx+0.38, ly-2.18, "回路控制线", va="center", fontsize=6, color=C_TEXT, zorder=10)
        ax.add_patch(patches.Rectangle((lx+0.04, ly-2.48), 0.16, 0.12, facecolor="#E8E8E8", edgecolor=C_LINE, linewidth=0.4, zorder=8))
        ax.text(lx+0.12, ly-2.42, "DB", ha="center", va="center", fontsize=5, fontweight="bold", color=C_TEXT, zorder=9)
        ax.text(lx+0.38, ly-2.42, "配电箱", va="center", fontsize=6, color=C_TEXT, zorder=10)
        nx, ny = -1.0, s(BH)-1.0
        ax.annotate("", xy=(nx, ny+0.7), xytext=(nx, ny), arrowprops=dict(arrowstyle="-|>", color=C_TEXT, lw=1.5), zorder=10)
        ax.text(nx, ny+0.85, "N", ha="center", va="bottom", fontsize=10, fontweight="bold", color=C_TEXT, zorder=10)
        ax.set_xlim(-2.0, s(BW)+4.5); ax.set_ylim(-1.5, s(BH)+1.5)
        fig.savefig(f"{IMG_DIR}/{fname}.png", bbox_inches="tight", pad_inches=0.3, dpi=150, facecolor=C_BG)
        plt.close(fig)
    print("  ✓ 电气图 (DXF + PNG) × 2")


# ══════════════════════════════════════════════
#  效果图（南立面渲染 + 室内俯视）
# ══════════════════════════════════════════════

def gen_render_south():
    """参考 view.jpg 风格：大面积落地窗(左) + 深色石材大门(右) + 二层阳台玻璃栏杆"""
    fig, ax = plt.subplots(1,1,figsize=(20,12),dpi=200,facecolor="#E8F0F8")
    ax.set_facecolor("#E8F0F8"); ax.set_aspect("equal"); ax.axis("off")
    for i in range(100):
        y0=TOP+0.5+i*4.0/100; y1=y0+0.04
        r=0.55+0.35*(i/100); g=0.72+0.25*(i/100); b=0.92+0.08*(i/100)
        ax.fill_between([-3,W_m+3],[y0]*2,[y1]*2,color=(r,g,b),zorder=0)
    ax.fill_between([-3,W_m+3],[-1.5,-1.5],[0,0],color="#8B9D6B",zorder=1)
    ax.fill_between([-3,W_m+3],[-0.15,-0.15],[0,0],color="#A0B07A",zorder=1)

    # 一层墙体 — 左侧浅色，右侧深色石材（参考view.jpg）
    ax.add_patch(patches.Rectangle((0,GL),8.0,F1_CL-GL,facecolor="#F5F0E8",edgecolor="none",zorder=3))
    ax.add_patch(patches.Rectangle((8.0,GL),W_m-8.0,F1_CL-GL,facecolor="#4A4038",edgecolor="none",zorder=3))
    # 二层墙体
    ax.add_patch(patches.Rectangle((0,F2_FL),W_m,F2_CL-F2_FL,facecolor="#F0EBE0",edgecolor="none",zorder=3))
    # 女儿墙
    ax.add_patch(patches.Rectangle((0,ROOF),W_m,PARAPET,facecolor="#E8E2D5",edgecolor="none",zorder=3))
    # 顶部压顶
    ax.add_patch(patches.Rectangle((-0.05,TOP-0.08),W_m+0.1,0.08,facecolor="#D0C8B8",edgecolor="#B0A898",linewidth=0.5,zorder=4))
    # 楼层分隔线
    ax.add_patch(patches.Rectangle((-0.03,F1_CL-0.05),W_m+0.06,0.2,facecolor="#D8D0C0",edgecolor="#C0B8A8",linewidth=0.5,zorder=4))
    # 外轮廓
    ax.plot([0,0,W_m,W_m],[GL,TOP,TOP,GL],color="#8A7E6E",linewidth=1.5,zorder=5)
    ax.plot([0,W_m],[GL,GL],color="#8A7E6E",linewidth=1.5,zorder=5)

    def rwin(x,y,w,h,divs=2):
        ax.add_patch(patches.Rectangle((x-0.04,y-0.04),w+0.08,h+0.08,facecolor="#6A6A6A",edgecolor="#555",linewidth=0.8,zorder=6))
        for j in range(divs):
            gx=x+j*w/divs
            for k in range(20):
                gy=y+k*h/20; t=k/20
                ax.add_patch(patches.Rectangle((gx+0.02,gy),w/divs-0.04,h/20,facecolor=(0.6+0.2*t,0.75+0.15*t,0.88+0.08*t),edgecolor="none",zorder=7))
            ax.add_patch(patches.Rectangle((gx,y),w/divs,h,facecolor="none",edgecolor="#555",linewidth=0.5,zorder=8))
        ax.plot([x,x+w],[y+h*0.45,y+h*0.45],color="#555",linewidth=0.4,zorder=8)
        ax.add_patch(patches.Rectangle((x-0.06,y-0.06),w+0.12,0.06,facecolor="#C8C0B0",edgecolor="#A8A098",linewidth=0.5,zorder=6))

    for (x, y, w, h, divs) in SOUTH_WIN:
        rwin(x, y, w, h, divs)

    # 玄关石材大门（参考view.jpg右侧深色门）
    dx,dy=9.5,F1_FL; dw,dh=1.2,2.6
    ax.add_patch(patches.Rectangle((dx-0.06,dy),dw+0.12,dh+0.1,facecolor="#3A3028",edgecolor="#2A2018",linewidth=1.2,zorder=6))
    ax.add_patch(patches.Rectangle((dx,dy),dw/2-0.02,dh,facecolor="#5A4A3A",edgecolor="#3A3028",linewidth=0.8,zorder=7))
    ax.add_patch(patches.Rectangle((dx+dw/2+0.02,dy),dw/2-0.02,dh,facecolor="#5A4A3A",edgecolor="#3A3028",linewidth=0.8,zorder=7))
    for i in range(3):
        ax.add_patch(patches.Rectangle((dx-0.3-i*0.15,dy-(i+1)*0.15),dw+0.6+i*0.3,0.15,facecolor="#4A4038",edgecolor="#3A3028",linewidth=0.5,zorder=4))

    # 二层阳台玻璃栏杆（参考view.jpg）
    ax.add_patch(patches.Rectangle((0.15,F2_FL-0.12),W_m-0.3,0.12,facecolor="#D8D0C0",edgecolor="#B0A898",linewidth=0.5,zorder=4))
    for i in range(9):
        px=0.3+i*(W_m-0.6)/8
        ax.add_patch(patches.Rectangle((px-0.025,F2_FL-1.1),0.05,1.1,facecolor="#808080",edgecolor="#606060",linewidth=0.3,zorder=5))
    for i in range(8):
        px1=0.3+i*(W_m-0.6)/8+0.04; px2=0.3+(i+1)*(W_m-0.6)/8-0.04
        ax.add_patch(patches.Rectangle((px1,F2_FL-1.1+0.08),px2-px1,0.86,facecolor="#C0D8E8",edgecolor="#90A8B8",linewidth=0.3,alpha=0.5,zorder=5))
    ax.add_patch(patches.Rectangle((0.25,F2_FL-0.06),W_m-0.5,0.06,facecolor="#707070",edgecolor="#505050",linewidth=0.5,zorder=6))

    # 景观
    def tree(cx,cy,th=1.2,cr=0.8):
        ax.add_patch(patches.Rectangle((cx-0.06,cy),0.12,th,facecolor="#8B6F47",edgecolor="#6B4F27",linewidth=0.5,zorder=2))
        for dy_t,r,c in [(0,cr,"#4A7A3A"),(cr*0.3,cr*0.85,"#5A8A4A"),(cr*0.6,cr*0.6,"#6A9A5A")]:
            ax.add_patch(patches.Ellipse((cx,cy+th+dy_t),r*2,r*1.5,facecolor=c,edgecolor="#3A6A2A",linewidth=0.3,alpha=0.85,zorder=2))
    def bush(cx,cy,w=0.8,h=0.4):
        for dx_b,r in [(-w*0.3,h*0.8),(0,h),(w*0.3,h*0.8)]:
            ax.add_patch(patches.Ellipse((cx+dx_b,cy+h*0.3),r*1.2,r,facecolor="#5A8A4A",edgecolor="#3A6A2A",linewidth=0.3,alpha=0.8,zorder=2))
    tree(-1.5,0,1.5,1.0); tree(W_m+1.5,0,1.8,1.2); tree(-0.5,-0.3,0.8,0.6)
    bush(1.0,-0.1,0.6,0.3); bush(5.0,-0.1,0.5,0.25); bush(8.0,-0.1,0.7,0.3); bush(12.0,-0.1,0.6,0.3)
    for fx in [1.0,3.5,6.0,8.5,11.0,13.0]:
        ax.add_patch(patches.Rectangle((fx-0.12,F2_FL-1.1-0.15),0.24,0.15,facecolor="#C08060",edgecolor="#A06040",linewidth=0.3,zorder=6))
        ax.add_patch(patches.Ellipse((fx,F2_FL-1.1+0.05),0.3,0.2,facecolor="#5A9A4A",edgecolor="#3A7A2A",linewidth=0.3,zorder=6))

    ax.text(W_m/2,TOP+2.5,"南立面渲染效果图",ha="center",va="center",fontsize=20,fontweight="bold",color="#4A5A6A",zorder=10)
    ax.text(W_m/2,TOP+2.0,"South Elevation Rendering  |  现代简约风格  |  14m × 11m  |  二层别墅",ha="center",va="center",fontsize=9,color="#8A8A8A",zorder=10)
    ax.set_xlim(-3,W_m+3); ax.set_ylim(-1.8,TOP+3.5)
    fig.savefig(f"{IMG_DIR}/南立面渲染效果图.png",bbox_inches="tight",pad_inches=0.2,dpi=200,facecolor="#E8F0F8")
    plt.close(fig)
    print("  ✓ 南立面渲染效果图 (PNG)")


def _interior_render(title, subtitle, floor_name, rooms, furniture, walls_h, walls_v, windows, filename):
    """通用室内俯视效果图生成器"""
    fig, ax = plt.subplots(1,1,figsize=(18,14),dpi=200,facecolor="#F5F2ED")
    ax.set_facecolor("#F5F2ED"); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=18, fontweight="bold", color="#3A3A3A", pad=8)
    ax.text(0.5, 0.97, subtitle, transform=ax.transAxes, ha="center", fontsize=9, color="#888", zorder=20)
    s = _s

    # 外墙
    for (x,y,w,h) in [(0,0,BW,OW),(0,BH-OW,BW,OW),(0,0,OW,BH),(BW-OW,0,OW,BH)]:
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#3A3A3A",edgecolor="#2A2A2A",linewidth=0.8,zorder=5))

    # 房间填充
    room_colors = {"客厅":"#D4C8B0","玄关":"#C8BCA8","客餐厅":"#D4C8B0","LDK":"#D4C8B0",
                   "厨房":"#E8E2D5","主卧":"#D4C8B0","主卫":"#E0E0E0","客卫":"#E0E0E0","公卫":"#E0E0E0",
                   "楼梯":"#C0B8A8","走廊":"#D8D0C0","次卧":"#D4C8B0","书房":"#D4C8B0",
                   "阳台":"#C8D8C0","车库":"#B8B8B8","休闲":"#D0C8B8"}
    for (x,y,w,h,name) in rooms:
        color = "#D4C8B0"
        for key, c in room_colors.items():
            if key in name:
                color = c; break
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor=color,edgecolor="none",zorder=1))

    # 内墙
    for (x,y,length) in walls_h:
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(length),s(IW),facecolor="#3A3A3A",edgecolor="#2A2A2A",linewidth=0.3,zorder=5))
    for (x,y,length) in walls_v:
        ax.add_patch(patches.Rectangle((s(x),s(y)),s(IW),s(length),facecolor="#3A3A3A",edgecolor="#2A2A2A",linewidth=0.3,zorder=5))

    # 窗户
    for (x,y,w,h,orient) in windows:
        if orient == "h":
            ax.add_patch(patches.Rectangle((s(x),s(y)-0.04),s(w),0.08,facecolor="#A8C8D8",edgecolor="#7098A8",linewidth=0.8,zorder=6))
        else:
            ax.add_patch(patches.Rectangle((s(x)-0.04,s(y)),0.08,s(h),facecolor="#A8C8D8",edgecolor="#7098A8",linewidth=0.8,zorder=6))

    # 家具
    for item in furniture:
        kind = item[0]
        if kind == "bed_d":
            x,y,w,h = item[1:5]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#E8E0D5",edgecolor="#B0A898",linewidth=0.6,zorder=4))
            ax.add_patch(patches.Rectangle((s(x+60),s(y+h-350)),s(w/2-90),s(280),facecolor="#F5F0E8",edgecolor="#C0B8A8",linewidth=0.4,zorder=4))
            ax.add_patch(patches.Rectangle((s(x+w/2+30),s(y+h-350)),s(w/2-90),s(280),facecolor="#F5F0E8",edgecolor="#C0B8A8",linewidth=0.4,zorder=4))
        elif kind == "bed_s":
            x,y,w,h = item[1:5]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#E8E0D5",edgecolor="#B0A898",linewidth=0.6,zorder=4))
            ax.add_patch(patches.Rectangle((s(x+60),s(y+h-350)),s(w-120),s(280),facecolor="#F5F0E8",edgecolor="#C0B8A8",linewidth=0.4,zorder=4))
        elif kind == "sofa":
            x,y = item[1:3]
            for (rx,ry,rw,rh) in [(x,y,2800,700),(x+50,y+50,850,580),(x+950,y+50,850,580),(x+2800,y-100,700,800)]:
                ax.add_patch(patches.Rectangle((s(rx),s(ry)),s(rw),s(rh),facecolor="#8BA87A",edgecolor="#6A8A5A",linewidth=0.5,zorder=4))
        elif kind == "tv":
            x,y,w = item[1:4]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(120),facecolor="#5A5A5A",edgecolor="#3A3A3A",linewidth=0.4,zorder=4))
        elif kind == "dining":
            cx,cy = item[1:3]
            ax.add_patch(patches.Circle((s(cx),s(cy)),s(550),facecolor="#F0E8D8",edgecolor="#C0B8A0",linewidth=0.6,zorder=4))
            for a in range(0,360,45):
                px = cx + 750*math.cos(math.radians(a)); py = cy + 750*math.sin(math.radians(a))
                ax.add_patch(patches.Circle((s(px),s(py)),s(120),facecolor="#A0A0A0",edgecolor="#808080",linewidth=0.3,zorder=4))
        elif kind == "kitchen_L":
            x,y,w,h = item[1:5]
            pts = [(s(x),s(y)),(s(x+w),s(y)),(s(x+w),s(y+550)),(s(x+550),s(y+550)),(s(x+550),s(y+h)),(s(x),s(y+h))]
            ax.add_patch(plt.Polygon(pts,facecolor="#D8D0C0",edgecolor="#A8A098",linewidth=0.5,closed=True,zorder=4))
        elif kind == "toilet":
            x,y = item[1:3]
            ax.add_patch(patches.Ellipse((s(x),s(y)),s(300),s(240),facecolor="white",edgecolor="#B0B0B0",linewidth=0.5,zorder=4))
            ax.add_patch(patches.Rectangle((s(x-170),s(y-200)),s(340),s(140),facecolor="white",edgecolor="#B0B0B0",linewidth=0.4,zorder=4))
        elif kind == "sink":
            x,y = item[1:3]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(450),s(350),facecolor="white",edgecolor="#B0B0B0",linewidth=0.4,zorder=4))
            ax.add_patch(patches.Circle((s(x+225),s(y+175)),s(70),facecolor="#D0D0D0",edgecolor="#A0A0A0",linewidth=0.3,zorder=4))
        elif kind == "shower":
            x,y,sz = item[1:4]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(sz),s(sz),facecolor="#E8E8E8",edgecolor="#B0B0B0",linewidth=0.5,zorder=4))
            ax.add_patch(patches.Circle((s(x+sz/2),s(y+sz/2)),s(160),facecolor="#D0D0D0",edgecolor="#A0A0A0",linewidth=0.4,zorder=4))
        elif kind == "stairs":
            x,y,w,h,n = item[1:6]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#C0B8A8",edgecolor="#A0A098",linewidth=0.6,zorder=4))
            step = h / n
            for i in range(1, n):
                sy2 = y + i * step
                ax.plot([s(x),s(x+w)],[s(sy2),s(sy2)],color="#A0A098",linewidth=0.3,zorder=4)
            mx = s(x + w/2)
            ax.annotate("",xy=(mx,s(y+h)-0.1),xytext=(mx,s(y)+0.1),arrowprops=dict(arrowstyle="->",color="#CC0000",lw=1),zorder=8)
        elif kind == "wardrobe":
            x,y,w,h = item[1:5]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#C8B8A0",edgecolor="#A8A088",linewidth=0.5,zorder=4))
        elif kind == "desk":
            x,y,w,h = item[1:5]
            ax.add_patch(patches.Rectangle((s(x),s(y)),s(w),s(h),facecolor="#C8B8A0",edgecolor="#A8A088",linewidth=0.5,zorder=4))
        elif kind == "door":
            x,y,r,sa,ea = item[1:6]
            ax.add_patch(Arc((s(x),s(y)),s(r)*2,s(r)*2,angle=0,theta1=sa,theta2=ea,color="#5A5A5A",linewidth=0.6,zorder=6))
        elif kind == "label":
            x,y,text = item[1:4]
            ax.text(s(x),s(y),text,ha="center",va="center",fontsize=8,fontweight="bold",color="#5A5A5A",zorder=10)
        elif kind == "light":
            x,y = item[1:3]
            ax.add_patch(patches.Circle((s(x),s(y)),0.06,facecolor="#FFD700",edgecolor="#CC9900",linewidth=0.3,alpha=0.7,zorder=8))
        elif kind == "plant":
            x,y = item[1:3]
            ax.add_patch(patches.Circle((s(x),s(y)),0.08,facecolor="#4A8A3A",edgecolor="#3A6A2A",linewidth=0.3,zorder=8))

    ax.set_xlim(-0.5, s(BW)+0.5); ax.set_ylim(-0.5, s(BH)+0.5)
    fig.savefig(f"{IMG_DIR}/{filename}.png",bbox_inches="tight",pad_inches=0.2,dpi=200,facecolor="#F5F2ED")
    plt.close(fig)


def gen_render_interior_f1():
    """一层室内俯视效果图"""
    X1=F1_X1; Y0=F1_Y0; Y1=F1_Y1; NX1=F1_NX1; NX2=F1_NX2; MX1=F1_MX1; MY1=F1_MY1

    rooms = [
        (OW, OW, X1-OW, Y0-OW, "客厅"),
        (X1+IW, OW, BW-OW-X1-IW, Y0-OW, "玄关"),
        (OW, Y0+IW, X1-OW, Y1-Y0-IW, "LDK"),
        (X1+IW, Y0+IW, MX1-X1-IW, Y1-Y0-IW, "主卧"),
        (MX1+IW, Y0+IW, BW-OW-MX1-IW, MY1-Y0-IW, "主卫"),
        (MX1+IW, MY1+IW, BW-OW-MX1-IW, Y1-MY1-IW, "衣帽间"),
        (OW, Y1+IW, NX1-OW, BH-OW-Y1-IW, "厨房"),
        (NX1+IW, Y1+IW, NX2-NX1-IW, BH-OW-Y1-IW, "客卫"),
        (NX2+IW, Y1+IW, BW-OW-NX2-IW, BH-OW-Y1-IW, "楼梯"),
    ]
    walls_h = [(OW,Y0,X1-OW),(X1+IW,Y0,BW-OW-X1-IW),(OW,Y1,BW-2*OW),
               (MX1+IW,MY1,BW-OW-MX1-IW)]
    walls_v = [(X1,OW,Y1-OW),(MX1,Y0+IW,Y1-Y0-IW),(NX1,Y1+IW,BH-OW-Y1-IW),(NX2,Y1+IW,BH-OW-Y1-IW)]
    windows = [
        (1000,0,5000,OW,"h"),
        (800,BH,2500,OW,"h"),(NX1+IW+200,BH,1000,OW,"h"),(NX2+IW+1500,BH,3500,OW,"h"),
        (0,3000,OW,3500,"v"),(0,Y1+IW+500,OW,2500,"v"),
        (BW,Y0+IW+500,OW,3500,"v"),(BW,Y1+IW+500,OW,2000,"v"),
    ]
    furniture = [
        ("sofa", 800, 3000),
        ("tv", 1000, Y0+IW+200, 2500),
        ("dining", 5500, 4800),
        ("kitchen_L", OW+100, Y1+IW+100, 4300, BH-OW-Y1-IW-200),
        ("bed_d", X1+IW+500, Y0+IW+1200, 1800, 2000),
        ("wardrobe", MX1+IW+100, MY1+IW+200, BW-OW-MX1-IW-200, 500),
        ("toilet", MX1+IW+400, Y0+IW+500),
        ("sink", MX1+IW+300, MY1-500),
        ("shower", MX1+IW+800, Y0+IW+200, 800),
        ("toilet", NX1+IW+400, Y1+IW+500),
        ("sink", NX1+IW+300, BH-OW-600),
        ("stairs", NX2+IW+400, Y1+IW+300, 2800, 3000, 14),
        ("door", X1+IW+1200, OW, 1200, 0, 90),
        ("door", 3500, Y0, 900, 270, 360),
        ("door", 2500, Y1+IW, 900, 0, 90),
        ("label", (OW+X1)/2, (OW+Y0)/2, "客厅"),
        ("label", (X1+BW)/2, (OW+Y0)/2, "玄关"),
        ("label", (OW+X1)/2, (Y0+Y1)/2, "客餐厅 LDK"),
        ("label", (X1+MX1)/2, (Y0+Y1)/2, "主卧1"),
        ("label", (MX1+BW)/2, (Y0+MY1)/2, "主卫1"),
        ("label", (MX1+BW)/2, (MY1+Y1)/2, "衣帽间"),
        ("label", (OW+NX1)/2, (Y1+BH)/2, "厨房"),
        ("label", (NX1+NX2)/2, (Y1+BH)/2, "客卫"),
        ("label", (NX2+BW)/2, (Y1+BH)/2, "楼梯间"),
        ("light", 4000, 1200), ("light", 11000, 1200),
        ("light", 4000, 4700), ("light", 5500, 4200),
        ("light", 2500, 9000), ("light", 5700, 9000), ("light", 10500, 9000),
        ("light", 10000, 4700), ("light", 13000, 3200),
        ("plant", 500, 500), ("plant", 7500, 500), ("plant", 500, 6500),
    ]
    _interior_render("一层室内俯视效果图", "Ground Floor Interior Rendering  |  实物家具渲染  |  14m × 11m",
                     "一层", rooms, furniture, walls_h, walls_v, windows, "一层室内俯视效果图")
    print("  ✓ 一层室内俯视效果图 (PNG)")


def gen_render_interior_f2():
    """二层室内俯视效果图"""
    X1=F2_X1; Y0=F2_Y0; Y1=F2_Y1; Y2=F2_Y2
    NX1=F2_NX1; NX2=F2_NX2; NX3=F2_NX3
    YM = Y2+IW+(BH-OW-Y2-IW)//2

    rooms = [
        (OW,OW,BW-2*OW,Y0-OW,"阳台"),
        (OW,Y0+IW,X1-OW,Y1-Y0-IW,"次卧"),
        (X1+IW,Y0+IW,BW-OW-X1-IW,Y1-Y0-IW,"次卧"),
        (OW,Y1+IW,BW-2*OW,Y2-Y1-IW,"走廊"),
        (OW,Y2+IW,NX1-OW,BH-OW-Y2-IW,"主卧"),
        (NX1+IW,Y2+IW,NX2-NX1-IW,BH-OW-Y2-IW,"主卫"),
        (NX2+IW,Y2+IW,NX3-NX2-IW,BH-OW-Y2-IW,"主卧"),
        (NX3+IW,Y2+IW,BW-OW-NX3-IW,(BH-OW-Y2-IW)//2,"公卫"),
        (NX3+IW,YM+IW,BW-OW-NX3-IW,(BH-OW-Y2-IW)//2-IW,"楼梯"),
    ]
    walls_h = [(OW,Y0,BW-2*OW),(OW,Y1,BW-2*OW),(OW,Y2,BW-2*OW),
               (NX3+IW,YM,BW-OW-NX3-IW)]
    walls_v = [(X1,Y0+IW,Y1-Y0-IW),(NX1,Y2+IW,BH-OW-Y2-IW),
               (NX2,Y2+IW,BH-OW-Y2-IW),(NX3,Y2+IW,BH-OW-Y2-IW)]
    windows = [
        (1000,BH,2500,OW,"h"),(NX1+300,BH,1500,OW,"h"),(NX2+500,BH,2000,OW,"h"),
        (0,8000,OW,2000,"v"),(0,Y0+500,OW,2000,"v"),
        (1200,Y0,2000,IW,"h"),(X1+500,Y0,3000,IW,"h"),(X1+4500,Y0,2000,IW,"h"),
        (BW,8500,OW,2000,"v"),(BW,Y0+500,OW,2000,"v"),
    ]
    furniture = [
        ("bed_d", 1500, 7800, 1800, 2000),
        ("wardrobe", 400, 10100, 5000, 500),
        ("toilet", NX1+IW+500, 8000),
        ("sink", NX1+IW+400, 9600),
        ("shower", NX1+IW+200, 7500, 900),
        ("bed_d", NX2+IW+400, 7800, 1800, 2000),
        ("wardrobe", NX2+IW+200, 10100, NX3-NX2-IW-400, 500),
        ("bed_s", 1200, Y0+IW+300, 1200, 2000),
        ("bed_d", X1+IW+1500, Y0+IW+300, 1800, 2000),
        ("desk", X1+IW+5500, Y0+IW+800, 1400, 550),
        ("toilet", NX3+IW+400, Y2+IW+400),
        ("sink", NX3+IW+300, YM-500),
        ("stairs", NX3+IW+200, YM+IW+200, 2200, BH-OW-YM-IW-400, 13),
        ("door", 2000, Y1, 800, 270, 360),
        ("door", X1+IW+2000, Y1, 800, 270, 360),
        ("door", 2500, Y2+IW, 900, 0, 90),
        ("door", NX2+IW+500, Y2+IW, 900, 0, 90),
        ("label", BW/2, Y0/2, "南向大阳台"),
        ("label", (OW+X1)/2, (Y0+Y1)/2, "次卧1"),
        ("label", (X1+BW)/2, (Y0+Y1)/2, "次卧2"),
        ("label", BW/2, (Y1+Y2)/2, "走廊"),
        ("label", (OW+NX1)/2, (Y2+BH)/2, "主卧2"),
        ("label", (NX1+NX2)/2, (Y2+BH)/2, "主卫2"),
        ("label", (NX2+NX3)/2, (Y2+BH)/2, "主卧3"),
        ("label", (NX3+BW)/2, (Y2+YM)/2, "公卫"),
        ("label", (NX3+BW)/2, (YM+BH)/2, "楼梯间"),
        ("light", 3000, 8800), ("light", 6900, 8500), ("light", 9600, 8800),
        ("light", 2000, 3500), ("light", 7500, 3500), ("light", 11000, 3000),
        ("light", 2000, 6200), ("light", 5000, 6200), ("light", 8000, 6200),
        ("light", 12200, 7800), ("light", 12200, 9500),
        ("light", 3000, 800), ("light", 7000, 800), ("light", 12000, 800),
        ("plant", 500, 500), ("plant", 7000, 500), ("plant", 13000, 500),
    ]
    _interior_render("二层室内俯视效果图", "Second Floor Interior Rendering  |  实物家具渲染  |  14m × 11m",
                     "二层", rooms, furniture, walls_h, walls_v, windows, "二层室内俯视效果图")
    print("  ✓ 二层室内俯视效果图 (PNG)")


def gen_render():
    gen_render_south()
    gen_render_interior_f1()
    gen_render_interior_f2()


# ══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  两层轻奢别墅 — 全套图纸生成")
    print("  输出目录：图纸/")
    print("=" * 60)

    print("\n📐 01-建筑设计")
    gen_floor1()
    gen_floor2()
    gen_elevations()
    gen_section()
    gen_roof()

    print("\n🚿 02-给排水设计")
    gen_plumbing()

    print("\n⚡ 03-电气设计")
    gen_electrical()

    print("\n🎨 04-效果图")
    gen_render()

    print("\n" + "=" * 60)
    print("  全部完成！")
    print("=" * 60)

    # 打印目录结构
    print("\n📁 图纸目录结构：")
    for root, dirs, files in sorted(os.walk(BASE)):
        level = root.replace(BASE, "").count(os.sep)
        indent = "  " * level
        folder = os.path.basename(root)
        print(f"  {indent}{folder}/")
        for f in sorted(files):
            print(f"  {indent}  {f}")
