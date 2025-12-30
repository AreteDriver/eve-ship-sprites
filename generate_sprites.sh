#!/bin/bash
#
# generate_sprites.sh - Automated EVE Online ship sprite generator
#
# This script:
#   1. Clones the EvE-3D-Printing repository (if needed)
#   2. Finds all STL ship models
#   3. Renders top-down sprites using Blender
#
# Usage: ./generate_sprites.sh [resolution] [--parallel N]
#
# Requirements: git, blender

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/Kyle-Cerniglia/EvE-3D-Printing.git"
REPO_DIR="$SCRIPT_DIR/EvE-3D-Printing"
OUTPUT_DIR="/home/arete/eve-ship-sprites"
RENDER_SCRIPT="$SCRIPT_DIR/render_ship.py"
RESOLUTION="${1:-512}"
PARALLEL_JOBS=1

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --parallel)
            PARALLEL_JOBS="$2"
            shift 2
            ;;
        [0-9]*)
            RESOLUTION="$1"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v git &> /dev/null; then
        log_error "git is not installed. Please install git."
        exit 1
    fi

    if ! command -v blender &> /dev/null; then
        log_error "blender is not installed."
        echo "  Install with: sudo apt install blender"
        echo "  Or download from: https://www.blender.org/download/"
        exit 1
    fi

    log_success "All dependencies found"
}

# Clone or update repository
setup_repository() {
    if [ -d "$REPO_DIR" ]; then
        log_info "Repository already exists, pulling updates..."
        cd "$REPO_DIR"
        git pull || log_warn "Could not pull updates, using existing files"
        cd "$SCRIPT_DIR"
    else
        log_info "Cloning EvE-3D-Printing repository..."
        git clone --depth 1 "$REPO_URL" "$REPO_DIR"
        log_success "Repository cloned"
    fi
}

# Create output directory structure
setup_output_dirs() {
    log_info "Setting up output directories..."
    mkdir -p "$OUTPUT_DIR"

    # Mirror the ships directory structure
    cd "$REPO_DIR/ships"
    find . -type d | while read -r dir; do
        mkdir -p "$OUTPUT_DIR/$dir"
    done
    cd "$SCRIPT_DIR"

    log_success "Output directories created"
}

# Render a single ship
render_ship() {
    local stl_file="$1"
    local relative_path="${stl_file#$REPO_DIR/ships/}"
    local output_file="$OUTPUT_DIR/${relative_path%.stl}.png"

    # Skip if already rendered
    if [ -f "$output_file" ]; then
        echo "  [SKIP] Already exists: $output_file"
        return 0
    fi

    echo "  [RENDER] $relative_path"
    blender --background --python "$RENDER_SCRIPT" -- "$stl_file" "$output_file" "$RESOLUTION" 2>/dev/null

    if [ -f "$output_file" ]; then
        echo "  [OK] $output_file"
        return 0
    else
        echo "  [FAIL] $relative_path"
        return 1
    fi
}

# Export function for parallel execution
export -f render_ship
export REPO_DIR OUTPUT_DIR RENDER_SCRIPT RESOLUTION

# Main rendering loop
render_all_ships() {
    log_info "Finding all STL files..."

    local stl_files=()
    while IFS= read -r -d '' file; do
        stl_files+=("$file")
    done < <(find "$REPO_DIR/ships" -name "*.stl" -type f -print0)

    local total=${#stl_files[@]}
    log_info "Found $total STL files to process"
    log_info "Rendering at ${RESOLUTION}x${RESOLUTION} resolution..."
    echo ""

    local count=0
    local success=0
    local skipped=0
    local failed=0

    for stl_file in "${stl_files[@]}"; do
        count=$((count + 1))
        echo "[$count/$total] Processing: $(basename "$stl_file")"

        local relative_path="${stl_file#$REPO_DIR/ships/}"
        local output_file="$OUTPUT_DIR/${relative_path%.stl}.png"

        if [ -f "$output_file" ]; then
            echo "  [SKIP] Already exists"
            skipped=$((skipped + 1))
            continue
        fi

        if blender --background --python "$RENDER_SCRIPT" -- "$stl_file" "$output_file" "$RESOLUTION" 2>/dev/null; then
            if [ -f "$output_file" ]; then
                echo "  [OK] Rendered successfully"
                success=$((success + 1))
            else
                echo "  [FAIL] Output file not created"
                failed=$((failed + 1))
            fi
        else
            echo "  [FAIL] Blender error"
            failed=$((failed + 1))
        fi
    done

    echo ""
    log_info "===== SUMMARY ====="
    log_success "Rendered: $success"
    log_info "Skipped (already existed): $skipped"
    if [ $failed -gt 0 ]; then
        log_error "Failed: $failed"
    fi
    log_info "Output directory: $OUTPUT_DIR"
}

# Main execution
main() {
    echo ""
    echo "=========================================="
    echo "   EVE Online Ship Sprite Generator"
    echo "=========================================="
    echo ""

    check_dependencies
    setup_repository
    setup_output_dirs
    render_all_ships

    echo ""
    log_success "Done! Sprites are in: $OUTPUT_DIR"
    echo ""
}

main
