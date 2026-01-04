#!/bin/bash
#
# generate_spritesheets.sh - Generate sprite sheets from individual ship sprites
#
# Creates one sprite sheet per faction with accompanying JSON metadata
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPRITES_DIR="$SCRIPT_DIR"
OUTPUT_DIR="$SCRIPT_DIR/sheets"
SPRITE_SIZE=512
PADDING=0

mkdir -p "$OUTPUT_DIR"

echo "=== Generating Sprite Sheets by Faction ==="
echo ""

for faction_dir in "$SPRITES_DIR"/*/; do
    # Skip non-faction directories
    [[ "$faction_dir" == *"/sheets/"* ]] && continue
    [[ "$faction_dir" == *"/audit_sheets/"* ]] && continue
    [[ "$faction_dir" == *"/EvE-3D-Printing/"* ]] && continue

    faction=$(basename "$faction_dir")

    # Find all PNGs in this faction (recursively)
    mapfile -t sprites < <(find "$faction_dir" -name "*.png" -type f | sort)
    count=${#sprites[@]}

    if [ $count -eq 0 ]; then
        echo "[$faction] No sprites found, skipping"
        continue
    fi

    echo "[$faction] Found $count sprites"

    # Calculate grid size (roughly square)
    cols=$(echo "sqrt($count)" | bc)
    [ $cols -lt 1 ] && cols=1
    rows=$(( (count + cols - 1) / cols ))

    # Adjust to make it more square
    while [ $((cols * rows)) -lt $count ]; do
        rows=$((rows + 1))
    done

    sheet_width=$((cols * SPRITE_SIZE))
    sheet_height=$((rows * SPRITE_SIZE))

    echo "  Grid: ${cols}x${rows} = ${sheet_width}x${sheet_height}px"

    # Generate sprite sheet
    output_png="$OUTPUT_DIR/${faction}.png"
    montage "${sprites[@]}" \
        -tile "${cols}x${rows}" \
        -geometry "${SPRITE_SIZE}x${SPRITE_SIZE}+${PADDING}+${PADDING}" \
        -background transparent \
        "$output_png"

    echo "  Created: $output_png"

    # Generate JSON metadata
    output_json="$OUTPUT_DIR/${faction}.json"
    echo "{" > "$output_json"
    echo "  \"faction\": \"$faction\"," >> "$output_json"
    echo "  \"sprite_size\": $SPRITE_SIZE," >> "$output_json"
    echo "  \"columns\": $cols," >> "$output_json"
    echo "  \"rows\": $rows," >> "$output_json"
    echo "  \"sheet_width\": $sheet_width," >> "$output_json"
    echo "  \"sheet_height\": $sheet_height," >> "$output_json"
    echo "  \"sprites\": [" >> "$output_json"

    idx=0
    for sprite in "${sprites[@]}"; do
        # Get ship name from path
        ship_name=$(basename "$sprite" .png)
        ship_class=$(basename "$(dirname "$sprite")")

        # Calculate position in sheet
        col=$((idx % cols))
        row=$((idx / cols))
        x=$((col * SPRITE_SIZE))
        y=$((row * SPRITE_SIZE))

        # JSON entry
        comma=","
        [ $idx -eq $((count - 1)) ] && comma=""

        echo "    {\"name\": \"$ship_name\", \"class\": \"$ship_class\", \"x\": $x, \"y\": $y, \"index\": $idx}$comma" >> "$output_json"

        idx=$((idx + 1))
    done

    echo "  ]" >> "$output_json"
    echo "}" >> "$output_json"

    echo "  Metadata: $output_json"
    echo ""
done

echo "=== Summary ==="
echo "Sprite sheets saved to: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/*.png 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Done!"
