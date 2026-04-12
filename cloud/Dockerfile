FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    proj-bin \
    proj-data \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY cloud ./cloud
COPY database ./database
COPY processed ./processed
COPY database ./schema.sql

EXPOSE 8080

CMD ["sh", "-c", "uvicorn cloud.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]