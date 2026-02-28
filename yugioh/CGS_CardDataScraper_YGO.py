import csv
import json
import requests

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(script_dir, "yugioh-cube.csv")
OUTPUT_JSON = os.path.join(script_dir, "yugioh_cards.json")

ATTRIBUTE_COLORS = {
    "EARTH": "black",
    "WIND": "green",
    "WATER": "blue",
    "FIRE": "red",
    "DARK": "purple",
    "LIGHT": "white",
    "DIVINE": "gold",
}

def fetch_card_info(card_id):
    """Query YGOPRODeck API for card data."""
    url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?id={card_id}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()["data"][0]

        return {
            "race": data.get("race"),
            "attribute": data.get("attribute"),
            "level": data.get("level"),
            "link": data.get("linkval"),
            "atk": data.get("atk"),
            "def": data.get("def"),
            "type_raw": data.get("type", "")
        }
    except Exception:
        return None

def map_color(api_info):
    """Determine cube color."""
    if api_info["attribute"] in ATTRIBUTE_COLORS:
        return [ATTRIBUTE_COLORS[api_info["attribute"]]]
    if api_info["type_raw"] == "Spell Card":
        return ["blue"]
    if api_info["type_raw"] == "Trap Card":
        return ["red"]
    return []

def determine_types(csv_type):
    """summon (monster) or backrow (spell/trap)."""
    last_word = csv_type.strip().split(" ")[-1].lower()
    if last_word == "monster":
        return ["summon"]
    if last_word in ("spell", "trap"):
        return ["backrow"]
    return []

def calculate_stats(api_info, csv_type):
    """Calculate rank, dmg, def."""
    last_word = csv_type.strip().split(" ")[-1].lower()

    if last_word == "monster":
        rank = api_info["level"] if api_info["level"] is not None else api_info["link"]

        atk = api_info["atk"]
        defe = api_info["def"]

        dmg = round(atk / 1000, 3) if isinstance(atk, int) else ""
        df = round(defe / 1000, 3) if isinstance(defe, int) else ""

        return rank, dmg, df

    if last_word == "spell":
        return "spell", "", ""
    if last_word == "trap":
        return "trap", "", ""

    return None, "", ""

def extract_type_and_supertype(type_raw):
    """
    Extract:
    - type: ["Monster"] | ["Spell"] | ["Trap"]
    - supertype: correctly inferred monster supertypes
    """

    if type_raw.endswith("Monster"):
        words = type_raw.replace("Monster", "").strip().split()

        supertypes = set(words)

        EXTRA_DECK_TYPES = {"Fusion", "Synchro", "Xyz", "Link"}

        is_extra_deck = any(t in supertypes for t in EXTRA_DECK_TYPES)
        is_normal = "Normal" in supertypes

        # Extra Deck monsters are Effect monsters unless explicitly Normal
        if is_extra_deck and not is_normal:
            supertypes.add("Effect")

        # Pendulum monsters are Effect unless Normal Pendulum
        if "Pendulum" in supertypes and not is_normal:
            supertypes.add("Effect")

        return ["Monster"], sorted(supertypes)

    if type_raw == "Spell Card":
        return ["Spell"], []

    if type_raw == "Trap Card":
        return ["Trap"], []

    return [], []

def main():
    cards = []

    with open(CSV_FILE, newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)
            card_id, card_name, csv_type, _ = row

            card_id = card_id.strip()
            card_name = card_name.strip()
            csv_type = csv_type.strip()

            api_info = fetch_card_info(card_id)
            if not api_info:
                continue

            grouping = [api_info["race"]] if api_info["race"] else []
            colors = map_color(api_info)

            large_img = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
            small_img = f"https://images.ygoprodeck.com/images/cards_small/{card_id}.jpg"

            rank, dmg, df = calculate_stats(api_info, csv_type)
            summon_types = determine_types(csv_type)

            type_arr, supertype_arr = extract_type_and_supertype(api_info["type_raw"])

            card_obj = {
                "id": f"ygo{card_id}",
                "name": card_name,
                "colors": colors,
                "grouping": grouping,
                "large-img": large_img,
                "small-img": small_img,
                "rank": rank,
                "dmg": dmg,
                "def": df,
                "cost": 0,
                "game-id": "Yu-Gi-Oh",
                "types": summon_types,     # summon / backrow
                "type": type_arr,          # Monster / Spell / Trap
                "supertype": supertype_arr # Effect, Fusion, Tuner, etc.
            }

            cards.append(card_obj)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(cards, out, indent=4, ensure_ascii=False)

    print(f"Complete. Exported {len(cards)} cards to {OUTPUT_JSON}.")

if __name__ == "__main__":
    main()
