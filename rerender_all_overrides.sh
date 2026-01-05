#!/bin/bash
# Re-render all ships with orientation overrides
# Extracts ship paths from ship_orientations.json and re-renders them

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

STL_BASE="EvE-3D-Printing/ships"
RENDER_SCRIPT="render_ship.py"

# Check Blender
if ! command -v blender &> /dev/null; then
    echo "Error: Blender not found"
    exit 1
fi

# Extract ship paths from JSON (skip comment lines)
SHIPS=$(python3 -c "
import json
with open('ship_orientations.json') as f:
    data = json.load(f)
ships = [k for k in data.keys() if not k.startswith('_')]
for s in ships:
    print(s)
")

TOTAL=$(echo "$SHIPS" | wc -l)
echo "=== Re-rendering $TOTAL ships with overrides ==="
echo ""

SUCCESS=0
FAILED=0
SKIPPED=0

echo "$SHIPS" | while IFS= read -r ship; do
    stl_path="$STL_BASE/$ship.stl"
    png_path="$ship.png"

    # Create output directory if needed
    mkdir -p "$(dirname "$png_path")"

    if [ ! -f "$stl_path" ]; then
        echo "SKIP: $ship (no STL)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo -n "Rendering $ship... "

    # Render with Blender (capture output)
    if timeout 120 blender --background --python "$RENDER_SCRIPT" -- "$stl_path" "$png_path" 512 > /tmp/render.log 2>&1; then
        if [ -f "$png_path" ] && [ -s "$png_path" ]; then
            # Check file size > 10KB (not blank)
            size=$(stat -f%z "$png_path" 2>/dev/null || stat -c%s "$png_path" 2>/dev/null)
            if [ "$size" -gt 10000 ]; then
                echo "OK"
                SUCCESS=$((SUCCESS + 1))
            else
                echo "WARN (small: ${size}b)"
                SUCCESS=$((SUCCESS + 1))
            fi
        else
            echo "FAILED (no output)"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "FAILED (blender error)"
        ((FAILED++))
    fi
done

echo ""
echo "=== Summary ==="
echo "Success: $SUCCESS"
echo "Failed: $FAILED"
echo "Skipped: $SKIPPED"
echo "Total: $TOTAL"
