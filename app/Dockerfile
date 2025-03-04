FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install --no-cache-dir -r requirements.txt

COPY app/src/* ./src/
