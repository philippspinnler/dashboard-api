FROM python:3.12-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev
RUN uv pip freeze > requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y locales-all

COPY . .
EXPOSE 8100
ENV PYTHONUNBUFFERED=1

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8100"]
