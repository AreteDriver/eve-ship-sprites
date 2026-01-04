#!/usr/bin/env python3
"""
Generate visual audit contact sheets for EVE ship sprites.

Creates a grid of all sprites organized by faction for quick visual review.
Each sprite is shown with its name label for easy identification of issues.

Usage:
    python generate_audit_sheet.py [--output DIR] [--size SIZE] [--cols COLS]

Options:
    --output DIR    Output directory (default: audit_sheets/)
    --size SIZE     Thumbnail size in pixels (default: 128)
    --cols COLS     Number of columns in grid (default: 8)
    --all           Generate single sheet with all sprites
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# Faction display order and colors
FACTION_CONFIG = {
    'amarr': {'color': (255, 215, 0), 'order': 1},      # Gold
    'caldari': {'color': (100, 149, 237), 'order': 2},  # Cornflower blue
    'gallente': {'color': (50, 205, 50), 'order': 3},   # Lime green
    'minmatar': {'color': (205, 92, 92), 'order': 4},   # Indian red
    'pirate': {'color': (148, 0, 211), 'order': 5},     # Purple
    'triglavian': {'color': (255, 69, 0), 'order': 6},  # Red-orange
    'ore': {'color': (255, 165, 0), 'order': 7},        # Orange
    'concord': {'color': (70, 130, 180), 'order': 8},   # Steel blue
    'sleeper': {'color': (128, 128, 128), 'order': 9},  # Gray
    'rogue': {'color': (139, 69, 19), 'order': 10},     # Brown
    'jove': {'color': (186, 85, 211), 'order': 11},     # Medium orchid
    'special_edition': {'color': (255, 20, 147), 'order': 12},  # Pink
    'upwell': {'color': (0, 191, 255), 'order': 13},    # Deep sky blue
}


def find_sprites(base_dir: Path) -> dict:
    """Find all sprite PNGs organized by faction."""
    sprites = defaultdict(list)

    for faction_dir in base_dir.iterdir():
        if not faction_dir.is_dir():
            continue
        if faction_dir.name in ['sheets', 'EvE-3D-Printing', 'audit_sheets']:
            continue

        faction = faction_dir.name

        # Find all PNGs recursively
        for png_path in faction_dir.rglob('*.png'):
            rel_path = png_path.relative_to(faction_dir)
            sprites[faction].append({
                'path': png_path,
                'name': png_path.stem,
                'subdir': str(rel_path.parent) if rel_path.parent != Path('.') else '',
            })

    # Sort sprites within each faction by subdir then name
    for faction in sprites:
        sprites[faction].sort(key=lambda x: (x['subdir'], x['name']))

    return sprites


def get_font(size: int = 12):
    """Get a font for labels, with fallback."""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    return ImageFont.load_default()


def create_contact_sheet(
    sprites: list,
    faction: str,
    output_path: Path,
    thumb_size: int = 128,
    cols: int = 8,
    label_height: int = 20,
):
    """Create a contact sheet for a list of sprites."""
    if not sprites:
        return None

    cell_width = thumb_size
    cell_height = thumb_size + label_height

    rows = (len(sprites) + cols - 1) // cols

    # Header height for faction name
    header_height = 40

    # Calculate image dimensions
    img_width = cols * cell_width + 20  # 10px padding on each side
    img_height = header_height + rows * cell_height + 20

    # Create image with dark background
    img = Image.new('RGBA', (img_width, img_height), (30, 30, 35, 255))
    draw = ImageDraw.Draw(img)

    # Get fonts
    title_font = get_font(20)
    label_font = get_font(10)

    # Draw faction header
    faction_color = FACTION_CONFIG.get(faction, {}).get('color', (200, 200, 200))
    draw.rectangle([0, 0, img_width, header_height], fill=(40, 40, 45))

    title = f"{faction.upper()} ({len(sprites)} ships)"
    draw.text((10, 10), title, fill=faction_color, font=title_font)

    # Draw sprites
    for idx, sprite_info in enumerate(sprites):
        row = idx // cols
        col = idx % cols

        x = 10 + col * cell_width
        y = header_height + 10 + row * cell_height

        # Load and resize sprite
        try:
            sprite = Image.open(sprite_info['path']).convert('RGBA')

            # Fit sprite into thumbnail box while maintaining aspect ratio
            sprite.thumbnail((thumb_size - 4, thumb_size - 4), Image.Resampling.LANCZOS)

            # Center sprite in cell
            sprite_x = x + (cell_width - sprite.width) // 2
            sprite_y = y + (thumb_size - sprite.height) // 2

            # Paste sprite
            img.paste(sprite, (sprite_x, sprite_y), sprite)

        except Exception as e:
            # Draw error placeholder
            draw.rectangle([x + 2, y + 2, x + thumb_size - 2, y + thumb_size - 2],
                          outline=(255, 0, 0), width=2)
            draw.text((x + 10, y + thumb_size // 2), "ERROR", fill=(255, 0, 0), font=label_font)

        # Draw label
        label = sprite_info['name']
        if len(label) > 14:
            label = label[:12] + '..'

        # Add subdir prefix if present
        if sprite_info['subdir']:
            subdir_short = sprite_info['subdir'][:3]
            label = f"{subdir_short}/{label}"
            if len(label) > 16:
                label = label[:14] + '..'

        label_y = y + thumb_size + 2
        draw.text((x + 4, label_y), label, fill=(180, 180, 180), font=label_font)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG')
    print(f"Created: {output_path} ({len(sprites)} sprites)")

    return output_path


def create_master_sheet(
    all_sprites: dict,
    output_path: Path,
    thumb_size: int = 96,
    cols: int = 12,
):
    """Create a single master sheet with all factions."""
    label_height = 16
    cell_width = thumb_size
    cell_height = thumb_size + label_height
    header_height = 30

    # Sort factions by config order
    sorted_factions = sorted(
        all_sprites.keys(),
        key=lambda f: FACTION_CONFIG.get(f, {}).get('order', 99)
    )

    # Calculate total height needed
    total_height = 20
    for faction in sorted_factions:
        sprites = all_sprites[faction]
        rows = (len(sprites) + cols - 1) // cols
        total_height += header_height + rows * cell_height + 10

    img_width = cols * cell_width + 20

    # Create master image
    img = Image.new('RGBA', (img_width, total_height), (25, 25, 30, 255))
    draw = ImageDraw.Draw(img)

    title_font = get_font(16)
    label_font = get_font(9)

    y_offset = 10

    for faction in sorted_factions:
        sprites = all_sprites[faction]
        if not sprites:
            continue

        faction_color = FACTION_CONFIG.get(faction, {}).get('color', (200, 200, 200))

        # Faction header
        draw.rectangle([0, y_offset, img_width, y_offset + header_height], fill=(35, 35, 40))
        title = f"{faction.upper()} ({len(sprites)})"
        draw.text((10, y_offset + 6), title, fill=faction_color, font=title_font)

        y_offset += header_height

        # Draw sprites for this faction
        for idx, sprite_info in enumerate(sprites):
            row = idx // cols
            col = idx % cols

            x = 10 + col * cell_width
            y = y_offset + row * cell_height

            try:
                sprite = Image.open(sprite_info['path']).convert('RGBA')
                sprite.thumbnail((thumb_size - 4, thumb_size - 4), Image.Resampling.LANCZOS)

                sprite_x = x + (cell_width - sprite.width) // 2
                sprite_y = y + (thumb_size - sprite.height) // 2

                img.paste(sprite, (sprite_x, sprite_y), sprite)

            except Exception:
                draw.rectangle([x + 2, y + 2, x + thumb_size - 2, y + thumb_size - 2],
                              outline=(255, 0, 0), width=1)

            # Label
            label = sprite_info['name']
            if len(label) > 12:
                label = label[:10] + '..'
            draw.text((x + 2, y + thumb_size), label, fill=(150, 150, 150), font=label_font)

        rows = (len(sprites) + cols - 1) // cols
        y_offset += rows * cell_height + 10

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG')

    total_sprites = sum(len(s) for s in all_sprites.values())
    print(f"Created: {output_path} ({total_sprites} total sprites)")

    return output_path


def main():
    parser = argparse.ArgumentParser(description='Generate visual audit sheets for EVE ship sprites')
    parser.add_argument('--output', '-o', default='audit_sheets', help='Output directory')
    parser.add_argument('--size', '-s', type=int, default=128, help='Thumbnail size (default: 128)')
    parser.add_argument('--cols', '-c', type=int, default=8, help='Columns per row (default: 8)')
    parser.add_argument('--all', '-a', action='store_true', help='Also generate master sheet with all sprites')

    args = parser.parse_args()

    base_dir = Path(__file__).parent
    output_dir = base_dir / args.output

    print("Scanning for sprites...")
    sprites = find_sprites(base_dir)

    if not sprites:
        print("No sprites found!")
        return 1

    total = sum(len(s) for s in sprites.values())
    print(f"Found {total} sprites across {len(sprites)} factions\n")

    # Generate per-faction sheets
    print("Generating faction contact sheets...")
    for faction, faction_sprites in sorted(sprites.items()):
        if faction_sprites:
            output_path = output_dir / f"{faction}_audit.png"
            create_contact_sheet(
                faction_sprites,
                faction,
                output_path,
                thumb_size=args.size,
                cols=args.cols,
            )

    # Generate master sheet if requested
    if args.all:
        print("\nGenerating master sheet...")
        master_path = output_dir / "ALL_SPRITES_audit.png"
        create_master_sheet(sprites, master_path, thumb_size=96, cols=12)

    print(f"\nDone! Sheets saved to: {output_dir}/")
    return 0


if __name__ == '__main__':
    sys.exit(main())
