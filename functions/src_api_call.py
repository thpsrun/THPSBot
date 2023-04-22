import aiohttp

async def main(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception(0)
                response = await resp.json()
                return response["data"]
        except aiohttp.ClientError as e:
            if isinstance(e, aiohttp.ClientConnectionError):
                raise Exception(1)
            else:
                raise Exception(2)
