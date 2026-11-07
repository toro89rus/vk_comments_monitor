FROM python:3.12-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

# та же версия uv, что в CI и локально
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tatd_bot

# зависимости — отдельным слоем: пересобирается, только когда меняется uv.lock
COPY pyproject.toml uv.lock /tatd_bot/

RUN uv sync --locked --no-dev --no-install-project

COPY . /tatd_bot/

RUN uv sync --locked --no-dev

CMD ["make", "run"]
