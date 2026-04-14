import importlib.resources
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from loguru import logger
from openapi_core import OpenAPI, validate_request
from openapi_core.datatypes import RequestParameters
from openapi_core.protocols import Request

from .config import get_settings
from .generated.models import (
    RestaurantsDataResponse,
)
from .pydantic_streamer import PydanticStreamer


class HttpxOpenAPIAdapter(Request):
    """Adapts an httpx.Request to perfectly match the openapi_core Request protocol."""

    def __init__(self, request: httpx.Request) -> None:
        self._request = request

        self.parameters = RequestParameters(
            query=dict(request.url.params),
            header=dict(request.headers),
            cookie={},
            path={},
        )

    @property
    def host_url(self) -> str:
        port_str = f":{self._request.url.port}" if self._request.url.port else ""
        return f"{self._request.url.scheme}://{self._request.url.host}{port_str}"

    @property
    def path(self) -> str:
        return self._request.url.path

    @property
    def method(self) -> str:
        return self._request.method.lower()

    @property
    def body(self) -> bytes | None:
        return self._request.content if hasattr(self._request, "content") else b""

    @property
    def content_type(self) -> str:
        content_type_header = str(
            self._request.headers.get("content-type", "application/json")
        )
        return content_type_header.split(";")[0]


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

        self._op_get_restaurants_by_postcode = self._ops.get(
            "getRestaurantsByPostcode", None
        )
        if not self._op_get_restaurants_by_postcode:
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

        if self._openapi is None:
            raise ValueError("OpenAPI spec not initialized")

        if self._op_get_restaurants_by_postcode is None:
            raise ValueError("Operation not initialized")

        path_template, method = self._op_get_restaurants_by_postcode
        full_url = f"{self._base_url}{path_template.format(postcode=postcode)}"

        logger.debug("Validating request according to OpenAPI specs")
        request = httpx.Request(method, full_url)
        validate_request(HttpxOpenAPIAdapter(request), spec=self._openapi.spec)

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
