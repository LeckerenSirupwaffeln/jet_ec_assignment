import json
from pathlib import Path

import httpx
from loguru import logger

from jet_api.config import get_settings
from jet_api.exceptions import ConfigurationError


def main() -> None:
    logger.debug("Loading settings...")
    settings = get_settings()

    logger.debug("Preparing script...")
    jet_uk_api_uri_template = settings.jet_uk_api_uri_template
    valid_uk_postcode = settings.VALID_UK_POSTCODE
    target_uri = jet_uk_api_uri_template.expand(postcode=valid_uk_postcode)

    target_path = Path(settings.EXAMPLE_JET_RESTUARANTS_DATA_PATH)
    if not target_path.suffix:
        raise ConfigurationError(f"Target is not a valid file path: {target_path}")

    if not target_path.parent.is_dir():
        raise NotADirectoryError(f"Target directory missing: {target_path.parent}")

    logger.info(f"Trying to fetch JET restaurant data from {target_uri}...")
    response = None
    try:
        response = httpx.get(target_uri)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        e.add_note(f"Response Body: {e.response.text[:200]}")
        raise
    except httpx.RequestError:
        raise

    try:
        _ = response.json()
    except (json.JSONDecodeError, httpx.ResponseNotRead) as e:
        e.add_note(f"Response Body: {response.text[:200]}")
        raise

    target_path.write_text(response.text)
    logger.info("Succesfully fetched JET restaurant data")


if __name__ == "__main__":
    main()
