from tcgdexsdk import TCGdex, Query
import asyncio

dex = TCGdex()

async def main():
    print(await dex.card.get("ecard2-95a"))
    #print(await dex.card.list(Query().equal("name", "Feraligatr")))

asyncio.run(main())