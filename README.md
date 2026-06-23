# CGS set builders
a bunch of scripts to turn exported decks from different card game websites into the cgs json set format
## cgs json set format
The cgs json set format is just a json  array of card objects. The card objects have the following fields

|Field Name| Value Type|Description|
|-|-|-|
|game-id|string|unique identifier between card games|
|id|string|unique identifier between cards in one card game|
|name|string|card name|
|cost|number|required summoning resources, such as mana, energy, material, etc.|
|small-img|string|url of a small card image for fast loading|
|large-img|string|url of a large card image for closer inspection|
|rank|number\|string|relative ordering. See the rules for a deeper explanation|
|colors|string[]|card color, such as element, magic color, etc.|
|def|number|defence value, such as health, hp, resistance, shield, etc.|
|dmg|number|damage value, such as strength, attack, etc.|
|grouping|string[]|categories, cards can be a part of|
|types|string[]|more general category, mainly summon, backrow and resource|

an example card could look like this
```json
[
  {
        "id": "ygo83994646",
        "name": "4-Starred Ladybug of Doom",
        "colors": [
            "green"
        ],
        "grouping": [
            "Insect"
        ],
        "large-img": "https://images.ygoprodeck.com/images/cards/83994646.jpg",
        "small-img": "https://images.ygoprodeck.com/images/cards_small/83994646.jpg",
        "rank": 3,
        "dmg": 0.8,
        "def": 1.2,
        "cost": 0,
        "game-id": "Yu-Gi-Oh!",
        "subtype":[
            "Insect"
        ],
        "types": [
            "summon"
        ],
        "supertype": [
            "Effect",
            "Flip"
        ]
    },
]
```
For a better understanding of these fields, read the [rules document](https://docs.google.com/document/d/1I6IJgf3fNb4dPWSHXUhV4R2asfJsbsJwLMW0f1Lu2NU/edit?tab=t.0).
## supported games

|Card Game|Deck Builder|Export Instructions|
|-|-|-|
|**Magic: the Gathering** | https://moxfield.com|Download > Copy Plain Text|
|**Pokémon**|https://my.limitlesstcg.com/builder|Share > Copy as Text|
|**Yu-Hi-Oh!**|https://ygoprodeck.com/deckbuilder|Download Cube (.csv)|
## how to use
1. Download this repository
2. Navigate to where you downloaded it
3. Copy and paste the exported deck from the deck building website into the provided `input.txt` file
4. Download [uv](https://docs.astral.sh/uv/#installation) and generate an `output.json` file with the command:  
  `uv run <game-folder-name>/build.py` where `<game-folder-name>` is the folder name of where the build script of the particular game is in. (as an example: for a magic deck, use `uv run magic/build.py`)

pass in `INFO` as an argument to get more logs for debugging (`uv run <game-folder-name/build.py INFO`)
  
alternatively to uv, just call the scripts directly with your local python version. You'll figure it out, I'm sure of it :)
