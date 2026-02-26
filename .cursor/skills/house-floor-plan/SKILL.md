---
name: house-floor-plan
description: Generates residential floor plans (DXF + PNG) for self-built houses and villas. Use when the user mentions floor plans, house design, building layout, DXF drawings, room layout optimization, or self-built house blueprints.
---

# House Floor Plan Generator

## Quick Start

Generate floor plans using `ezdxf` (DXF) + `matplotlib` (PNG preview):

```bash
pip install ezdxf matplotlib Pillow
```

## Design Principles

1. **South-facing orientation** — living spaces face south for light and ventilation
2. **Public-private separation** — LDK (living+dining+kitchen) open plan; bedrooms isolated
3. **Wet-dry separation** — bathrooms with separated wash/toilet/shower zones
4. **Every room has a door** — verify all rooms have proper entry/exit doors with correct swing direction
5. **Elderly room on ground floor** — south-facing with en-suite, easy access
6. **Stairs alignment** — upper/lower floor stairwells must occupy the same XY footprint

## Building Code Reference (GB 55031-2022)

| Parameter | Min | Recommended |
|-----------|-----|-------------|
| Floor height | ≥2.80m | 3.0~3.3m |
| Interior clear height | ≥2.40m | 2.7~2.9m |
| Stair width | ≥1.10m | 1.2~1.5m |
| Stair tread/riser | ≥260mm / ≤175mm | 280mm / 165mm |
| Corridor width | ≥1.20m | 1.5m |
| Entry door | ≥1.0m×2.0m | 1.2m×2.4m |
| Bedroom door | ≥0.9m | 0.9m×2.1m |
| Bathroom door | ≥0.8m | 0.8m×2.1m |

## Room Area Guidelines

| Room | Min | Comfortable | Notes |
|------|-----|-------------|-------|
| Master bedroom | 12㎡ | 16~22㎡ | Excluding en-suite |
| Secondary bedroom | 8㎡ | 10~14㎡ | |
| Living room | 15㎡ | 25~40㎡ | Open plan preferred |
| Kitchen | 5㎡ | 8~12㎡ | L/U-shaped counter |
| Bathroom | 3㎡ | 4~6㎡ | Wet-dry separated |
| Study | 6㎡ | 8~12㎡ | Can double as guest room |

## Drawing Specification

### Color Scheme

| Element | HEX | DXF ACI | zorder |
|---------|-----|---------|--------|
| Background | `#FFFFFF` | — | — |
| Room fill | `#D6E8F0` | 150 | 1 |
| Walls | `#1A1A1A` | 250 | 5 |
| Furniture | `#333333` | 8 | 4 |
| Text (CN) | `#1A1A1A` | 250 | 10 |
| Text (EN/dim) | `#666666` | 8 | 10 |
| Dimensions | `#CC0000` | 1 | 8 |
| Windows | `#4A90D9` | 4 | 6 |
| Doors | `#333333` | 250 | 6 |
| Stairs | `#888888` | 8 | 4 |

### Wall Thickness
- **Exterior**: 240mm (lineweight=50)
- **Interior**: 120mm (lineweight=35)

### Annotation Rules
- Room label: Chinese name (bold) + English name (gray) + dimensions (gray), centered
- Dimensions: exterior, segmented (-700mm) + total (-1400mm)
- Info block: right side with floor/size/area/style
- North arrow: top-left corner

### Furniture Standard Sizes

| Item | Size (mm) | Drawing |
|------|-----------|---------|
| Double bed | 1800×2000 | Rectangle + pillow zone |
| Single bed | 1200×2000 | Rectangle + pillow zone |
| L-sofa | 2800×700+700×800 | Composite rectangles |
| Round dining table | R550 + 8×R120 chairs | Circle + small circles |
| Desk + chair | 1400×600 + R180 | Rectangle + circle |
| Wardrobe | wall-width × 550 deep | Rectangle + center line |
| Toilet | 300×240 ellipse + tank | Ellipse + rectangle |
| Sink | 450×350 | Rectangle + circle |
| Shower | 900×900 | Square + circle |

## Workflow

1. **Confirm requirements** — occupants, bedrooms, plot size, floors, orientation
2. **Zone allocation** — assign functions per floor
3. **Wall layout** — define structural grid with outer/inner walls
4. **Door placement** — **every room must have a door** with correct swing
5. **Window placement** — based on orientation and ventilation needs
6. **Furniture layout** — place per standard sizes, verify clearance
7. **Circulation check** — simulate daily paths, ensure no dead ends
8. **Dimension annotation** — all key dimensions on exterior
9. **Cross-drawing sync** — update elevations, sections, MEP, renderings to match floor plan changes
10. **Export** — DXF (AutoCAD R2010, mm units) + PNG (150dpi)

## Critical Checklist

Before finalizing any floor plan, verify:

- [ ] Every room has at least one door with correct swing direction
- [ ] Master bedrooms have en-suite bathroom doors
- [ ] Stairwell position matches between floors
- [ ] No room is a dead end (accessible only through another private room)
- [ ] Kitchen is adjacent to dining area
- [ ] Guest WC is not on the front facade
- [ ] All windows provide adequate ventilation (especially bathrooms)
- [ ] Corridor width ≥ 1.2m throughout
- [ ] Room dimensions meet minimum area requirements

## Reference Implementation

Complete working example: [generate_house_dxf.py](examples/generate_house_dxf.py)

For the full project with all drawing types (floor plans, elevations, sections, MEP, 3D renderings), see the repository root `generate_all.py`.
