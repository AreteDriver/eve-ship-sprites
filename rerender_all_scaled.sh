#!/bin/bash
# Re-render ALL ships with proper size scaling
# This rebuilds the entire sprite collection with relative ship sizes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

STL_BASE="EvE-3D-Printing/ships"
RENDER_SCRIPT="render_ship.py"

# Check Blender
if ! command -v blender &> /dev/null; then
    echo "Error: Blender not found"
    exit 1
fi

# Find all STL files
STLS=$(find "$STL_BASE" -name "*.stl" -type f | sort)
TOTAL=$(echo "$STLS" | wc -l)

echo "=== Re-rendering $TOTAL ships with size scaling ==="
echo ""

SUCCESS=0
FAILED=0

echo "$STLS" | while IFS= read -r stl_path; do
    # Convert STL path to PNG path
    # e.g., EvE-3D-Printing/ships/minmatar/frigate/rifter.stl -> minmatar/frigate/rifter.png
    relative_path="${stl_path#$STL_BASE/}"
    png_path="${relative_path%.stl}.png"

    # Create output directory if needed
    mkdir -p "$(dirname "$png_path")"

    echo -n "[$((SUCCESS + FAILED + 1))/$TOTAL] $png_path... "

    # Render with Blender
    if timeout 180 blender --background --python "$RENDER_SCRIPT" -- "$stl_path" "$png_path" 512 > /tmp/render.log 2>&1; then
        if [ -f "$png_path" ] && [ -s "$png_path" ]; then
            echo "OK"
            SUCCESS=$((SUCCESS + 1))
        else
            echo "FAILED (no output)"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "FAILED (blender error)"
        cat /tmp/render.log | tail -5
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=== Summary ==="
echo "Success: $SUCCESS"
echo "Failed: $FAILED"
echo "Total: $TOTAL"
