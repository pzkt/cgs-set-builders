import json
import requests
import re
import os
import time

headers = {
    'User-Agent': 'CardGameSingularityApp',
    'Accept':'*/*'
}

r = requests.get("https://api.scryfall.com/cards/named?exact=Aegis%20of%20the%20Gods&set=jou&collector_number=1", headers=headers)
print(r.json())