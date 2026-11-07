FROM python:3.12-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

# та же версия uv, что в CI и локально
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

COPY . /tatd_bot/

WORKDIR /tatd_bot

RUN apt-get update && apt-get install make

RUN uv sync --locked --no-dev

CMD ["make", "run"]
