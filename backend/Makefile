dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

celery:
	uv run celery -A app.core.celery_app:celery_app worker --concurrency=2 --loglevel=info --pool=solo

flower:
	uv run celery -A app.core.celery_app:celery_app flower --port=5555

api:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

install_all: 
	uv sync --all-extras
	