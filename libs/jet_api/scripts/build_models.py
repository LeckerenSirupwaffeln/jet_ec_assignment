import importlib.resources
import sys
from pathlib import Path

from datamodel_code_generator import (
    InputFileType,
    PythonVersion,
    generate,
)
from datamodel_code_generator.format import Formatter
from loguru import logger
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename

from jet_api.config import get_settings

_REPO_ROOT = Path(__file__).resolve().parent.parent
_OUTPUT_DIR = _REPO_ROOT / "src" / "jet_api" / "generated"
_TARGET_PYTHON_VERSION = PythonVersion(
    f"{sys.version_info.major}.{sys.version_info.minor}"
)


def main() -> None:
    logger.info("Loading settings...")
    settings = get_settings()
    spec_traversable = settings.OPENAPI_SPEC_TRAVERSABLE

    logger.info("Loading OpenAPI spec file...")
    spec_dict = None
    with importlib.resources.as_file(spec_traversable) as file_path:
        spec_dict, _ = read_from_filename(str(file_path))

    logger.info("Validating spec file...")
    validate_spec(spec_dict)

    logger.info(f"Validating output dir: {_OUTPUT_DIR}")
    if not _OUTPUT_DIR.is_dir():
        raise ValueError(f"Output directory {_OUTPUT_DIR} is not a valid directory")

    logger.info("Generating Pydantic models")
    generate(
        input_=spec_traversable.read_text(),
        input_file_type=InputFileType.OpenAPI,
        output=_OUTPUT_DIR / "models.py",
        use_schema_description=True,
        use_title_as_name=True,
        field_constraints=True,
        use_standard_collections=True,
        target_python_version=_TARGET_PYTHON_VERSION,
        allow_remote_refs=True,
        custom_file_header="# ruff: noqa\n",
        formatters=[Formatter.RUFF_FORMAT, Formatter.RUFF_CHECK],
    )

    logger.info(f"Successfully built & stored models.py in {_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
