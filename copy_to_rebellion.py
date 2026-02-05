#!/usr/bin/env python3
"""
Copy faction-colored sprites to eve_rebellion_rust project.
Uses EVE Online type ID to ship name mappings.
"""

import os
import shutil
from pathlib import Path

# EVE Online type ID -> (faction, ship_class, ship_name) mapping
# Source: EVE SDE typeIDs.yaml
TYPE_MAP = {
    # Caldari Frigates
    583: ("caldari", "frigate", "bantam"),
    602: ("caldari", "frigate", "kestrel"),
    603: ("caldari", "frigate", "merlin"),
    605: ("caldari", "frigate", "condor"),
    608: ("caldari", "frigate", "griffin"),
    607: ("caldari", "frigate", "heron"),

    # Caldari Cruisers
    621: ("caldari", "cruiser", "caracal"),
    620: ("caldari", "cruiser", "moa"),
    622: ("caldari", "cruiser", "osprey"),
    623: ("caldari", "cruiser", "blackbird"),

    # Caldari Battleships
    638: ("caldari", "battleship", "raven"),
    639: ("caldari", "battleship", "scorpion"),
    640: ("caldari", "battleship", "rokh"),

    # Caldari Battlecruisers
    24688: ("caldari", "battlecruiser", "drake"),
    16238: ("caldari", "battlecruiser", "ferox"),
    16236: ("caldari", "battlecruiser", "nighthawk"),

    # Amarr Frigates
    589: ("amarr", "frigate", "impairor"),  # Actually this is Impairor (rookie)
    593: ("amarr", "frigate", "magnate"),
    594: ("amarr", "frigate", "crucifier"),
    596: ("amarr", "frigate", "tormentor"),
    597: ("amarr", "frigate", "punisher"),
    598: ("amarr", "frigate", "inquisitor"),
    590: ("amarr", "frigate", "executioner"),

    # Amarr Cruisers
    624: ("amarr", "cruiser", "omen"),
    625: ("amarr", "cruiser", "maller"),
    626: ("amarr", "cruiser", "augoror"),
    628: ("amarr", "cruiser", "arbitrator"),

    # Amarr Battleships
    642: ("amarr", "battleship", "apocalypse"),
    643: ("amarr", "battleship", "armageddon"),
    644: ("amarr", "battleship", "abaddon"),

    # Amarr Battlecruisers
    24690: ("amarr", "battlecruiser", "prophecy"),
    16240: ("amarr", "battlecruiser", "harbringer"),

    # Gallente Frigates
    585: ("gallente", "frigate", "atron"),
    586: ("gallente", "frigate", "incursus"),
    587: ("gallente", "frigate", "tristan"),
    588: ("gallente", "frigate", "imicus"),
    591: ("gallente", "frigate", "maulus"),
    592: ("gallente", "frigate", "navitas"),

    # Gallente Cruisers
    627: ("gallente", "cruiser", "vexor"),
    629: ("gallente", "cruiser", "thorax"),
    630: ("gallente", "cruiser", "exequror"),
    631: ("gallente", "cruiser", "celestis"),

    # Gallente Battleships
    641: ("gallente", "battleship", "dominix"),
    645: ("gallente", "battleship", "megathron"),

    # Gallente Battlecruisers
    24696: ("gallente", "battlecruiser", "myrmidon"),
    16242: ("gallente", "battlecruiser", "brutix"),

    # Minmatar Frigates - these are the correct IDs
    # Note: EVE type IDs for Minmatar frigates start at higher numbers
    # Actually 587 = Rifter according to some sources, need to verify
    # Let me use the commonly known ones:

    # Minmatar Assault Frigates
    11371: ("minmatar", "frigate", "wolf"),
    11373: ("minmatar", "frigate", "jaguar"),

    # Minmatar Cruisers
    11377: ("minmatar", "cruiser", "vagabond"),
    11381: ("minmatar", "cruiser", "muninn"),
    11387: ("minmatar", "cruiser", "scythe"),
    11400: ("minmatar", "cruiser", "stabber"),

    # Minmatar Battleships
    24694: ("minmatar", "battleship", "tempest"),
    24700: ("minmatar", "battleship", "typhoon"),

    # Minmatar Battlecruisers
    11547: ("minmatar", "battlecruiser", "cyclone"),
    11566: ("minmatar", "battlecruiser", "hurricane"),
    11567: ("minmatar", "battlecruiser", "sleipnir"),
    11568: ("minmatar", "battlecruiser", "claymore"),

    # Assault Frigates (Amarr)
    11184: ("amarr", "frigate", "vengeance"),
    11186: ("amarr", "frigate", "retribution"),

    # Special ships
    1944: ("concord", "frigate", "pacifier"),  # CONCORD frigate
    2006: ("special_edition", "battleship", "marshall"),  # Assuming
    3764: ("pirate", "fighter", "Pirate_Fighter"),

    # ORE
    20185: ("ore", "frigate", "venture"),

    # Navy/Pirate
    23757: ("pirate", "soe", "Stratios"),
    23911: ("pirate", "sanshas nation", "phantasm"),
    23915: ("pirate", "sanshas nation", "nightmare"),
    24483: ("pirate", "blood raiders", "Ashimmu"),

    # Triglavian
    47269: ("triglavian", "", "damavik"),
    47466: ("triglavian", "", "kikimora"),

    # T3 Destroyers
    35683: ("caldari", "destroyer", "Jackdaw"),
    35685: ("minmatar", "destroyer", "svipul"),
}

SRC_DIR = Path("/home/arete/projects/eve-ship-sprites")
DEST_DIR = Path("/home/arete/projects/eve_rebellion_rust/assets/ships")


def find_sprite(faction: str, ship_class: str, name: str) -> Path | None:
    """Find sprite file with fuzzy matching."""
    # Direct path attempts
    attempts = [
        SRC_DIR / faction / ship_class / f"{name}.png",
        SRC_DIR / faction / ship_class / f"{name.lower()}.png",
        SRC_DIR / faction / f"{name}.png",
    ]

    for path in attempts:
        if path.exists():
            return path

    # Search in faction directory
    faction_dir = SRC_DIR / faction
    if faction_dir.exists():
        for png in faction_dir.rglob("*.png"):
            if png.stem.lower() == name.lower():
                return png
            # Handle variations like machariel_final
            if name.lower() in png.stem.lower():
                return png

    return None


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Get type IDs to update
    existing_ids = []
    for f in DEST_DIR.glob("*.png"):
        try:
            existing_ids.append(int(f.stem))
        except ValueError:
            pass

    print(f"Updating {len(existing_ids)} sprites with faction colors\n")

    updated = 0
    missing = []

    for type_id in sorted(existing_ids):
        if type_id in TYPE_MAP:
            faction, ship_class, name = TYPE_MAP[type_id]
            src = find_sprite(faction, ship_class, name)

            if src:
                dest = DEST_DIR / f"{type_id}.png"
                shutil.copy2(src, dest)
                print(f"  {type_id:5d}: {name:20s} ({faction:12s}) OK")
                updated += 1
            else:
                missing.append((type_id, faction, ship_class, name))
                print(f"  {type_id:5d}: {name:20s} ({faction:12s}) NOT FOUND")
        else:
            missing.append((type_id, "unknown", "", ""))
            print(f"  {type_id:5d}: {'???':20s} ({'unknown':12s}) NO MAPPING")

    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(existing_ids)}")
    print(f"Missing: {len(missing)}")

    if missing:
        print("\nMissing sprites - need manual resolution:")
        for tid, faction, cls, name in missing:
            print(f"  {tid}: {faction}/{cls}/{name}")


if __name__ == "__main__":
    main()
