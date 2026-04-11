test:
    uv run tox -e py312

lint:
    uv run tox -e lint

typecheck:
    uv run tox -e typecheck

build-docs:
    uv run tox -e build-docs
