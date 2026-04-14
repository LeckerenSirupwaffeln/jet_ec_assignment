import sys
import asyncio

import questionary
from rich.console import Console
from rich.table import Table
from jet_api import Client
from jet_api.models import Restaurant
from loguru import logger

CONSOLE = Console()


def add_restaurant_row(table: Table, restaurant: Restaurant, count: int) -> None:
    cuisines_list = ", ".join([c.name for c in restaurant.cuisines])

    rating_val = restaurant.rating.starRating
    rating_str = str(rating_val) if rating_val is not None else "N/A"

    address = restaurant.address
    full_address = f"{address.firstLine}, {address.city}, {address.postalCode}"
    logger.debug(full_address)

    table.add_row(
        str(count),
        restaurant.name,
        cuisines_list,
        rating_str,
        full_address
    )


async def fetch_restaurants(client: Client, postcode: str):
    table = Table(
        title=f"Top Restaurants in {postcode}",
        show_lines=True, 
        expand=True
    )
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Cuisines", style="yellow")
    table.add_column("Rating", style="green")
    table.add_column("Address", style="cyan", overflow="fold")

    async with client.stream_restaurants(postcode) as streamer:
        count = 0
        async for restaurant in streamer:
            if isinstance(restaurant, Restaurant):
                count += 1
                add_restaurant_row(table, restaurant, count)
            
            if count >= 10:
                break
    
    CONSOLE.print(table)


async def main() -> None:
    client = Client()

    logger.debug("Starting app...")
    while True:
        postcode = await questionary.text("Enter a postcode:").ask_async()

        if not postcode:
            break

        await fetch_restaurants(client, postcode)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        CONSOLE.print("\n[bold red]Aborted by user.[/]")
        sys.exit(0)
