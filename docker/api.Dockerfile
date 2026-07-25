FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY apps/api ./apps/api
COPY alembic.ini ./
COPY migrations ./migrations

CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
