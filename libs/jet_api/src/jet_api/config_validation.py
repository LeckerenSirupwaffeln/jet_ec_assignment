from importlib import resources
from importlib.resources.abc import Traversable
from typing import Annotated

from pydantic import BeforeValidator


def _validate_and_create_traversable_resource(
    resource_name: str | Traversable,
) -> Traversable:
    if isinstance(resource_name, Traversable):
        return resource_name

    resource = resources.files(__package__).joinpath("resources", resource_name)
    if not resource.is_file():
        raise ValueError(f"Resource {resource} is not a valid file")

    return resource


type TraversableResource = Annotated[
    Traversable, BeforeValidator(_validate_and_create_traversable_resource)
]
