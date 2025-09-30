FROM python:3.12-slim

LABEL authors="kung_fu_stalin"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /bot

COPY . /bot

RUN python3 -m uv sync

CMD ["/bot/.venv/bin/python", "main.py"]
