# Dockerfile pour backend FastAPI BrainStormIA
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code source
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p data/uploads data/context

# Exposer le port FastAPI
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "src.web.app_fastapi:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
