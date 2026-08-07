FROM python:3.12-slim AS base

# Sécurité : utilisateur non-root / non-root user
RUN useradd -m riverside
# Libs système requises par rasterio/stackstac (expat) sur slim /
# EN: system libs required by rasterio/stackstac (expat) on slim images
RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
# Robustesse réseau / network resilience: retry + long timeouts (le réseau
# local est lent — torch 500MB+). EN: retry + long timeouts for slow networks.
RUN pip install --no-cache-dir --retries 5 --timeout 300 -r requirements.txt

COPY src ./src
COPY db ./db

USER riverside
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
