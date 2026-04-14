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
    """
    An API client dynamically configured via an OpenAPI specification.

    This client provides a high-level interface to stream data from the API
    automatically resolving endpoints and base URLs from a local OpenAPI
    specification file.
    """

    def __init__(self) -> None:
        """
        Initializes the Client by loading the OpenAPI spec and mapping operations.

        The initialization process retrieves the spec location from application
        settings, validates that the spec contains at least one server, and
        pre-maps the 'getRestaurantsByPostcode' operation for faster lookups.

        Raises:
            ValueError: If the OpenAPI spec is missing servers, contains no
                valid operations, or is missing the required
                "getRestaurantsByPostcode" operationId.
        """

        logger.info("Initializing client...")
        spec_traversable = get_settings().OPENAPI_SPEC_TRAVERSABLE

        logger.debug("Loading OpenAPI spec...")
        self._openapi = None
        with importlib.resources.as_file(spec_traversable) as file_path:
            self._openapi = OpenAPI.from_file_path(str(file_path))

        logger.debug("Loading base url...")
        servers: list[dict[str, Any]] = self._openapi.spec.get("servers", [])
        if not servers:
            raise ValueError("Found no valid servers in loaded OpenAPI spec")

        self._base_url = servers[0]["url"].rstrip("/")

        logger.debug("Loading ops...")
        self._ops = {
            details["operationId"]: (path, method.upper())
            for path, methods in self._openapi.spec.get("paths", {}).items()
            for method, details in methods.items()
            if "operationId" in details
        }

        if not self._ops:
            raise ValueError("Found no valid ops in loaded OpenAPI spec")

        self.op_get_restaurants_by_postcode = self._ops.get(
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
        """
        Streams restaurant data from the API for a specific postcode.

        This method opens an asynchronous HTTP stream to the resolved endpoint
        and yields a PydanticStreamer. The streamer handles the incremental
        parsing of the JSON response, specifically looking for the "restaurants" key.

        Args:
            postcode: A valid UK postcode string (e.g., "NW1 8NZ").

        Yields:
            An instance of PydanticStreamer configured to parse RestaurantsDataResponse objects.

        Raises:
            ValueError: If the client was not initialized correctly with
                the required operation.
            httpx.HTTPStatusError: If the API returns a non-success status code.

        Example:
            ```python
            client = Client()
            async with client.stream_restaurants("NW1 8NZ") as streamer:
                async for restaurant in streamer:
                    # "restaurant" is yielded as a validated Pydantic model
                    print(f"Found: {restaurant.name}")
            ```
        """

        if self.op_get_restaurants_by_postcode is None:
            raise ValueError("Operation not initialized")

        path_template, method = self.op_get_restaurants_by_postcode
        full_url = f"{self._base_url}{path_template.format(postcode=postcode)}"

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
