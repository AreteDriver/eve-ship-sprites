#!/bin/bash
# Re-render sprites used by eve_rebellion_rust with full-frame sizing

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ships needed by the game (from copy_to_rebellion.py TYPE_MAP)
declare -A SHIPS=(
    # Caldari
    ["caldari/frigate/bantam"]="583"
    ["caldari/frigate/kestrel"]="602"
    ["caldari/frigate/merlin"]="603"
    ["caldari/frigate/condor"]="605"
    ["caldari/frigate/griffin"]="608"
    ["caldari/battleship/raven"]="638"
    ["caldari/battleship/scorpion"]="639"
    ["caldari/battleship/rokh"]="640"
    ["caldari/battlecruiser/drake"]="24688"
    ["caldari/battlecruiser/ferox"]="16238"
    ["caldari/battlecruiser/nighthawk"]="16236"
    ["caldari/destroyer/Jackdaw"]="35683"

    # Amarr
    ["amarr/frigate/impairor"]="589"
    ["amarr/frigate/magnate"]="593"
    ["amarr/frigate/crucifier"]="594"
    ["amarr/frigate/punisher"]="597"
    ["amarr/frigate/inquisitor"]="598"
    ["amarr/frigate/vengeance"]="11184"
    ["amarr/frigate/retribution"]="11186"
    ["amarr/cruiser/omen"]="624"
    ["amarr/cruiser/maller"]="625"
    ["amarr/cruiser/augoror"]="626"
    ["amarr/battleship/armageddon"]="643"
    ["amarr/battlecruiser/prophecy"]="24690"
    ["amarr/battlecruiser/harbringer"]="16240"

    # Gallente
    ["gallente/frigate/atron"]="585"
    ["gallente/frigate/incursus"]="586"
    ["gallente/frigate/tristan"]="587"
    ["gallente/frigate/maulus"]="591"
    ["gallente/frigate/navitas"]="592"
    ["gallente/cruiser/exequror"]="630"
    ["gallente/battleship/dominix"]="641"
    ["gallente/battleship/megathron"]="645"
    ["gallente/battlecruiser/myrmidon"]="24696"
    ["gallente/battlecruiser/brutix"]="16242"

    # Minmatar
    ["minmatar/frigate/wolf"]="11371"
    ["minmatar/frigate/jaguar"]="11373"
    ["minmatar/cruiser/vagabond"]="11377"
    ["minmatar/cruiser/muninn"]="11381"
    ["minmatar/cruiser/scythe"]="11387"
    ["minmatar/cruiser/stabber"]="11400"
    ["minmatar/battleship/tempest"]="24694"
    ["minmatar/battleship/typhoon"]="24700"
    ["minmatar/battlecruiser/cyclone"]="11547"
    ["minmatar/battlecruiser/hurricane"]="11566"
    ["minmatar/battlecruiser/sleipnir"]="11567"
    ["minmatar/destroyer/svipul"]="35685"

    # Special
    ["concord/frigate/pacifier"]="1944"
    ["pirate/fighter/Pirate_Fighter"]="3764"
    ["ore/frigate/venture"]="20185"
    ["pirate/soe/Stratios"]="23757"
    ["pirate/sanshas nation/phantasm"]="23911"
    ["pirate/sanshas nation/nightmare"]="23915"
    ["pirate/blood raiders/Ashimmu"]="24483"
    ["triglavian/damavik"]="47269"
    ["triglavian/kikimora"]="47466"
)

STL_BASE="EvE-3D-Printing/ships"
DEST_DIR="/home/arete/projects/eve_rebellion_rust/assets/ships"

echo "=== Re-rendering game sprites with full-frame sizing ==="
echo ""

for ship_path in "${!SHIPS[@]}"; do
    type_id="${SHIPS[$ship_path]}"

    # Find STL file
    ship_name=$(basename "$ship_path")
    faction=$(dirname "$ship_path" | cut -d'/' -f1)

    # Search for STL
    stl_file=$(find "$STL_BASE" -iname "${ship_name}.stl" 2>/dev/null | head -1)

    if [ -z "$stl_file" ]; then
        echo "  SKIP: $ship_name (no STL found)"
        continue
    fi

    output_file="$DEST_DIR/${type_id}.png"

    echo -n "  $type_id ($ship_name)... "

    if timeout 60 blender --background --python render_ship.py -- "$stl_file" "$output_file" 512 > /tmp/render.log 2>&1; then
        echo "OK"
    else
        echo "FAILED"
        tail -3 /tmp/render.log
    fi
done

echo ""
echo "=== Done ==="
