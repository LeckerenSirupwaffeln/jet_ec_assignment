from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from uritemplate import URITemplate


class Settings(BaseSettings):
    JET_UK_API_URI_TEMPLATE: str
    VALID_UK_POSTCODE: str
    EXAMPLE_JET_RESTUARANTS_DATA_PATH: str

    model_config = SettingsConfigDict(env_file="libs/jet_api/.env", env_file_required=True)

    @computed_field
    @property
    def jet_uk_api_uri_template(self) -> URITemplate:
        return URITemplate(self.JET_UK_API_URI_TEMPLATE)


@lru_cache
def get_settings() -> Settings:
    return Settings()
