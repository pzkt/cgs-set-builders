import json
import re
from tcgdexsdk import TCGdex
import asyncio

def write_log(level, msg):
    #print(f"{level}: {msg}\n")
    pass

def write_exception(msg):
    print(f"EXCEPTION: {msg}\n")

async def getCard(name):
    return await tcgdex.card.get(name) 

def build_code(result, card_set, line_arr, padded):
    number = line_arr[-1]
    if (padded is True):
        number = number.zfill(3)
    code = card_set + "-" + number
    if "prefix" in result:   
        code = card_set + "-" + result["prefix"] + number
    return code

def buildData(card):
    data = {}
    # game id
    data["game-id"] = "pokemon"

    # id
    data["id"] = card.id

    # name
    data["name"] = card.name

    # cost
    data["cost"] = 0

    if card.image is not None:
        # small image
        data["small-img"] = card.image + "/low.webp"

        # large image
        data["large-img"] = card.image + "/high.webp"
    else:
        data["small-img"] = "NONE"
        data["large-img"] = "NONE"

    # rank
    match card.stage:
        case "Basic":
            data["rank"] = 0
        case "Stage1":
            data["rank"] = 1
        case "Stage2":
            data["rank"] = 2
        case _:
            data["rank"] = "rankless"

    if(card.category == "Trainer"):
        data["rank"] = "trainer"

    # color
    types = card.types
    colors = []

    if types is None:
        data["colors"] = []
    else:
        for color in types:
            match color:
                case "Fire" | "Fighting":
                    colors.append("red")
                case "Water":
                    colors.append("blue")
                case "Lightning":
                    colors.append("white")
                case "Grass":
                    colors.append("green")
                case "Metal" | "Darkness":
                    colors.append("black")
                case "Psychic" | "Fairy":
                    colors.append("purple")
                case "Dragon":
                    colors.append("gold")
                case "Colorless":
                    colors.append("colorless")
    if len(colors) == 0:
        colors.append("colorless")
    data["colors"] = colors

    # defensive stat
    if card.hp is None:
        data["def"] = ""
    else:
        data["def"] = int(card.hp) / 10

    # attack stat
    if card.attacks is None:
        data["dmg"] = 0
    else:
        damage_values = [str(atk.damage) for atk in card.attacks]
        damage_numbers = [int(re.sub(r'\D', '', damage)) for damage in damage_values if re.sub(r'\D', '', damage)]
        data["dmg"] = max(damage_numbers) / 10 if damage_numbers else 0
    
    # grouping
    data["grouping"] = []

    # types (summon/backrow/resource)
    type_tags = []
    # treat cards with a stage or Pokémon supertype as summon
    card_stage = getattr(card, 'stage', None)
    card_super = getattr(card, 'supertype', None)
    card_category = getattr(card, 'category', None)
    card_subtypes = getattr(card, 'subtypes', None) or []
    if card_stage not in (None, ''):
        type_tags.append('summon')
    elif card_super and str(card_super).lower().startswith('pok'):
        type_tags.append('summon')

    # trainer/backrow detection
    if card_category == 'Trainer' or (card_super == 'Trainer') or any(s in ('Item', 'Supporter', 'Tool', 'Stadium') for s in card_subtypes):
        type_tags.append('backrow')

    # energy/resource detection
    if card_super == 'Energy' or card_category == 'Energy' or any('Energy' in str(s) for s in card_subtypes):
        type_tags.append('resource')

    # remove duplicates and set
    data['types'] = list(dict.fromkeys(type_tags))

    return data

with open('data/pokemonSetInfo.json', 'r') as file:
    data = json.load(file)

tcgdex = TCGdex()

with open('data/pokemonSet.txt', 'r') as file:
    count = 0
    output = []
    output_path = 'pokemon.json'
    for line in file:
        line_arr = line.strip().split()
        if(len(line_arr) < 4):
            continue
        #if(not line_arr[-1].isdigit()):
        #    write_log('ERROR', f"Letter in card number: {line.strip()}")
        #    exit(1)
        result = next((item for item in data if item.get("ptcgoCode", None) == line_arr[-2]), None)

        if result == None:
            write_log('ERROR', f"No ptcgoCode match for line: {line_arr}")
            exit(1)
        card_set = result["id"]
        try:
            card = asyncio.run(getCard(build_code(result, card_set, line_arr,False)))
        except:
            try:
                card = asyncio.run(getCard(build_code(result, card_set, line_arr,True)))
            except:
                write_exception(f"Failed to fetch card for line: {line.strip()}")
                card = None
        if card is None:
            continue
        final_data = buildData(card)
        output.append(final_data)
        write_log('INFO', f"added {final_data['name']}")
    # write collected results to file
    try:
        with open(output_path, 'w') as out_file:
            json.dump(output, out_file, indent=2)
        write_log('INFO', f"Wrote {len(output)} cards to {output_path}")
    except Exception:
        write_exception('ERROR writing output file')