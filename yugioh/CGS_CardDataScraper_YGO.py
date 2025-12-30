import csv
import json
import requests

CSV_FILE = "yugioh-cube.csv"
OUTPUT_JSON = "yugioh_cards.json"

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
    """Query YGOPRODeck API for race, attribute, level, atk, def."""
    url = f"https://db.ygoprodeck.com/api/v7/cardinfo.php?id={card_id}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()["data"][0]

        return {
            "race": data.get("race", None),
            "attribute": data.get("attribute", None),
            "level": data.get("level", None),
            "link": data.get("linkval", None),
            "atk": data.get("atk", None),
            "def": data.get("def", None),
            "type_raw": data.get("type", "")
        }
    except Exception:
        return None

def map_color(data):
    """Map attribute to cube color rule."""
    if data["attribute"] in ATTRIBUTE_COLORS:
        return [ATTRIBUTE_COLORS[data["attribute"]]]
    elif data["type_raw"] == "Spell Card":
        return ["blue"]  # If it's a spell, make it blue
    elif data["type_raw"] == "Trap Card":
        return ["red"]
    else:
        return []

def determine_types(csv_type):
    """Monster -> summon; Spell/Trap -> backrow."""
    last_word = csv_type.strip().split(" ")[-1].lower()
    if last_word == "monster":
        return ["summon"]
    if last_word in ("spell", "trap"):
        return ["backrow"]
    return []

def calculate_stats(api_info, csv_type):
    """Return rank, dmg, def based on card type and API data."""
    last_word = csv_type.strip().split(" ")[-1].lower()

    if last_word == "monster":
        # Rank priority: level, else link
        rank = api_info["level"] if api_info["level"] is not None else api_info["link"]

        atk = api_info["atk"]
        defe = api_info["def"]

        dmg = round(atk / 1000, 3) if isinstance(atk, int) else ""
        df = round(defe / 1000, 3) if isinstance(defe, int) else ""

        return rank, dmg, df

    # Spell / Trap
    if last_word == "spell":
        return "spell", "", ""
    if last_word == "trap":
        return "trap", "", ""

    return None, "", ""

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
            types = determine_types(csv_type)

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
                "types": types
            }

            cards.append(card_obj)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(cards, out, indent=4, ensure_ascii=False)

    print(f"Complete. Exported {len(cards)} cards to {OUTPUT_JSON}.")

if __name__ == "__main__":
    main()
