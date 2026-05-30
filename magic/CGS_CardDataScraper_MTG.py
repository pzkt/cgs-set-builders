import json
import requests
import re
import os
import time

script_dir = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(script_dir, "mtg_list.txt")
OUTPUT_JSON = os.path.join(script_dir, "mtg_cards.json")
CACHE_FILE = os.path.join(script_dir, "scryfall_cache.json")

COLOR_MAP = {
    "W": "white",
    "U": "blue",
    "B": "black",
    "R": "red",
    "G": "green"
}

TYPE_MAP = {
    "Planeswalker": "planeswalker",
    "Creature": "summon",
    "Sorcery": "backrow",
    "Instant": "backrow",
    "Artifact": "backrow",
    "Enchantment": "backrow",
    "Kindred": "backrow",
    "Land": "resource",
    "Battle": "battle"
}

VALID_SUPERTYPES = {
    "Basic",
    "Legendary",
    "Ongoing",
    "Snow",
    "World"
}

VALID_TYPES = {
    "Creature",
    "Planeswalker",
    "Sorcery",
    "Instant",
    "Artifact",
    "Enchantment",
    "Land",
    "Battle",
    "Kindred"
}

# =========================================================
# CACHE
# =========================================================

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[CACHE ERROR] Could not load cache: {e}")
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CACHE ERROR] Could not save cache: {e}")

# =========================================================
# INPUT PARSING
# =========================================================

def parse_line(line):
    match = re.match(r"\d+\s+(.+?)\s+\(([^)]+)\)\s+(.+)", line)

    if not match:
        return None

    name = match.group(1).split("/")[0].strip()
    set_code = match.group(2).lower()
    collector_number = match.group(3)

    return name, set_code, collector_number

# =========================================================
# SCRYFALL FETCHING
# =========================================================

def fetch_card(name, set_code, collector_number, cache, retries=3):

    cache_key = f"{set_code}_{collector_number}"

    # Return cached card immediately
    if cache_key in cache:
        print(f"[CACHE] {name} ({set_code.upper()} {collector_number})")
        return cache[cache_key]

    url = (
        "https://api.scryfall.com/cards/named"
        f"?exact={name}"
        f"&set={set_code}"
        f"&collector_number={collector_number}"
    )

    for attempt in range(retries):

        try:
            r = requests.get(url, timeout=15)

            r.raise_for_status()

            data = r.json()

            # Save successful fetch to cache
            cache[cache_key] = data
            save_cache(cache)

            print(f"[FETCH] {name} ({set_code.upper()} {collector_number})")

            # Small delay to avoid hammering Scryfall
            time.sleep(0.1)

            return data

        except requests.exceptions.RequestException as e:

            print(
                f"[RETRY {attempt + 1}/{retries}] "
                f"{name} ({set_code.upper()} {collector_number}) -> {e}"
            )

            time.sleep(2)

    print(
        f"[FAILED] {name} ({set_code.upper()} {collector_number})"
    )

    return None

# =========================================================
# CARD NORMALIZATION
# =========================================================

def normalize_card_data(data):

    backside_url = ""

    # Double-faced / transform cards
    if "card_faces" in data and isinstance(data["card_faces"], list):

        face = data["card_faces"][0]

        face_colors = face.get("colors")

        # Extract backside image if present
        if len(data["card_faces"]) > 1:

            backside = data["card_faces"][1]

            backside_url = (
                backside.get("image_uris", {})
                .get("large", "")
            )

        return {
            "name": face.get("name", data.get("name")),
            "type_line": face.get("type_line", ""),
            "power": face.get("power"),
            "toughness": face.get("toughness"),
            "image_uris": face.get("image_uris", {}),
            "colors": (
                face_colors
                if face_colors is not None
                else data.get("colors", [])
            ),
            "cmc": data.get("cmc", 0),
            "backside_url": backside_url
        }

    return {
        "name": data["name"],
        "type_line": data["type_line"],
        "power": data.get("power"),
        "toughness": data.get("toughness"),
        "image_uris": data.get("image_uris", {}),
        "colors": data.get("colors", []),
        "cmc": data["cmc"],
        "backside_url": ""
    }

# =========================================================
# TYPE PARSING
# =========================================================

def normalize_type_line(type_line):
    return (
        type_line
        .replace("\u2014", "-")
        .replace("\u2013", "-")
    )

def extract_super_and_types(type_line):

    normalized = normalize_type_line(type_line)

    left_side = normalized.split("-")[0].strip()

    tokens = left_side.split()

    supertypes = []
    types = []

    for token in tokens:

        if token in VALID_SUPERTYPES:
            supertypes.append(token)

        elif token in VALID_TYPES:
            types.append(token)

    return supertypes, types

def extract_types_for_cube(type_line):

    normalized = normalize_type_line(type_line)

    main_types = normalized.split("-")[0].strip().split()

    return list({
        TYPE_MAP[t]
        for t in main_types
        if t in TYPE_MAP
    })

def extract_grouping(type_line):

    normalized = normalize_type_line(type_line)

    if "-" not in normalized:
        return []

    subtypes = normalized.split("-", 1)[1]

    return [s.strip() for s in subtypes.split()]

# =========================================================
# POWER / TOUGHNESS
# =========================================================

def parse_pt(value):

    if value is None:
        return ""

    if value == "*":
        return 0

    try:
        return int(value)

    except ValueError:
        return 0

# =========================================================
# MAIN
# =========================================================

def main():

    cards = []

    cache = load_cache()

    with open(INPUT_FILE, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            parsed = parse_line(line)

            if not parsed:
                print(f"[SKIP] Could not parse line: {line}")
                continue

            name, set_code, collector_number = parsed

            raw_data = fetch_card(
                name,
                set_code,
                collector_number,
                cache
            )

            if raw_data is None:
                continue

            data = normalize_card_data(raw_data)

            raw_colors = data.get("colors", [])

            # Explicit colorless handling
            if not raw_colors:
                colors = ["colorless"]
            else:
                colors = [
                    COLOR_MAP[c]
                    for c in raw_colors
                    if c in COLOR_MAP
                ]

            grouping = extract_grouping(data["type_line"])

            cube_types = extract_types_for_cube(
                data["type_line"]
            )

            supertypes, card_types = extract_super_and_types(
                data["type_line"]
            )

            power = parse_pt(data.get("power"))

            toughness = parse_pt(data.get("toughness"))

            cmc = data["cmc"]

            card = {
                "id": f"mtg{set_code}{collector_number}",
                "name": data["name"],
                "colors": colors,
                "grouping": grouping,
                "large-img": data["image_uris"].get("large", ""),
                "small-img": data["image_uris"].get("small", ""),
                "backside-url": data.get("backside_url", ""),
                "rank": cmc,
                "dmg": power,
                "def": toughness,
                "cost": cmc,
                "game-id": "Magic: The Gathering",
                "types": cube_types,
                "Type": card_types,
                "Supertype": supertypes
            }

            cards.append(card)

            print(
                f"[OK] {data['name']} | "
                f"Colors: {colors} | "
                f"Types: {cube_types}"
            )

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:

        json.dump(
            cards,
            out,
            indent=4,
            ensure_ascii=False
        )

    print("")
    print(f"Exported {len(cards)} Magic cards.")
    print(f"Cache saved to: {CACHE_FILE}")

# =========================================================

if __name__ == "__main__":
    main()