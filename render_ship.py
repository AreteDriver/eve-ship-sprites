#!/usr/bin/env python3
"""
Blender script to render a top-down orthographic view of an STL file.
Usage: blender --background --python render_ship.py -- input.stl output.png [resolution]
"""

import bpy
import sys
import os
import math
import json

# Path to orientation overrides (relative to script location)
ORIENTATIONS_FILE = os.path.join(os.path.dirname(__file__), "ship_orientations.json")
SIZES_FILE = os.path.join(os.path.dirname(__file__), "ship_sizes.json")

# Scale configuration
# Reference: frigate (75m) fills ~15% of frame, titan (14000m) fills 100%
REFERENCE_SIZE_METERS = 75  # Frigate baseline
MIN_FILL_RATIO = 0.85  # All ships fill most of frame (game sprites)
MAX_FILL_RATIO = 1.0   # Largest ships fill 100% of frame
SCALE_POWER = 0.4  # Power curve (0.5 = sqrt, lower = more compressed range)

# Faction color palettes (base_color, metallic, roughness, specular_tint)
FACTION_MATERIALS = {
    'amarr': {
        'base_color': (0.85, 0.65, 0.25, 1.0),  # Gold/bronze
        'metallic': 0.9,
        'roughness': 0.15,
        'specular': 0.8,
    },
    'caldari': {
        'base_color': (0.55, 0.6, 0.7, 1.0),  # Blue-gray chrome
        'metallic': 0.95,
        'roughness': 0.12,
        'specular': 0.9,
    },
    'gallente': {
        'base_color': (0.4, 0.55, 0.35, 1.0),  # Olive-green
        'metallic': 0.7,
        'roughness': 0.25,
        'specular': 0.6,
    },
    'minmatar': {
        'base_color': (0.65, 0.4, 0.28, 1.0),  # Rust/copper
        'metallic': 0.6,
        'roughness': 0.35,
        'specular': 0.5,
    },
    'pirate': {
        'base_color': (0.25, 0.22, 0.25, 1.0),  # Dark gunmetal
        'metallic': 0.85,
        'roughness': 0.2,
        'specular': 0.7,
    },
    'triglavian': {
        'base_color': (0.6, 0.15, 0.15, 1.0),  # Deep red
        'metallic': 0.8,
        'roughness': 0.18,
        'specular': 0.75,
    },
    'sleeper': {
        'base_color': (0.5, 0.55, 0.5, 1.0),  # Faded teal-gray
        'metallic': 0.75,
        'roughness': 0.22,
        'specular': 0.65,
    },
    'rogue': {
        'base_color': (0.3, 0.32, 0.35, 1.0),  # Industrial gray
        'metallic': 0.7,
        'roughness': 0.3,
        'specular': 0.55,
    },
    'concord': {
        'base_color': (0.2, 0.25, 0.45, 1.0),  # Deep blue
        'metallic': 0.9,
        'roughness': 0.1,
        'specular': 0.85,
    },
    'ore': {
        'base_color': (0.7, 0.55, 0.25, 1.0),  # Industrial orange
        'metallic': 0.5,
        'roughness': 0.4,
        'specular': 0.4,
    },
    'jove': {
        'base_color': (0.7, 0.72, 0.75, 1.0),  # Pristine silver
        'metallic': 1.0,
        'roughness': 0.08,
        'specular': 1.0,
    },
    'nation': {
        'base_color': (0.15, 0.15, 0.18, 1.0),  # Near-black
        'metallic': 0.9,
        'roughness': 0.15,
        'specular': 0.8,
    },
    'raiders': {
        'base_color': (0.45, 0.35, 0.3, 1.0),  # Weathered brown
        'metallic': 0.55,
        'roughness': 0.45,
        'specular': 0.4,
    },
    'upwell': {
        'base_color': (0.6, 0.62, 0.65, 1.0),  # Clean industrial
        'metallic': 0.8,
        'roughness': 0.2,
        'specular': 0.7,
    },
    # Default fallback
    '_default': {
        'base_color': (0.5, 0.52, 0.55, 1.0),  # Neutral gray
        'metallic': 0.75,
        'roughness': 0.25,
        'specular': 0.6,
    },
}

def load_orientations():
    """Load ship orientation overrides from JSON file."""
    if os.path.exists(ORIENTATIONS_FILE):
        with open(ORIENTATIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_ship_sizes():
    """Load ship size data from JSON file."""
    if os.path.exists(SIZES_FILE):
        with open(SIZES_FILE, 'r') as f:
            return json.load(f)
    return {}

def get_ship_size(ship_key, sizes_data):
    """Get ship size in meters from sizes data.

    Falls back to class defaults if specific ship not found.
    Returns None if no size data available.
    """
    if not sizes_data or not ship_key:
        return None

    # Try exact match first
    if ship_key in sizes_data:
        return sizes_data[ship_key]

    # Try class default based on path
    parts = ship_key.split('/')
    if len(parts) >= 2:
        ship_class = parts[1]  # e.g., 'frigate', 'cruiser', 'capital'
        class_defaults = sizes_data.get('_class_defaults', {})
        if ship_class in class_defaults:
            return class_defaults[ship_class]

    return None

def calculate_fill_ratio(size_meters):
    """Calculate how much of the frame the ship should fill based on its size.

    Uses a power curve to compress the wide range of ship sizes (75m to 14000m)
    into a visually useful range (12% to 100% of frame).
    """
    if size_meters is None:
        return MAX_FILL_RATIO  # Default: fill frame if size unknown

    # Normalize to reference size
    normalized = size_meters / REFERENCE_SIZE_METERS

    # Apply power curve to compress range
    # e.g., power=0.4 means titan (186x frigate) appears as 186^0.4 = 9.5x larger
    scaled = pow(normalized, SCALE_POWER)

    # Map to fill ratio range
    # At normalized=1 (frigate), scaled=1, fill=MIN_FILL_RATIO
    # At normalized=186 (titan), scaled=9.5, we want fill=MAX_FILL_RATIO
    max_normalized = pow(14000 / REFERENCE_SIZE_METERS, SCALE_POWER)  # ~9.5

    fill = MIN_FILL_RATIO + (MAX_FILL_RATIO - MIN_FILL_RATIO) * (scaled - 1) / (max_normalized - 1)

    # Clamp to valid range
    return max(MIN_FILL_RATIO, min(MAX_FILL_RATIO, fill))

def get_ship_key(output_path):
    """Extract ship key from output path (e.g., 'amarr/frigate/punisher').

    Handles both standard paths and paths with spaces (pirate factions).
    """
    # Normalize path and extract faction/class/ship
    path = output_path.replace('\\', '/')
    parts = path.split('/')

    # Find the ship name (without .png)
    ship_name = os.path.splitext(parts[-1])[0]

    # All known factions (including pirate sub-factions with spaces)
    main_factions = ['amarr', 'caldari', 'gallente', 'minmatar', 'pirate',
                     'ore', 'jove', 'concord', 'triglavian', 'sleeper',
                     'rogue', 'special_edition', 'upwell']

    # Try to find faction/class/ship pattern
    for i, part in enumerate(parts):
        if part in main_factions:
            if i + 2 < len(parts):
                return f"{parts[i]}/{parts[i+1]}/{ship_name}"
            elif i + 1 < len(parts):
                return f"{parts[i]}/{ship_name}"

    return None

def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def import_stl(filepath):
    """Import an STL file and return the imported object."""
    bpy.ops.wm.stl_import(filepath=filepath)
    obj = bpy.context.selected_objects[0]
    return obj

def setup_camera_topdown(obj, scale_override=None, fill_ratio=1.0, resolution=512):
    """Set up an orthographic camera looking down Z axis at the object.

    Args:
        obj: The Blender object to frame
        scale_override: Optional dict with 'scale' multiplier for large models
        fill_ratio: How much of the frame the ship should fill (0.0-1.0)
        resolution: Output resolution in pixels
    """
    bpy.context.view_layer.update()

    dims = obj.dimensions
    # After orient_for_topdown, X=width, Y=length, Z=height
    model_extent = max(dims.x, dims.y)

    # Apply scale multiplier for large/problematic models
    scale_mult = 1.1  # Default 10% margin
    if scale_override and 'scale' in scale_override:
        scale_mult = scale_override['scale']

    # Calculate ortho_scale to achieve desired fill ratio
    # ortho_scale is how many Blender units fit in the frame
    # To make ship fill X% of frame: ortho_scale = model_extent / fill_ratio
    target_fill = fill_ratio * scale_mult
    ortho_scale = model_extent / target_fill

    print(f"Size scaling: fill_ratio={fill_ratio:.2f}, model={model_extent:.1f}, ortho_scale={ortho_scale:.1f}")

    # Camera above looking down -Z (far enough for any model)
    cam_height = max(dims.z + 100, 1000)
    cam_location = (0, 0, cam_height)

    print(f"Camera: pos={cam_location}, ortho_scale={ortho_scale:.1f}, dims=({dims.x:.1f}, {dims.y:.1f}, {dims.z:.1f})")

    bpy.ops.object.camera_add(location=cam_location)
    camera = bpy.context.object
    camera.rotation_euler = (0, 0, 0)  # Look along -Z
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = ortho_scale
    camera.data.clip_end = cam_height + dims.z + 1000  # Ensure clip plane is far enough

    bpy.context.scene.camera = camera
    return camera, cam_location

def get_faction_from_path(output_path):
    """Extract faction name from output path."""
    path = output_path.replace('\\', '/').lower()

    # Check for main factions in path
    for faction in FACTION_MATERIALS.keys():
        if faction != '_default' and f'/{faction}/' in path:
            return faction

    # Fallback: check if faction is at start of relative path
    parts = path.split('/')
    for part in parts:
        if part in FACTION_MATERIALS and part != '_default':
            return part

    return '_default'

def setup_lighting(camera_location):
    """Set up dramatic lighting with key, fill, and rim lights for polished sprites."""
    cam_z = camera_location[2]

    # Key light - main illumination from upper-front-right (45° angle)
    bpy.ops.object.light_add(type='SUN', location=(150, -150, cam_z * 0.8))
    key_light = bpy.context.object
    key_light.rotation_euler = (math.radians(45), math.radians(15), math.radians(-45))
    key_light.data.energy = 4.0
    key_light.data.angle = math.radians(5)  # Slightly soft shadows

    # Fill light - softer from opposite side to reduce harsh shadows
    bpy.ops.object.light_add(type='SUN', location=(-120, 120, cam_z * 0.6))
    fill_light = bpy.context.object
    fill_light.rotation_euler = (math.radians(50), math.radians(-10), math.radians(135))
    fill_light.data.energy = 1.5
    fill_light.data.angle = math.radians(15)  # Very soft

    # Rim light - behind and below for edge definition (creates that "glow" outline)
    bpy.ops.object.light_add(type='SUN', location=(0, 200, cam_z * 0.3))
    rim_light = bpy.context.object
    rim_light.rotation_euler = (math.radians(75), 0, math.radians(180))
    rim_light.data.energy = 2.5
    rim_light.data.angle = math.radians(2)  # Sharp for crisp rim

    # Top fill - gentle ambient from above to prevent pure black shadows
    bpy.ops.object.light_add(type='SUN', location=(0, 0, cam_z))
    top_fill = bpy.context.object
    top_fill.rotation_euler = (0, 0, 0)
    top_fill.data.energy = 0.8
    top_fill.data.angle = math.radians(45)  # Very diffuse

def setup_material(obj, faction='_default'):
    """Apply faction-specific material to the object with polished appearance."""
    mat_config = FACTION_MATERIALS.get(faction, FACTION_MATERIALS['_default'])
    print(f"Applying {faction} material: {mat_config['base_color'][:3]}")

    mat = bpy.data.materials.new(name=f"ShipMaterial_{faction}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Get the principled BSDF
    bsdf = nodes["Principled BSDF"]

    # Apply faction colors and material properties
    bsdf.inputs["Base Color"].default_value = mat_config['base_color']
    bsdf.inputs["Metallic"].default_value = mat_config['metallic']
    bsdf.inputs["Roughness"].default_value = mat_config['roughness']
    bsdf.inputs["Specular IOR Level"].default_value = mat_config['specular']

    # Add subtle clearcoat for extra shine on metallic ships
    if mat_config['metallic'] > 0.7:
        bsdf.inputs["Coat Weight"].default_value = 0.15
        bsdf.inputs["Coat Roughness"].default_value = 0.1

    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def setup_render_settings(output_path, resolution=512):
    """Configure render settings for sprite output."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128  # Higher quality for better specular/rim lighting
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'  # Best denoiser for clean results

    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.film_transparent = True  # Transparent background

    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.filepath = output_path

def orient_with_override(obj, override):
    """Apply manual orientation override from metadata.

    Args:
        obj: The Blender object to orient
        override: Dict with orientation settings:
            - axis: which STL axis should point UP (become Z) - 'x', 'y', or 'z'
            - rotation: final Z rotation in degrees (for nose direction)
            - flip: if True, rotate 180° (flip nose direction)
            - rx, ry, rz: explicit euler rotations to apply (advanced)
    """
    bpy.context.view_layer.objects.active = obj

    dims = obj.dimensions.copy()
    print(f"Original dimensions: X={dims.x:.1f}, Y={dims.y:.1f}, Z={dims.z:.1f}")
    print(f"Applying override: {override}")

    # Check for explicit euler rotation mode (most control)
    if 'rx' in override or 'ry' in override or 'rz' in override:
        rx = override.get('rx', 0)
        ry = override.get('ry', 0)
        rz = override.get('rz', 0)
        obj.rotation_euler.x = math.radians(rx)
        obj.rotation_euler.y = math.radians(ry)
        obj.rotation_euler.z = math.radians(rz)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        dims = obj.dimensions
        print(f"After explicit rotation: X={dims.x:.1f}, Y={dims.y:.1f}, Z={dims.z:.1f}")
        return

    # Standard axis-based orientation
    up_axis = override.get('axis', 'z')

    # Rotate to put specified axis pointing up (becoming Z)
    if up_axis == 'x':
        # X should point up, rotate around Y by -90°
        obj.rotation_euler.y = math.radians(-90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    elif up_axis == 'y':
        # Y should point up, rotate around X by 90°
        obj.rotation_euler.x = math.radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    # else Z is already up, no rotation needed

    # Orient longest dimension along Y (nose pointing up in render)
    dims = obj.dimensions
    if dims.x > dims.y:
        obj.rotation_euler.z = math.radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Apply flip if nose is pointing wrong direction (rotate 180°)
    if override.get('flip', False):
        obj.rotation_euler.z = math.radians(180)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Apply any extra Z rotation from metadata (fine-tuning)
    extra_rotation = override.get('rotation', 0)
    if extra_rotation != 0:
        obj.rotation_euler.z = math.radians(extra_rotation)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    dims = obj.dimensions
    print(f"Final dimensions: X={dims.x:.1f}, Y={dims.y:.1f}, Z={dims.z:.1f}")


def orient_for_topdown(obj):
    """Rotate the model so Z is the height axis (smallest dimension).

    This ensures the camera can always look down Z to get a top-down view.
    Also orients so the longest dimension is along Y (nose pointing up).
    """
    bpy.context.view_layer.objects.active = obj

    dims = obj.dimensions.copy()
    print(f"Original dimensions: X={dims.x:.1f}, Y={dims.y:.1f}, Z={dims.z:.1f}")

    dim_list = [(dims.x, 'x', 0), (dims.y, 'y', 1), (dims.z, 'z', 2)]
    dim_list.sort(key=lambda d: d[0])

    smallest = dim_list[0]  # Should become Z (height)
    middle = dim_list[1]    # Should become X (width)
    largest = dim_list[2]   # Should become Y (length)

    print(f"Smallest (height): {smallest[1]}={smallest[0]:.1f}")
    print(f"Middle (width): {middle[1]}={middle[0]:.1f}")
    print(f"Largest (length): {largest[1]}={largest[0]:.1f}")

    # Rotate model to put smallest dimension on Z axis
    if smallest[1] == 'x':
        # X is smallest, rotate around Y by 90°
        obj.rotation_euler.y = math.radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    elif smallest[1] == 'y':
        # Y is smallest, rotate around X by 90°
        obj.rotation_euler.x = math.radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    # else Z is already smallest, no rotation needed

    # Now check if we need to rotate around Z to put length along Y
    dims = obj.dimensions
    if dims.x > dims.y:
        obj.rotation_euler.z = math.radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    dims = obj.dimensions
    print(f"Final dimensions: X={dims.x:.1f}, Y={dims.y:.1f}, Z={dims.z:.1f}")

def render_ship(input_stl, output_png, resolution=512, orientations=None, sizes=None):
    """Main function to render a ship STL to a top-down PNG sprite."""
    import mathutils  # Must import after bpy is loaded

    # Make mathutils available globally
    global mathutils
    import mathutils

    clear_scene()

    # Import the model
    obj = import_stl(input_stl)

    # Center the object at origin
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0, 0, 0)

    # Check for orientation override
    ship_key = get_ship_key(output_png)
    override = None
    if orientations and ship_key:
        override = orientations.get(ship_key)
        if override:
            print(f"Found orientation override for: {ship_key}")

    # Get ship size and calculate fill ratio
    ship_size = get_ship_size(ship_key, sizes)
    fill_ratio = calculate_fill_ratio(ship_size)
    if ship_size:
        print(f"Ship size: {ship_size}m -> fill ratio: {fill_ratio:.2f}")

    # Rotate model so camera can look down Z for top-down view
    if override:
        orient_with_override(obj, override)
    else:
        orient_for_topdown(obj)

    # Re-center after rotation
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0, 0, 0)

    # Detect faction for material coloring
    faction = get_faction_from_path(output_png)
    print(f"Detected faction: {faction}")

    # Set up scene
    setup_material(obj, faction)
    camera, cam_location = setup_camera_topdown(obj, override, fill_ratio, resolution)
    setup_lighting(cam_location)
    setup_render_settings(output_png, resolution)

    # Render
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_png}")

def main():
    # Get arguments after "--"
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        print("Usage: blender --background --python render_ship.py -- input.stl output.png [resolution]")
        sys.exit(1)

    if len(argv) < 2:
        print("Usage: blender --background --python render_ship.py -- input.stl output.png [resolution]")
        sys.exit(1)

    input_stl = argv[0]
    output_png = argv[1]
    resolution = int(argv[2]) if len(argv) > 2 else 512

    if not os.path.exists(input_stl):
        print(f"Error: Input file not found: {input_stl}")
        sys.exit(1)

    # Load orientation overrides
    orientations = load_orientations()
    if orientations:
        # Count non-comment entries
        count = len([k for k in orientations.keys() if not k.startswith('_')])
        print(f"Loaded {count} orientation overrides")

    # Load ship sizes
    sizes = load_ship_sizes()
    if sizes:
        count = len([k for k in sizes.keys() if not k.startswith('_')])
        print(f"Loaded {count} ship sizes")

    render_ship(input_stl, output_png, resolution, orientations, sizes)

if __name__ == "__main__":
    main()
