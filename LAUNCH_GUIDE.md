# 🚀 Guide de Lancement - Plateforme d'Apprentissage

## 📋 Prérequis

Vous avez déjà installé :
- ✅ Python 3.13.5
- ✅ Node.js v22.16.0

## 🔑 Étape 1 : Configuration des clés API

### 1.1 Fichier .env principal (racine du projet)

Le fichier `.env` existe déjà. Vérifiez qu'il contient :

```bash
OPENAI_API_KEY=sk-proj-your-api-key-here
ANAM_API_KEY=your-anam-api-key-here
```

**Où obtenir ces clés ?**
- **OpenAI API Key** : https://platform.openai.com/api-keys
- **ANAM API Key** : https://www.anam.ai/ (pour l'avatar vocal)

### 1.2 Fichier .env frontend

Créez le fichier `frontend/.env` :

```bash
cd frontend
cp .env.example .env
```

Puis éditez `frontend/.env` et ajoutez votre clé OpenAI :

```bash
VITE_OPENAI_API_KEY=sk-proj-your-api-key-here
```

## 📦 Étape 2 : Installation des dépendances

### 2.1 Backend Python (Serveur RAG)

```bash
# À la racine du projet
cd /Users/margauxloncour/Desktop/goinfre/Brainstorm_agent

# Installer les dépendances Python
pip3 install -r requirements.txt
```

### 2.2 Frontend React

```bash
# Aller dans le dossier frontend
cd frontend

# Installer les dépendances Node
npm install
```

## 🎬 Étape 3 : Lancement du projet

Vous devez lancer **3 terminaux** en parallèle :

### Terminal 1 : Serveur RAG (Backend)
```bash
cd /Users/margauxloncour/Desktop/goinfre/Brainstorm_agent
python3 rag_server.py
```

✅ **Le serveur démarre sur :** `http://localhost:5000`

Vous devriez voir :
```
🚀 RAG Server starting...
📚 Collection: documents
🤖 Embedding Model: OpenAI text-embedding-3-small
📊 Vector size: 1536
🔑 OpenAI API Key: ✓ Set
```

### Terminal 2 : Frontend (Interface React)
```bash
cd /Users/margauxloncour/Desktop/goinfre/Brainstorm_agent/frontend
npm run dev
```

✅ **L'interface démarre sur :** `http://localhost:5173`

Vous devriez voir :
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Terminal 3 : Serveur de fichiers (optionnel - si nécessaire)
```bash
cd /Users/margauxloncour/Desktop/goinfre/Brainstorm_agent
python3 server.py
```

## 🌐 Étape 4 : Accéder à l'application

Ouvrez votre navigateur et allez sur :

**👉 http://localhost:5173**

## 📚 Étape 5 : Utiliser la plateforme

### 1. **Définir vos objectifs d'apprentissage**
   - Décrivez ce que vous voulez apprendre
   - Exemple : "Je suis en terminale scientifique, j'ai des difficultés en mathématiques..."

### 2. **Uploader vos cours** (optionnel)
   - Glissez-déposez vos PDF, DOCX, TXT, MD
   - Le professeur pourra référencer ces documents pendant la leçon

### 3. **Sélectionner le professeur**
   - Cliquez sur "Professeur Martin" 👨‍🏫

### 4. **Démarrer la leçon**
   - Cliquez sur "Démarrer la leçon"
   - Parlez avec le professeur via votre micro
   - Posez vos questions, demandez des explications

### 5. **Terminer et sauvegarder**
   - Cliquez sur "Terminer la leçon"
   - Un résumé de la leçon sera généré automatiquement
   - Accédez à vos notes via "📁 Mes leçons"

## 🛠️ Résolution de problèmes

### Problème : "Module not found"
```bash
# Réinstaller les dépendances Python
pip3 install -r requirements.txt --force-reinstall

# Réinstaller les dépendances Node
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Problème : "OpenAI API Key not found"
- Vérifiez que le fichier `.env` contient votre clé
- Vérifiez que `frontend/.env` contient `VITE_OPENAI_API_KEY`
- Redémarrez les serveurs après modification

### Problème : "Port already in use"
```bash
# Trouver et tuer le processus sur le port 5000
lsof -ti:5000 | xargs kill -9

# Trouver et tuer le processus sur le port 5173
lsof -ti:5173 | xargs kill -9
```

### Problème : "ANAM connection failed"
- Vérifiez votre clé ANAM dans `.env`
- Vérifiez votre connexion internet
- L'avatar vocal nécessite une connexion stable

## 📝 Arrêter les serveurs

Dans chaque terminal, appuyez sur :
```
Ctrl + C
```

## 🎓 Architecture du projet

```
Brainstorm_agent/
├── rag_server.py          # Serveur backend (RAG + Upload)
├── server.py              # Serveur de fichiers (optionnel)
├── .env                   # Clés API backend
├── requirements.txt       # Dépendances Python
├── uploads/               # Documents uploadés
├── qdrant_storage/        # Base vectorielle
└── frontend/
    ├── src/
    │   ├── components/    # Interface React
    │   ├── services/      # API et génération
    │   ├── config/        # Configuration du professeur
    │   └── types/         # Types TypeScript
    ├── .env               # Clés API frontend
    └── package.json       # Dépendances Node
```

## 🆘 Support

Si vous rencontrez des problèmes :
1. Vérifiez que tous les serveurs sont lancés
2. Vérifiez les clés API dans les fichiers `.env`
3. Regardez les logs dans les terminaux
4. Consultez la console du navigateur (F12)

---

**Bon apprentissage ! 📚🎓**
