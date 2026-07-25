FROM python:3.13-slim
WORKDIR /app

# Install uv
RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

CMD ["uv", "run", "python", "-m", "apps.worker.main"]
