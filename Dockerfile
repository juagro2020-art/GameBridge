FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    "sqlalchemy>=2.0" \
    greenlet \
    aiosqlite \
    asyncpg \
    psycopg2-binary \
    alembic \
    pydantic \
    pydantic-settings \
    httpx \
    jinja2 \
    python-multipart \
    aiogram \
    pillow \
    pytest \
    pytest-asyncio

COPY . .

RUN mkdir -p uploads static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
