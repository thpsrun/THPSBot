# syntax=docker/dockerfile:1
FROM python:3.13.5-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends  build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd -U app_user && install -d -m 0755 -o app_user -g app_user /app

WORKDIR /app
USER app_user:app_user

COPY --chown=app_user:app_user . .

CMD [ "python3", "-m", "thpsbot.main" ]