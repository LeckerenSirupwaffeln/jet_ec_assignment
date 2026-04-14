import asyncio

from loguru import logger

from jet_api import Client
from jet_api.models import Restaurant


async def main() -> None:
    client = Client()

    async with client.stream_restaurants("SW1A 1AA") as streamer:
        async for restaurant in streamer:
            if isinstance(restaurant, Restaurant):
                logger.info(f"Just streamed: {restaurant.name}")


if __name__ == "__main__":
    asyncio.run(main())
