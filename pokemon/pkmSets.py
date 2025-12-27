import json
import csv

with open('data/pokemonSetInfo.json', 'r') as file:
    data = json.load(file)

with open('data/pokemonSet.txt', 'r') as file:
    count = 0
    for line in file:
        line_arr = line.strip().split()
        if(len(line_arr) < 4):
            continue
        result = next((item for item in data if item.get("ptcgoCode", None) == line_arr[-2]), None)
        if result == None:
            print("ERROR ", line_arr)
        card_set = result["id"]

        with open("data/pokemonTCG.csv", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            
            found = False
            for row in reader:
                if(row["id"] == card_set + "-" + line_arr[-1]):
                    print(row["name"] + " - " + row["large_image_source"])
                    found = True
            if(not found):
                print("ERROR - " + card_set + "-" + line_arr[-1] + " - " + line)
        
