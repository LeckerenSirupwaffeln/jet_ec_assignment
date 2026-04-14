# ruff: noqa

from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, Field, RootModel


class Type(StrEnum):
    Point = "Point"


class GeoJSONPoint(BaseModel):
    type: Type
    coordinates: list[float] = Field(..., min_length=2)
    bbox: list[float] | None = Field(None, min_length=4)


class Type1(StrEnum):
    LineString = "LineString"


class Coordinate(RootModel[list[float]]):
    root: list[float] = Field(..., min_length=2)


class GeoJSONLineString(BaseModel):
    type: Type1
    coordinates: list[Coordinate] = Field(..., min_length=2)
    bbox: list[float] | None = Field(None, min_length=4)


class Type2(StrEnum):
    Polygon = "Polygon"


class Coordinate1Item(RootModel[list[float]]):
    root: list[float] = Field(..., min_length=2)


class Coordinate1(RootModel[list[Coordinate1Item]]):
    root: list[Coordinate1Item] = Field(..., min_length=4)


class GeoJSONPolygon(BaseModel):
    type: Type2
    coordinates: list[Coordinate1]
    bbox: list[float] | None = Field(None, min_length=4)


class Type3(StrEnum):
    MultiPoint = "MultiPoint"


class Coordinate2(RootModel[list[float]]):
    root: list[float] = Field(..., min_length=2)


class GeoJSONMultiPoint(BaseModel):
    type: Type3
    coordinates: list[Coordinate2]
    bbox: list[float] | None = Field(None, min_length=4)


class Type4(StrEnum):
    MultiLineString = "MultiLineString"


class Coordinate3Item(RootModel[list[float]]):
    root: list[float] = Field(..., min_length=2)


class Coordinate3(RootModel[list[Coordinate3Item]]):
    root: list[Coordinate3Item] = Field(..., min_length=2)


class GeoJSONMultiLineString(BaseModel):
    type: Type4
    coordinates: list[Coordinate3]
    bbox: list[float] | None = Field(None, min_length=4)


class Type5(StrEnum):
    MultiPolygon = "MultiPolygon"


class Coordinate4Item(RootModel[list[float]]):
    root: list[float] = Field(..., min_length=2)


class Coordinate4(RootModel[list[Coordinate4Item]]):
    root: list[Coordinate4Item] = Field(..., min_length=4)


class GeoJSONMultiPolygon(BaseModel):
    type: Type5
    coordinates: list[list[Coordinate4]]
    bbox: list[float] | None = Field(None, min_length=4)


class Geometry(
    RootModel[
        GeoJSONPoint
        | GeoJSONLineString
        | GeoJSONPolygon
        | GeoJSONMultiPoint
        | GeoJSONMultiLineString
        | GeoJSONMultiPolygon
    ]
):
    root: (
        GeoJSONPoint
        | GeoJSONLineString
        | GeoJSONPolygon
        | GeoJSONMultiPoint
        | GeoJSONMultiLineString
        | GeoJSONMultiPolygon
    ) = Field(..., title="GeoJSON Geometry")


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
    firstLine: str
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
