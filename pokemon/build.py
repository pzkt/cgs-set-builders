import json
import re
from tcgdexsdk import TCGdex
import asyncio
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

def write_log(level, msg):
	pass

def write_exception(msg):
	print(f"EXCEPTION: {msg}\n")

async def getCard(name):
	return await tcgdex.card.get(name)

def build_code(result, card_set, line_arr, padded):
	number = line_arr[-1]
	if padded is True:
		number = number.zfill(3)
	code = card_set + "-" + number
	if "prefix" in result:
		code = card_set + "-" + result["prefix"] + number
	return code


# -------------------------
# NEW NORMALIZATION RULES
# -------------------------

VALID_SUPERTYPES = {
	"Prism Star",
	"ex",
	"Lv.X",
	"EX",
	"Ace SPEC",
	"Basic",
	"Special"
}

VALID_TRAINER_SUBTYPES = {
	"Item",
	"Supporter",
	"Tool",
	"Stadium"
}


def buildData(card):
	data = {}

	data["game-id"] = "pokemon"
	data["id"] = card.id
	data["name"] = card.name
	data["cost"] = 0

	if card.image is not None:
		data["small-img"] = card.image + "/low.webp"
		data["large-img"] = card.image + "/high.webp"
	else:
		data["small-img"] = "NONE"
		data["large-img"] = "NONE"

	# -------------------------
	# Rank
	# -------------------------
	match card.stage:
		case "Basic":
			data["rank"] = 0
		case "Stage1":
			data["rank"] = 1
		case "Stage2":
			data["rank"] = 2
		case _:
			data["rank"] = "rankless"

	if card.category == "Trainer":
		data["rank"] = "trainer"

	# -------------------------
	# Colors
	# -------------------------
	types = card.types
	colors = []

	if types:
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

	if not colors:
		colors.append("colorless")

	data["colors"] = colors

	# -------------------------
	# DEF
	# -------------------------
	if card.hp is None:
		data["def"] = ""
	else:
		data["def"] = int(card.hp) / 10

	# -------------------------
	# DMG
	# -------------------------
	if card.attacks is None:
		data["dmg"] = 0
	else:
		damage_values = [str(atk.damage) for atk in card.attacks]
		damage_numbers = [
			int(re.sub(r'\D', '', damage))
			for damage in damage_values
			if re.sub(r'\D', '', damage)
		]
		data["dmg"] = max(damage_numbers) / 10 if damage_numbers else 0

	# -------------------------
	# Grouping
	# -------------------------
	data["grouping"] = []

	# -------------------------
	# Existing cube gameplay tags
	# -------------------------
	type_tags = []

	card_stage = getattr(card, 'stage', None)
	card_super = getattr(card, 'supertype', None)
	card_category = getattr(card, 'category', None)
	card_subtypes = getattr(card, 'subtypes', None) or []

	if card_stage not in (None, ''):
		type_tags.append('summon')
	elif card_super and str(card_super).lower().startswith('pok'):
		type_tags.append('summon')

	if card_category == 'Trainer' or card_super == 'Trainer':
		type_tags.append('backrow')

	if card_super == 'Energy' or card_category == 'Energy':
		type_tags.append('resource')

	data['types'] = list(dict.fromkeys(type_tags))

	# ==========================================================
	# NEW: Supertype + Subtype
	# ==========================================================

	# ---- Supertype ----
	supertypes = []
	for s in card_subtypes:
		if s in VALID_SUPERTYPES:
			supertypes.append(s)

	data["Supertype"] = list(dict.fromkeys(supertypes))

	# ---- Subtype (Trainer only) ----
	subtypes = []
	if card_super == "Trainer":
		for s in card_subtypes:
			if s in VALID_TRAINER_SUBTYPES:
				subtypes.append(s)

	data["Subtype"] = list(dict.fromkeys(subtypes))

	return data


with open(os.path.join(script_dir, 'data/pokemonSetInfo.json'), 'r') as file:
	data = json.load(file)

tcgdex = TCGdex()

with open(os.path.join(script_dir, 'data/pokemonSet.txt'), 'r') as file:
	output = []
	output_path = os.path.join(script_dir, 'pokemon.json')

	for line in file:
		line_arr = line.strip().split()
		if len(line_arr) < 4:
			continue

		result = next(
			(item for item in data if item.get("ptcgoCode", None) == line_arr[-2]),
			None
		)

		if result is None:
			exit(1)

		card_set = result["id"]

		try:
			card = asyncio.run(getCard(build_code(result, card_set, line_arr, False)))
		except:
			try:
				card = asyncio.run(getCard(build_code(result, card_set, line_arr, True)))
			except:
				write_exception(f"Failed to fetch card for line: {line.strip()}")
				card = None

		if card is None:
			continue

		final_data = buildData(card)
		output.append(final_data)

	try:
		with open(output_path, 'w') as out_file:
			json.dump(output, out_file, indent=2)
	except Exception:
		write_exception('ERROR writing output file')