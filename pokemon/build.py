import logging
import json
import re
from tcgdexsdk import TCGdex
import asyncio
import os
import sys

if "INFO" in sys.argv:
	logging.getLogger().setLevel(logging.INFO)

script_dir = os.path.dirname(os.path.abspath(__file__))

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


def buildData(card, line):
	logging.info(f"building card: {card}")
	data = {}

	data["game-id"] = "Pokemon"
	data["id"] = card.id
	data["name"] = card.name
	data["cost"] = 0

	if card.image is not None:
		data["small-img"] = card.image + "/low.webp"
		data["large-img"] = card.image + "/high.webp"
	else:
		data["small-img"] = "NONE"
		data["large-img"] = "NONE"

	
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

	if card.hp is None:
		data["def"] = ""
	else:
		data["def"] = int(card.hp) / 10


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


	data["grouping"] = []

	type_tags = []

	card_stage = getattr(card, 'stage', None)
	card_category = getattr(card, 'category', None)

	if card_stage not in (None, ''):
		type_tags.append('summon')

	if card_category == 'Trainer':
		type_tags.append('backrow')

	if card_category == 'Energy':
		type_tags.append('resource')

	data['types'] = list(dict.fromkeys(type_tags))

	# Supertype
	supertypes = []
	if "ace spec" in card.rarity.lower():
		supertypes.append('Ace SPEC')

	if card_category == 'Energy':
		if card.energyType == 'Special':
			supertypes.append("Special")
		elif card.energyType == "Normal":
			supertypes.append("Basic")
	
	if "Prism Star" in line:
		supertypes.append("Prism Star")
	
	if not (str(card.abilities) == "None"):
		supertypes.append("Rulebox")

	data["supertype"] = supertypes

	# Subtype
	subtypes = []
	if card_category == "Trainer" and card.trainerType:
		subtypes.append(card.trainerType)

	data["Subtype"] = subtypes

	return data

with open(os.path.join(script_dir, 'data/pokemonSetInfo.json'), 'r') as file:
	data = json.load(file)

tcgdex = TCGdex()

with open(os.path.join(script_dir,'..', 'input.txt'), 'r') as file:
	output = []
	output_path = os.path.join(script_dir,'..', 'output.json')

	for line in file:
		line_arr = line.strip().split()
		if len(line_arr) < 4:
			continue

		logging.info(f'processing line: {line}')

		result = next(
			(item for item in data if item.get("ptcgoCode", None) == line_arr[-2]),
			None
		)

		if result is None:
			raise NotImplementedError(f"no set: {line_arr[-2]} found in pokemonSetInfo.json for: card {line}")

		card_set = result["id"]

		try:
			card = asyncio.run(getCard(build_code(result, card_set, line_arr, False)))
		except:
			try:
				card = asyncio.run(getCard(build_code(result, card_set, line_arr, True)))
			except:
				raise ConnectionError(f"Failed to fetch card for url: {build_code(result, card_set, line_arr, True)}")

		if card is None:
			continue

		final_data = buildData(card, line)
		output.append(final_data)

	try:
		with open(output_path, 'w') as out_file:
			json.dump(output, out_file, indent=2)
		logging.info(f"-- all cards built - no errors --")
	except Exception:
		raise BaseException("couldn't write to output file :(")