FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main --no-interaction

COPY . .

EXPOSE 8000

# Migrate then seed the proprietary content (both idempotent — safe on every
# deploy) before serving. The seeds populate the curated Rowling topics and the
# maths problems into this app's `thinkingify` schema.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seeds.topics && python -m app.seeds.math_problems && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
