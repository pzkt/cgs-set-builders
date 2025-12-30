import json
import requests
import re

INPUT_FILE = "mtg_list.txt"
OUTPUT_JSON = "mtg_cards.json"

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

def parse_line(line):
    """
    Example:
    1 Kytheon, Hero of Akros / Gideon, Battle-Forged (ORI) 23
    """
    match = re.match(r"\d+\s+(.+?)\s+\(([^)]+)\)\s+(.+)", line)
    if not match:
        return None

    name = match.group(1).split("/")[0].strip()
    set_code = match.group(2).lower()
    collector_number = match.group(3)

    return name, set_code, collector_number

def fetch_card(name, set_code, collector_number):
    url = (
        "https://api.scryfall.com/cards/named"
        f"?exact={name}"
        f"&set={set_code}"
        f"&collector_number={collector_number}"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def normalize_card_data(data):
    """
    Use the first face for double-faced cards and tokens.
    Prefer face colors if available.
    """
    if "card_faces" in data and isinstance(data["card_faces"], list):
        face = data["card_faces"][0]
        face_colors = face.get("colors")

        return {
            "name": face.get("name", data.get("name")),
            "type_line": face.get("type_line", ""),
            "power": face.get("power"),
            "toughness": face.get("toughness"),
            "image_uris": face.get("image_uris", {}),
            "colors": face_colors if face_colors is not None else data.get("colors", []),
            "cmc": data.get("cmc", 0)
        }

    return {
        "name": data["name"],
        "type_line": data["type_line"],
        "power": data.get("power"),
        "toughness": data.get("toughness"),
        "image_uris": data.get("image_uris", {}),
        "colors": data.get("colors", []),
        "cmc": data["cmc"]
    }

def normalize_type_line(type_line):
    # Replace Unicode em dash with ASCII hyphen
    return type_line.replace("\u2014", "-")

def extract_types(type_line):
    normalized = normalize_type_line(type_line)
    main_types = normalized.split("-")[0].strip().split()
    return list({
        TYPE_MAP[t] for t in main_types if t in TYPE_MAP
    })

def extract_grouping(type_line):
    normalized = normalize_type_line(type_line)
    if "-" not in normalized:
        return []
    subtypes = normalized.split("-", 1)[1]
    return [s.strip() for s in subtypes.split()]

def parse_pt(value):
    if value is None:
        return ""
    if value == "*":
        return 0
    try:
        return int(value)
    except ValueError:
        return 0

def main():
    cards = []

    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parsed = parse_line(line)
            if not parsed:
                continue

            name, set_code, collector_number = parsed
            raw_data = fetch_card(name, set_code, collector_number)
            print(f"[OK] {name} ({set_code.upper()} {collector_number})")
            data = normalize_card_data(raw_data)

            raw_colors = data.get("colors", [])

            if not raw_colors:
              colors = ["colorless"]
            else:
              colors = [
                COLOR_MAP[c] for c in raw_colors
                if c in COLOR_MAP
              ]


            grouping = extract_grouping(data["type_line"])
            types = extract_types(data["type_line"])

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
                "rank": cmc,
                "dmg": power,
                "def": toughness,
                "cost": cmc,
                "game-id": "Magic: The Gathering",
                "types": types
            }

            cards.append(card)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(cards, out, indent=4, ensure_ascii=False)

    print(f"Exported {len(cards)} Magic cards.")

if __name__ == "__main__":
    main()
