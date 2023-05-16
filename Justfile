default: format lint

format: ssort isort black

ssort:
    python -m ssort .

isort:
    python -m isort .

black:
    python -m black .

lint: ruff pyright

ruff:
    python -m ruff .

pyright:
    python -m pyright .
