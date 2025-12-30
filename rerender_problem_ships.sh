#!/bin/bash
#
# rerender_problem_ships.sh - Re-render ships with orientation issues
#
# Uses ship_orientations.json to apply correct rotations
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Kyle-Cerniglia/EvE-3D-Printing.git"
REPO_DIR="$SCRIPT_DIR/EvE-3D-Printing"
OUTPUT_DIR="$SCRIPT_DIR"
RENDER_SCRIPT="$SCRIPT_DIR/render_ship.py"
RESOLUTION="${1:-512}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Ships to re-render (from rerender_list.txt)
PROBLEM_SHIPS=(
    # Minmatar
    "minmatar/frigate/rifter"
    "minmatar/frigate/breacher"
    "minmatar/frigate/vigil"
    "minmatar/cruiser/rupture"
    "minmatar/cruiser/stabber"
    "minmatar/cruiser/bellicose"
    "minmatar/cruiser/scythe"
    "minmatar/cruiser/vagabond"
    "minmatar/cruiser/huginn"
    "minmatar/cruiser/muninn"
    "minmatar/cruiser/broadsword"
    "minmatar/cruiser/rapier"
    "minmatar/battlecruiser/tornado"
    "minmatar/battleship/tempest"
    "minmatar/battleship/maelstorm"
    "minmatar/battleship/vargur"
    "minmatar/capital/naglfar"
    "minmatar/capital/fenrir"
    # Amarr
    "amarr/frigate/tormentor"
    "amarr/cruiser/augoror"
    "amarr/battlecruiser/oracle"
    "amarr/battleship/apocalypse"
    "amarr/battleship/apocalypse_old"
    "amarr/battleship/abaddon"
    "amarr/battleship/armageddon"
    "amarr/battleship/paladin"
    "amarr/battleship/redeemer"
    "amarr/capital/aeon"
    "amarr/capital/revelation"
    "amarr/capital/avatar"
    # Gallente
    "gallente/cruiser/vexor"
    "gallente/battleship/dominix"
    "gallente/battleship/hyperion"
)

# Check blender
if ! command -v blender &> /dev/null; then
    log_error "Blender is not installed. Please install blender."
    exit 1
fi

# Clone repo if needed
if [ ! -d "$REPO_DIR" ]; then
    log_info "Cloning EvE-3D-Printing repository..."
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
    log_success "Repository cloned"
else
    log_info "STL repository already exists"
fi

# Re-render problem ships
log_info "Re-rendering ${#PROBLEM_SHIPS[@]} problem ships..."
echo ""

success=0
failed=0
notfound=0

for ship in "${PROBLEM_SHIPS[@]}"; do
    stl_file="$REPO_DIR/ships/$ship.stl"
    output_file="$OUTPUT_DIR/$ship.png"

    echo -n "[$((success + failed + notfound + 1))/${#PROBLEM_SHIPS[@]}] $ship... "

    if [ ! -f "$stl_file" ]; then
        echo -e "${YELLOW}STL not found${NC}"
        notfound=$((notfound + 1))
        continue
    fi

    # Remove existing file to force re-render
    rm -f "$output_file"

    # Ensure output directory exists
    mkdir -p "$(dirname "$output_file")"

    if blender --background --python "$RENDER_SCRIPT" -- "$stl_file" "$output_file" "$RESOLUTION" 2>/dev/null; then
        if [ -f "$output_file" ]; then
            echo -e "${GREEN}OK${NC}"
            success=$((success + 1))
        else
            echo -e "${RED}FAIL (no output)${NC}"
            failed=$((failed + 1))
        fi
    else
        echo -e "${RED}FAIL (blender error)${NC}"
        failed=$((failed + 1))
    fi
done

echo ""
log_info "===== SUMMARY ====="
log_success "Re-rendered: $success"
if [ $notfound -gt 0 ]; then
    log_warn "STL not found: $notfound"
fi
if [ $failed -gt 0 ]; then
    log_error "Failed: $failed"
fi
echo ""
