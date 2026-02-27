# House Floor Plan — Reference

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

## Color Scheme

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

## Furniture Standard Sizes

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
| Bathtub | 750×1600 | Rectangle + inner ellipse |

## DXF Layer Setup

| Layer | ACI Color | Purpose |
|-------|-----------|---------|
| WALL | 250 (black) | Wall outlines |
| WALL-FILL | 250 (black) | Filled wall hatches |
| ROOM-FILL | 150 (light blue) | Room area fills |
| DOOR | 250 (black) | Door arcs |
| WINDOW | 250 (black) | Window markers |
| STAIRS | 8 (gray) | Staircase elements |
| TEXT | 250 (black) | Room labels |
| DIM | 1 (red) | Dimension annotations |
| FIXTURE | 8 (gray) | Bathroom fixtures |
| FURNITURE | 8 (gray) | Furniture outlines |
| TITLE | 250 (black) | Title block |
| INFO | 250 (black) | Info block |
