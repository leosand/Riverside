FROM python:3.12-slim AS base

# Sécurité : utilisateur non-root / non-root user
RUN useradd -m riverside
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY db ./db

USER riverside
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
