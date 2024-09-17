FROM python:3.10-slim AS builder
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["fastapi", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
