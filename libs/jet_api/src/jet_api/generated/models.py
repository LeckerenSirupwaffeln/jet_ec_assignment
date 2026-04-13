# ruff: noqa

from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, Field, RootModel


class Type(StrEnum):
    Point = 'Point'


class Geometry1(BaseModel):
    type: Type
    coordinates: list[float] = Field(..., min_length=2)
    bbox: list[float] | None = Field(None, min_length=4)


class Type1(StrEnum):
    LineString = 'LineString'


class Coordinate(RootModel[list[float]]):
    root: list[float]


class Geometry2(BaseModel):
    type: Type1
    coordinates: list[Coordinate] = Field(..., min_length=2)
    bbox: list[float] | None = Field(None, min_length=4)


class Type2(StrEnum):
    Polygon = 'Polygon'


class Geometry3(BaseModel):
    type: Type2
    coordinates: list[list[Coordinate]]
    bbox: list[float] | None = Field(None, min_length=4)


class Type3(StrEnum):
    MultiPoint = 'MultiPoint'


class Geometry4(BaseModel):
    type: Type3
    coordinates: list[list[float]]
    bbox: list[float] | None = Field(None, min_length=4)


class Type4(StrEnum):
    MultiLineString = 'MultiLineString'


class Geometry5(BaseModel):
    type: Type4
    coordinates: list[list[Coordinate]]
    bbox: list[float] | None = Field(None, min_length=4)


class Type5(StrEnum):
    MultiPolygon = 'MultiPolygon'


class Geometry6(BaseModel):
    type: Type5
    coordinates: list[list[list[Coordinate]]]
    bbox: list[float] | None = Field(None, min_length=4)


class Geometry(RootModel[Geometry1 | Geometry2 | Geometry3 | Geometry4 | Geometry5 | Geometry6]):
    root: Geometry1 | Geometry2 | Geometry3 | Geometry4 | Geometry5 | Geometry6 = Field(..., title='GeoJSON Geometry')


class Rating(BaseModel):
    count: int
    starRating: float | None
    userRating: float | None


class Cuisine(BaseModel):
    name: str
    uniqueName: str


class Location(RootModel[Geometry]):
    root: Geometry


class Address(BaseModel):
    city: str
    firstLine: float
    postalCode: str
    location: Location


class Restaurant(BaseModel):
    id: str
    name: str
    uniqueName: str
    address: Address
    rating: Rating
    cuisines: list[Cuisine]


class RestaurantsDataResponse(BaseModel):
    restaurants: list[Restaurant]
