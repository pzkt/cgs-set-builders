from tcgdexsdk import TCGdex, Query
import asyncio

dex = TCGdex()

async def main():
    print(await dex.card.get("sm7.5-24"))
    #print(await dex.card.list(Query().equal("name", "Feraligatr")))

asyncio.run(main())