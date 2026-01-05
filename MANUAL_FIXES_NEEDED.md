# Ships Needing Manual STL Rotation in Blender

These ships have orientation issues that can't be fixed with simple axis rotation overrides.
They require manual inspection and rotation in Blender for proper top-down rendering.

## Priority 1: Completely Wrong Orientation (Front/Side View)

These ships are rendered from the wrong angle entirely:

| Ship | Path | Issue |
|------|------|-------|
| Iteron Mark V | gallente/industrial/iteron mark v.png | Front view, need 90° rotation |
| Naglfar | minmatar/capital/naglfar.png | Edge-on, need different axis |
| Ragnarok | minmatar/capital/ragnarok.png | Edge-on view |
| Vargur | minmatar/battleship/vargur.png | Side/front view |
| Vagabond | minmatar/cruiser/vagabond.png | Side view |
| Tornado | minmatar/battlecruiser/tornado.png | Edge-on |
| Epithal | gallente/industrial/epithal.png | Front view |
| Iteron III | gallente/industrial/iteron iii_old.png | Front view |

## Priority 2: Edge-On / Low Fill (Very Thin Profile)

These render but barely fill the frame - likely wrong rotation:

| Ship | Path | Fill % |
|------|------|--------|
| Zephyr | special_edition/zephyr.png | 7.6% |
| Pacifier | concord/frigate/pacifier.png | 7.9% |
| Buzzard | caldari/frigate/buzzard.png | 9.1% |
| Heron | caldari/frigate/heron.png | 9.1% |
| Apotheosis | pirate/soct/apotheosis.png | 10.8% |
| Sunesis | pirate/soct/sunesis.png | 12.7% |
| Gnosis | pirate/soct/gnosis.png | 12.8% |
| Jackdaw | caldari/destroyer/jackdaw.png | 14.2% |

## Priority 3: Nose Direction Issues

These may have nose pointing wrong direction (check and flip if needed):

| Ship | Path | Issue |
|------|------|-------|
| Slasher | minmatar/frigate/slasher.png | Balance=0.15 (mass at bottom) |
| Mantis | caldari/fighter/mantis.png | Balance=0.18 |
| Maelstrom | minmatar/battleship/maelstorm.png | Balance=0.26 |
| Buzzard | caldari/frigate/buzzard.png | Balance=0.28 |
| Widow | caldari/battleship/widow.png | Balance=0.29 |
| Scorpion | caldari/battleship/scorpion.png | Balance=0.29 |
| Breacher | minmatar/frigate/breacher.png | Balance=0.35 |

## Priority 4: Too Small in Frame

These ships render too small - scale issue:

| Ship | Path | Max Dimension |
|------|------|---------------|
| Praxis | pirate/soct/praxis.png | 125px |
| Minokawa | caldari/capital/minokawa.png | 138px |

## How to Fix

1. Open Blender
2. Import the STL: `File > Import > STL`
3. Rotate to proper top-down orientation:
   - Camera should look down -Z axis
   - Ship nose should point +Y (up in render)
   - Ship width should be along X axis
4. Export rotated STL or note the euler angles needed
5. Add override to `ship_orientations.json`:
   ```json
   "faction/class/ship": {"rx": 90, "ry": 0, "rz": 45}
   ```
6. Re-render with `render_ship.py`

## Estimated Work

- ~20 ships need manual inspection
- ~10 ships need significant rotation fixes
- ~5 ships may have fundamentally broken STL models
