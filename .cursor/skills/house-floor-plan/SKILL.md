---
name: house-floor-plan
description: Generates residential floor plans (DXF + PNG) for self-built houses and villas using ezdxf and matplotlib. Use when the user mentions floor plans, house design, building layout, DXF drawings, room layout optimization, self-built house blueprints, or residential architecture drawings.
---

# House Floor Plan Generator

Generate professional residential floor plans as DXF (AutoCAD) + PNG (preview) files.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate floor plans using `ezdxf` for DXF output and `matplotlib` for PNG preview.

**Utility scripts** (execute, don't read):

| Script | Purpose |
|--------|---------|
| `scripts/generate_all.py` | Generate full drawing set (floor plans, elevations, sections, MEP, renderings) |
| `scripts/generate_render_3d.py` | Generate 3D perspective renderings |
| `examples/generate_house_dxf.py` | Standalone floor plan example (DXF + PNG) |

```bash
python scripts/generate_all.py     # outputs to ./图纸/
python scripts/generate_render_3d.py
python examples/generate_house_dxf.py
```

## Design Principles

1. **South-facing orientation** — living spaces face south for light and ventilation
2. **Public-private separation** — LDK (living+dining+kitchen) open plan; bedrooms isolated
3. **Wet-dry separation** — bathrooms with separated wash/toilet/shower zones
4. **Every room has a door** — verify all rooms have proper entry/exit with correct swing direction
5. **Elderly room on ground floor** — south-facing with en-suite, easy access
6. **Stairs alignment** — upper/lower floor stairwells must occupy the same XY footprint

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Confirm requirements
- [ ] Step 2: Zone allocation
- [ ] Step 3: Wall layout
- [ ] Step 4: Door placement
- [ ] Step 5: Window placement
- [ ] Step 6: Furniture layout
- [ ] Step 7: Circulation check
- [ ] Step 8: Dimension annotation
- [ ] Step 9: Cross-drawing sync
- [ ] Step 10: Export & validate
```

**Step 1: Confirm requirements**
Gather: occupants, bedroom count, plot size (m), floors, orientation, style preference.

**Step 2: Zone allocation**
Assign functions per floor. Ground floor: public areas + elderly room. Upper floors: private bedrooms.

**Step 3: Wall layout**
Define structural grid. Exterior walls: 240mm. Interior walls: 120mm.

**Step 4: Door placement**
Every room must have a door with correct swing direction. Master bedrooms require en-suite bathroom doors.

**Step 5: Window placement**
Place windows based on orientation and ventilation needs. Bathrooms require ventilation windows.

**Step 6: Furniture layout**
Place per standard sizes from [reference.md](reference.md). Verify clearance paths.

**Step 7: Circulation check**
Simulate daily movement paths. Ensure no dead ends (rooms accessible only through another private room).

**Step 8: Dimension annotation**
Add exterior dimensions: segmented at -700mm offset, total at -1400mm offset.

**Step 9: Cross-drawing sync**
Update elevations, sections, MEP, and renderings to match any floor plan changes.

**Step 10: Export & validate**
Export DXF (AutoCAD R2010, mm units) + PNG (150dpi). Run the validation checklist below.

## Validation Checklist

Before finalizing any floor plan, verify:

```
Validation:
- [ ] Every room has at least one door with correct swing direction
- [ ] Master bedrooms have en-suite bathroom doors
- [ ] Stairwell position matches between floors
- [ ] No dead-end rooms (accessible only through another private room)
- [ ] Kitchen is adjacent to dining area
- [ ] Guest WC is not on the front facade
- [ ] All windows provide adequate ventilation (especially bathrooms)
- [ ] Corridor width ≥ 1.2m throughout
- [ ] Room dimensions meet minimum area requirements
- [ ] All dimension annotations are present
```

## Drawing Specification (Quick Reference)

### Wall Thickness
- **Exterior**: 240mm (`lineweight=50`)
- **Interior**: 120mm (`lineweight=35`)

### Annotation Rules
- Room label: Chinese name (bold) + English name (gray) + dimensions (gray), centered
- Dimensions: exterior segmented (-700mm offset) + total (-1400mm offset)
- Info block: right side with floor/size/area/style
- North arrow: top-left corner

## Additional Resources

- For building code reference (GB 55031-2022), room area guidelines, color scheme, and furniture standard sizes, see [reference.md](reference.md)
- For a complete working example (single floor plan), see [examples/generate_house_dxf.py](examples/generate_house_dxf.py)
- For the full drawing set generator, see [scripts/generate_all.py](scripts/generate_all.py)
- For 3D rendering, see [scripts/generate_render_3d.py](scripts/generate_render_3d.py)
