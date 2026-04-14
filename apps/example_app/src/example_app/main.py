import sys
import asyncio

import questionary
from rich.console import Console
from rich.table import Table
from jet_api import Client
from jet_api.models import Restaurant


CONSOLE = Console()


async def fetch_restaurants(client: Client, postcode: str):
    table = Table(title=f"Top Restaurants in {postcode}")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Name", style="magenta")

    async with client.stream_restaurants(postcode) as streamer:
        count = 0
        async for restaurant in streamer:
            if isinstance(restaurant, Restaurant):
                count += 1
                table.add_row(str(count), restaurant.name)
            
            if count >= 10:
                break
    
    CONSOLE.print(table)


async def main() -> None:
    client = Client()

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
