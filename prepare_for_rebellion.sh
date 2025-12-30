#!/bin/bash
#
# prepare_for_rebellion.sh - Prepare sprites for EVE_Rebellion project
#
# 1. Flattens nested structure to single directory
# 2. Renames files to match expected naming convention
# 3. Creates 256x256 variants
#

set -e

SRC_DIR="/home/arete/projects/eve-ship-sprites"
DEST_DIR="/home/arete/projects/EVE_Rebellion/assets/ship_sprites"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Ensure destination exists
mkdir -p "$DEST_DIR"

log_info "=== Step 1: Flatten and copy sprites ==="

copied=0
skipped=0

# Find all PNG files in faction directories
shopt -s nullglob
for png in "$SRC_DIR"/amarr/*/*.png "$SRC_DIR"/caldari/*/*.png "$SRC_DIR"/gallente/*/*.png "$SRC_DIR"/minmatar/*/*.png "$SRC_DIR"/pirate/*/*.png; do
    [ -f "$png" ] || continue

    # Get just the filename (e.g., rifter.png)
    filename=$(basename "$png")
    dest_file="$DEST_DIR/$filename"

    # Copy (overwrite if exists)
    cp "$png" "$dest_file"
    copied=$((copied + 1))
done

log_success "Copied $copied sprites to $DEST_DIR"

log_info "=== Step 2: Create 256x256 variants ==="

converted=0

for png in "$DEST_DIR"/*.png; do
    [ -f "$png" ] || continue

    filename=$(basename "$png" .png)

    # Skip if already a _256 variant
    [[ "$filename" == *_256 ]] && continue
    [[ "$filename" == *_512 ]] && continue
    [[ "$filename" == *_render_* ]] && continue

    dest_256="$DEST_DIR/${filename}_256.png"

    # Create 256x256 version
    convert "$png" -resize 256x256 "$dest_256" 2>/dev/null && {
        converted=$((converted + 1))
    }
done

log_success "Created $converted 256x256 variants"

log_info "=== Summary ==="
echo "  Sprites copied: $copied"
echo "  256x256 created: $converted"
echo "  Destination: $DEST_DIR"
echo ""
log_success "Done! Sprites ready for EVE_Rebellion"
