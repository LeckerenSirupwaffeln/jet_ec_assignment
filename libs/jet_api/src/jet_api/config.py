from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from .config_validation import (
    TraversableResource,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="libs/jet_api/.env")

    OPENAPI_SPEC_TRAVERSABLE: TraversableResource


@lru_cache
def get_settings() -> Settings:
    return Settings()
