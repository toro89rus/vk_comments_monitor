FROM python:3.12-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /tatd_bot/

WORKDIR /tatd_bot

RUN apt-get update && apt-get install make

RUN make install

CMD ["make", "run"]
