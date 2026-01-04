#!/bin/bash
# Re-render ships with fixed orientation overrides
# Run from eve-ship-sprites directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STL_BASE="$SCRIPT_DIR/EvE-3D-Printing/ships"
RENDER_SCRIPT="$SCRIPT_DIR/render_ship.py"

# Check Blender
if ! command -v blender &> /dev/null; then
    echo "Error: Blender not found. Install with: sudo apt install blender"
    exit 1
fi

# Ships to re-render (from orientation audit)
SHIPS=(
    # Minmatar frigates (nose flip)
    "minmatar/frigate/rifter"
    "minmatar/frigate/breacher"
    "minmatar/frigate/vigil"
    "minmatar/frigate/slasher"

    # Minmatar battleships (explicit rotation)
    "minmatar/battleship/tempest"
    "minmatar/battleship/maelstorm"

    # Minmatar capitals (broken/blank)
    "minmatar/capital/lif"

    # Amarr capitals (broken/blank or wrong orientation)
    "amarr/capital/avatar"
    "amarr/capital/avatar_old"
    "amarr/capital/apostle"
    "amarr/capital/aeon"

    # Pirate (side view)
    "pirate/sanshas nation/nightmare_final"

    # SOE (nose flip)
    "pirate/soe/astero"

    # Triglavian (broken)
    "triglavian/zirnitra"
)

echo "Re-rendering ${#SHIPS[@]} ships with fixed orientations..."
echo ""

SUCCESS=0
FAILED=0

for ship in "${SHIPS[@]}"; do
    stl_path="$STL_BASE/$ship.stl"
    png_path="$SCRIPT_DIR/$ship.png"

    # Create output directory if needed
    mkdir -p "$(dirname "$png_path")"

    if [ ! -f "$stl_path" ]; then
        echo "SKIP: $ship (STL not found)"
        continue
    fi

    echo -n "Rendering $ship... "

    # Remove old PNG
    rm -f "$png_path"

    # Render with Blender
    if blender --background --python "$RENDER_SCRIPT" -- "$stl_path" "$png_path" 512 2>&1 | tail -5; then
        if [ -f "$png_path" ] && [ -s "$png_path" ]; then
            echo "OK"
            ((SUCCESS++))
        else
            echo "FAILED (empty output)"
            ((FAILED++))
        fi
    else
        echo "FAILED"
        ((FAILED++))
    fi
done

echo ""
echo "=== Summary ==="
echo "Success: $SUCCESS"
echo "Failed: $FAILED"
