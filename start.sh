#!/bin/bash

# 🚀 Script de lancement automatique de la plateforme d'apprentissage

echo "🎓 Lancement de la plateforme d'apprentissage..."
echo ""

# Vérifier que les clés API sont configurées
if ! grep -q "sk-proj-" .env 2>/dev/null; then
    echo "⚠️  ATTENTION: Veuillez configurer vos clés API dans le fichier .env"
    echo "   Copiez .env.example vers .env et ajoutez vos clés"
    exit 1
fi

if ! grep -q "VITE_OPENAI_API_KEY" frontend/.env 2>/dev/null; then
    echo "⚠️  ATTENTION: Veuillez configurer VITE_OPENAI_API_KEY dans frontend/.env"
    echo "   Copiez frontend/.env.example vers frontend/.env et ajoutez votre clé"
    exit 1
fi

echo "✅ Configuration des clés API détectée"
echo ""

# Fonction pour arrêter tous les processus en cas d'interruption
cleanup() {
    echo ""
    echo "🛑 Arrêt des serveurs..."
    kill $RAG_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Vérifier les dépendances Python
echo "📦 Vérification des dépendances Python..."
if ! python3 -c "import flask, qdrant_client, openai" 2>/dev/null; then
    echo "⚠️  Installation des dépendances Python..."
    pip3 install -r requirements.txt
fi

# Vérifier les dépendances Node
echo "📦 Vérification des dépendances Node..."
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Installation des dépendances Node..."
    cd frontend && npm install && cd ..
fi

echo ""
echo "🚀 Démarrage des serveurs..."
echo ""

# Lancer le serveur RAG en arrière-plan
echo "1️⃣  Lancement du serveur RAG (port 5000)..."
python3 rag_server.py > logs_rag.txt 2>&1 &
RAG_PID=$!
sleep 3

# Vérifier si le serveur RAG a démarré
if ! ps -p $RAG_PID > /dev/null; then
    echo "❌ Erreur: Le serveur RAG n'a pas démarré. Consultez logs_rag.txt"
    exit 1
fi

echo "✅ Serveur RAG démarré (PID: $RAG_PID)"

# Lancer le frontend en arrière-plan
echo "2️⃣  Lancement du frontend React (port 5173)..."
cd frontend
npm run dev > ../logs_frontend.txt 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 5

# Vérifier si le frontend a démarré
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ Erreur: Le frontend n'a pas démarré. Consultez logs_frontend.txt"
    kill $RAG_PID 2>/dev/null
    exit 1
fi

echo "✅ Frontend démarré (PID: $FRONTEND_PID)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Plateforme lancée avec succès !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Serveur RAG:     http://localhost:5000"
echo "📍 Application web: http://localhost:5173"
echo ""
echo "📝 Logs disponibles dans:"
echo "   - logs_rag.txt"
echo "   - logs_frontend.txt"
echo ""
echo "🌐 Ouvrez votre navigateur sur: http://localhost:5173"
echo ""
echo "⌨️  Appuyez sur Ctrl+C pour arrêter tous les serveurs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Attendre indéfiniment (les processus tournent en arrière-plan)
wait
