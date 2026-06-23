from tcgdexsdk import TCGdex, Query
import asyncio

dex = TCGdex()

async def main():
    print(await dex.card.get("me03-080"))
    #print(await dex.card.list(Query().equal("name", "Poké Ball")))

asyncio.run(main())