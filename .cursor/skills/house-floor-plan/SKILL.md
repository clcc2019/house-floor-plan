---
name: house-floor-plan
description: Generates residential floor plans and full drawing sets (DXF + PNG + 3D renderings) for self-built houses and villas. Enforces strict cross-drawing consistency through a centralized building config. Use when the user mentions floor plans, house design, building layout, DXF drawings, room layout optimization, self-built house blueprints, or residential architecture drawings.
---

# House Floor Plan Generator

Generate professional residential floor plans as DXF (AutoCAD) + PNG (preview) + 3D renderings.

## Architecture: Single Source of Truth

All scripts share one centralized config to guarantee cross-drawing consistency:

```
scripts/building_config.py    ← 唯一数据源 (Single Source of Truth)
  ├── 基地尺寸 (BW/BH/OW/IW)
  ├── 层高体系 (F1H/F2H/SLAB/PARAPET → 推导 GL/F1_FL/.../TOP)
  ├── 平面布局 (F1_X1/F1_Y0/.../F2_NX3 — 每层房间分割坐标)
  ├── 窗户定义 (SOUTH_WIN/NORTH_WIN/EAST_WIN/WEST_WIN — 全朝向统一)
  └── 立面参数 (DARK_STONE_X/SOUTH_DOOR — 外观特征)

scripts/fonts/                ← 内嵌中文字体 (Noto Sans SC 子集, ~530KB, 无需系统字体)
scripts/generate_all.py       ← 全套图纸 (从 building_config 导入)
scripts/generate_render_3d.py ← 3D透视渲染 (从 building_config 导入)
```

**核心原则**：修改建筑参数时，只改 `building_config.py` 一处，所有图纸自动同步。禁止在各脚本中硬编码建筑尺寸。

## Quick Start

```bash
pip install -r requirements.txt
```

**Utility scripts** (execute, don't read):

| Script | Purpose |
|--------|---------|
| `scripts/building_config.py` | Centralized building parameters (edit this to change dimensions) |
| `scripts/generate_all.py` | Generate full drawing set (floor plans, elevations, sections, MEP, renderings) |
| `scripts/generate_render_3d.py` | Generate 3D perspective renderings |
| `examples/generate_house_dxf.py` | Standalone floor plan example (DXF + PNG) |

```bash
python scripts/generate_all.py       # DXF → ./图纸/  PNG → ./docs/images/
python scripts/generate_render_3d.py  # PNG → ./docs/images/
```

## Consistency Rules

When modifying any drawing, follow these rules to maintain cross-drawing consistency:

1. **Window positions** — Defined once in `building_config.py` as `SOUTH_WIN/NORTH_WIN/EAST_WIN/WEST_WIN`. All scripts (elevations, renderings, 3D) read from the same arrays.
2. **Floor heights** — Derived chain: `GL → F1_FL → F1_CL → F2_FL → F2_CL → ROOF → TOP`. Never hardcode intermediate values.
3. **Room layout** — Floor plan partition coordinates (`F1_X1`, `F2_NX3`, etc.) are defined in config. Both `generate_all.py` and 3D renderings import the same values.
4. **No phantom volumes** — The building is a flat-roof box (ROOF + PARAPET). No raised roof volumes, attics, or mezzanines unless explicitly added to config.
5. **East ≠ West** — East and west facades have different window layouts because the underlying rooms differ. Never mirror one side to the other.

## Design Principles

1. **South-facing orientation** — living spaces face south for light and ventilation
2. **Public-private separation** — LDK (living+dining+kitchen) open plan; bedrooms isolated
3. **Wet-dry separation** — bathrooms with separated wash/toilet/shower zones
4. **Every room has a door** — verify all rooms have proper entry/exit with correct swing direction
5. **Elderly room on ground floor** — south-facing with en-suite, easy access
6. **Stairs alignment** — upper/lower floor stairwells must occupy the same XY footprint

## Workflow

```
- [ ] Step 1: Confirm requirements (occupants, bedrooms, plot size, floors, style)
- [ ] Step 2: Zone allocation (ground: public + elderly; upper: private)
- [ ] Step 3: Update building_config.py (walls, rooms, windows)
- [ ] Step 4: Door & window placement (verify every room has access)
- [ ] Step 5: Furniture layout (per reference.md standard sizes)
- [ ] Step 6: Circulation check (no dead-end rooms)
- [ ] Step 7: Dimension annotation (segmented + total)
- [ ] Step 8: Run generate_all.py + generate_render_3d.py
- [ ] Step 9: Cross-drawing validation (see checklist below)
```

## Validation Checklist

```
Functional:
- [ ] Every room has at least one door with correct swing direction
- [ ] Master bedrooms have en-suite bathroom doors
- [ ] Stairwell position matches between floors
- [ ] Kitchen is adjacent to dining area
- [ ] Corridor width ≥ 1.2m throughout

Cross-drawing consistency:
- [ ] Elevation windows match floor plan window_h/window_v positions
- [ ] 3D renderings match elevation window layout exactly
- [ ] No phantom roof volumes or extra building mass in renderings
- [ ] East and west elevations reflect actual room differences
- [ ] Section shows correct slab/parapet/stair positions
- [ ] Building height (TOP) is identical across all drawings
```

## Drawing Specification

- **Exterior wall**: 240mm (`lineweight=50`), **Interior**: 120mm (`lineweight=35`)
- **Room label**: Chinese name (bold) + English name (gray) + dimensions (gray), centered
- **Dimensions**: exterior segmented (-700mm offset) + total (-1400mm offset)
- **Export**: DXF (AutoCAD R2010, mm units) + PNG (150dpi, 效果图200dpi)
- **CJK Font**: 内嵌子集字体 `fonts/NotoSansSC-Subset.ttf` (265KB) + Bold (266KB)，无需依赖系统字体

## Drawing Quality Standards

### MEP (Mechanical, Electrical, Plumbing) Drawings
Electrical plans must include:
- Distribution box (DB) with BV cable specifications (BV10/BV2.5/BV4)
- Circuit control lines (switch → light dashed connections)
- Standard symbols: ⊕ ceiling light, ● downlight, ▶ 10A outlet, □ 16A outlet
- Room name labels matching floor plan positions

Plumbing plans must include:
- Pipe diameter annotations on lines (DN20/DN50/DN110)
- Riser IDs (JL-1/WL-1) at vertical pipe locations
- Valve symbols (butterfly ▷◁) at branch points
- Water meter symbol (◇W) at building entry

### Rendering Quality
Elevation renderings include:
- Multi-layer sky gradient with clouds
- Lawn stripe texture, walkway, ground shadow
- Wall surface gradient (top-light to bottom-dark)
- Glass reflection (sky blue → green ground reflection)
- Stone cladding texture with horizontal joint lines
- Multi-layer tree canopies and landscaping details

3D perspective renderings include:
- Glass horizontal highlight band
- Multi-layer tree crowns (5-layer overlay)
- Grass stripe texture
- Building shadow projection on ground

## Additional Resources

- [reference.md](reference.md) — Building code (GB 55031-2022), room area guidelines, color scheme, furniture sizes
- [examples/generate_house_dxf.py](examples/generate_house_dxf.py) — Standalone single-floor example
