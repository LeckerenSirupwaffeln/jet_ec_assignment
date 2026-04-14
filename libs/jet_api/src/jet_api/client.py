import importlib.resources
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from loguru import logger
from openapi_core import OpenAPI

from .config import get_settings
from .generated.models import (
    RestaurantsDataResponse,
)
from .pydantic_streamer import PydanticStreamer


class Client:
    """An API client dynamically configured via an OpenAPI specification."""

    def __init__(self) -> None:
        logger.info("Initializing client...")
        spec_traversable = get_settings().OPENAPI_SPEC_TRAVERSABLE

        logger.debug("Loading OpenAPI spec...")
        self.openapi = None
        with importlib.resources.as_file(spec_traversable) as file_path:
            self.openapi = OpenAPI.from_file_path(str(file_path))

        logger.debug("Loading base url...")
        servers: list[dict[str, Any]] = self.openapi.spec.get("servers", [])
        if not servers:
            raise ValueError("Found no valid servers in loaded OpenAPI spec")

        self.base_url = servers[0]["url"].rstrip("/")

        logger.debug("Loading ops...")
        self.ops = {
            details["operationId"]: (path, method.upper())
            for path, methods in self.openapi.spec.get("paths", {}).items()
            for method, details in methods.items()
            if "operationId" in details
        }

        if not self.ops:
            raise ValueError("Found no valid ops in loaded OpenAPI spec")

        self.op_get_restaurants_by_postcode = self.ops.get(
            "getRestaurantsByPostcode", None
        )
        if not self.op_get_restaurants_by_postcode:
            raise ValueError(
                'Found no valid op where "operationId" is "getRestaurantsByPostcode"'
            )

        logger.info("Client initialized")

    @asynccontextmanager
    async def stream_restaurants(
        self, postcode: str
    ) -> AsyncIterator[PydanticStreamer[RestaurantsDataResponse]]:
        if self.op_get_restaurants_by_postcode is None:
            raise ValueError("Operation not initialized")

        path_template, method = self.op_get_restaurants_by_postcode
        full_url = f"{self.base_url}{path_template.format(postcode=postcode)}"

        logger.debug(f"Returning streaming request to {full_url}")

        async with (
            httpx.AsyncClient() as client,
            client.stream(method, full_url) as response,
        ):
            response.raise_for_status()
            streamer = PydanticStreamer(
                response=response,
                schema=RestaurantsDataResponse,
                stream_keys=["restaurants"],
            )
            yield streamer

    # end def stream_restaurants(...)
