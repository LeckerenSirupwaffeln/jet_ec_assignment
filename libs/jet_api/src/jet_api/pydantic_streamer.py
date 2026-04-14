import types
from collections.abc import (
    AsyncIterable,
    AsyncIterator,
    Generator,
    Sequence,
)
from typing import (
    Any,
    Union,
    cast,
    get_args,
    get_origin,
)

import httpx
import ijson  # type: ignore[import-untyped]
from pydantic import BaseModel


class AsyncStreamReader:
    """
    Wraps an async iterable into an async file-like object with a read() method.

    This utility is primarily used to provide a compatibility layer for libraries
    (like ijson) that require a "read()" interface when consuming data from
    asynchronous sources like "httpx" response streams.
    """

    def __init__(self, async_iterable: AsyncIterable[bytes]):
        """
        Initializes the reader with an asynchronous source of bytes.

        Args:
            async_iterable: An asynchronous iterable (e.g., a response byte stream)
                yielding byte chunks.
        """

        self._iterator = aiter(async_iterable)
        self._buffer = bytearray()

    async def read(self, n: int = -1) -> bytes:
        """
        Reads up to n bytes from the stream asynchronously.

        If the internal buffer is empty, it awaits the next chunk from the
        source iterable.

        Args:
            n: The number of bytes to read. If -1 (default), reads until
                the stream is exhausted.

        Returns:
            The bytes read from the stream. Returns an empty byte string
            to signal End of File (EOF).
        """

        while not self._buffer:
            try:
                chunk = await anext(self._iterator)
                self._buffer.extend(chunk)
            except StopAsyncIteration:
                return b""  # Signal true EO

        if n == -1:
            result = bytes(self._buffer)
            self._buffer.clear()
            return result

        result = bytes(self._buffer[:n])
        del self._buffer[:n]
        return result


class PydanticStreamer[T: BaseModel]:
    """
    A streaming parser that yields validated Pydantic models from a JSON stream.

    This class leverages "ijson" to perform "incremental" parsing, allowing
    the application to process individual items in a large JSON array as they
    arrive over the network, rather than waiting for the entire response body.

    Type Args:
        T: The Pydantic BaseModel class representing the full response schema.
    """

    def __init__(
        self, response: httpx.Response, schema: type[T], stream_keys: Sequence[str]
    ) -> None:
        """
        Initializes the streamer and inspects the schema for target model types.

        The initializer performs introspection on the provided Pydantic schema
        to determine the inner types of the fields specified in "stream_keys".
        This ensures that individual items can be validated correctly during
        the streaming process.

        Args:
            response: The active httpx response object (usually from a stream).
            schema: The Pydantic model class for the total response.
            stream_keys: A list of field names in the schema that contain
                lists of items to be yielded individually.

        Raises:
            ValueError: If a key in "stream_keys" is not present in the schema.
            TypeError: If a specified field lacks the necessary type annotations
                to determine the item type.
        """

        self.response = response
        self.schema = schema

        self._final_data: dict[str, Any] = {}
        self.stream_models: dict[str, type[BaseModel]] = {}

        for key in stream_keys:
            if key not in schema.model_fields:
                raise ValueError(
                    f'Invalid stream_key "{key}". Valid keys: {list(schema.model_fields)}'
                )

            annotation = schema.model_fields[key].annotation
            if annotation is None:
                raise TypeError(f"Field {key} lacks a type annotation")

            if get_origin(annotation) in (Union, types.UnionType):
                for arg in get_args(annotation):
                    if get_origin(arg) is list:
                        annotation = arg
                        break

            extracted_type = get_args(annotation)[0]
            self.stream_models[key] = cast(type[BaseModel], extracted_type)

    async def __aiter__(self) -> AsyncIterator[BaseModel]:
        stream_reader = AsyncStreamReader(self.response.aiter_bytes())

        parser = ijson.parse_async(stream_reader)
        builder = ijson.ObjectBuilder()

        async for prefix, event, value in parser:
            builder.event(event, value)

            if event == "end_map" and prefix.endswith(".item"):
                field_name = prefix[:-5]  # remove ".item" to get the field name

                if field_name in self.stream_models:
                    model_class = self.stream_models[field_name]
                    raw_item = builder.value[field_name][-1]

                    yield model_class.model_validate(raw_item)

        self._final_data = builder.value

    def __await__(self) -> Generator[Any, None, T]:
        return self._consume().__await__()

    async def _consume(self) -> T:
        async for _ in self:
            pass  # Exhaust the stream fully

        return self.schema.model_validate(self._final_data)
