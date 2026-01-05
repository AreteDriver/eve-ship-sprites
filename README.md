# EVE Ship Sprites

Top-down ship sprites rendered from EVE Online 3D models for use in 2D games.

## Features

- **330+ ships** from all factions (Amarr, Caldari, Gallente, Minmatar, Pirate, etc.)
- **Size-scaled sprites** - frigates appear small, titans appear large
- **Proper top-down orientation** - all ships show deck view with nose pointing up
- **Sprite sheets** with JSON metadata for game engine integration

## Directory Structure

```
eve-ship-sprites/
├── amarr/              # Amarr faction sprites
├── caldari/            # Caldari faction sprites
├── gallente/           # Gallente faction sprites
├── minmatar/           # Minmatar faction sprites
├── pirate/             # Pirate faction sprites
├── sheets/             # Consolidated sprite sheets + JSON
├── audit_sheets/       # Visual audit grids per faction
├── ship_orientations.json   # Orientation overrides
├── ship_sizes.json          # Ship sizes in meters
└── render_ship.py           # Blender render script
```

## Size Scaling

Ships are scaled proportionally based on their in-game dimensions:

| Class | Size (meters) | Fill Ratio |
|-------|---------------|------------|
| Frigate | 60-80 | 12% |
| Cruiser | 280-380 | 21% |
| Battleship | 800-1100 | 33% |
| Capital | 1500-2800 | 50% |
| Titan | 13000-15000 | 100% |

The scaling uses a power curve (exponent 0.4) to compress the 186:1 size range into a visually balanced 8:1 range.

## Orientation System

Ships are automatically oriented for top-down view (camera looking down Z-axis). For ships with unusual model orientation, `ship_orientations.json` provides overrides:

```json
{
  "minmatar/battleship/tempest": {"rx": -90},
  "amarr/capital/aeon": {"scale": 1.5},
  "caldari/frigate/buzzard": {"rx": 90, "ry": 0, "rz": 0}
}
```

Options:
- `axis`: Set which axis points "up" (`x`, `y`, or `z`)
- `flip`: Rotate 180° around up axis
- `rx`, `ry`, `rz`: Explicit Euler angles in degrees
- `scale`: Camera margin multiplier (for large ships)

## Scripts

### render_ship.py

Render a single ship sprite using Blender:

```bash
blender --background --python render_ship.py -- input.stl output.png [size]
```

### generate_spritesheets.sh

Generate consolidated sprite sheets per faction:

```bash
./generate_spritesheets.sh
```

Output: `sheets/<faction>.png` + `sheets/<faction>.json`

### prepare_for_rebellion.sh

Copy sprites to EVE_Rebellion game project:

```bash
./prepare_for_rebellion.sh
```

## Sprite Sheet JSON Format

```json
{
  "sprite_size": 512,
  "columns": 8,
  "rows": 9,
  "sprites": {
    "battleship/tempest": {"x": 0, "y": 0, "w": 512, "h": 512},
    "cruiser/rupture": {"x": 512, "y": 0, "w": 512, "h": 512}
  }
}
```

## Requirements

- Blender 3.0+ (for render_ship.py)
- ImageMagick (for sprite sheet generation)
- Python 3.8+

## License

Ship models from [EvE-3D-Printing](https://github.com/nicti/EvE-3D-Printing) project.

EVE Online and all related assets are property of CCP Games.
