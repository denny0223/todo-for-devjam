FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-cache --locked --no-dev

COPY main.py .

EXPOSE 8080

CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8080"]
