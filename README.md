# 🎓 Plateforme d'Apprentissage avec IA

Une plateforme interactive d'apprentissage avec un professeur virtuel (IA) qui peut donner des leçons, répondre aux questions et s'adapter à vos cours.

## 🚀 Lancement rapide

### Méthode 1 : Script automatique (Recommandé)

```bash
./start.sh
```

Puis ouvrez votre navigateur sur **http://localhost:5173**

### Méthode 2 : Manuel (3 terminaux)

**Terminal 1 - Serveur RAG:**
```bash
python3 rag_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## ⚙️ Configuration initiale

### 1. Clés API backend (`.env`)
```bash
OPENAI_API_KEY=sk-proj-votre-cle-ici
ANAM_API_KEY=votre-cle-anam-ici
```

### 2. Clés API frontend (`frontend/.env`)
```bash
VITE_OPENAI_API_KEY=sk-proj-votre-cle-ici
```

### 3. Installation des dépendances

**Backend:**
```bash
pip3 install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

## 📖 Utilisation

1. **Définissez vos objectifs d'apprentissage** - Décrivez ce que vous voulez apprendre
2. **Uploadez vos cours** (optionnel) - PDF, DOCX, TXT, MD
3. **Sélectionnez Professeur Martin** 👨‍🏫
4. **Démarrez la leçon** - Discutez avec le professeur par voix
5. **Terminez et sauvegardez** - Recevez un résumé de la leçon

## 📚 Fonctionnalités

- ✅ **Professeur virtuel interactif** avec voix et avatar
- ✅ **Upload de documents** - Le prof peut lire vos cours
- ✅ **RAG (Retrieval Augmented Generation)** - Recherche dans vos documents
- ✅ **Résumés automatiques** de chaque leçon
- ✅ **Historique complet** de vos leçons
- ✅ **Export en Markdown** de toutes vos notes

## 🛠️ Technologies

- **Frontend:** React + TypeScript + Vite
- **Backend:** Flask + Python
- **IA:** OpenAI GPT-4 + ANAM AI (avatar vocal)
- **Base vectorielle:** Qdrant (in-memory)
- **RAG:** OpenAI embeddings + recherche sémantique

## 📁 Structure

```
Brainstorm_agent/
├── rag_server.py          # Serveur RAG + Upload
├── .env                   # Configuration backend
├── requirements.txt       # Dépendances Python
├── start.sh              # Script de lancement
├── LAUNCH_GUIDE.md       # Guide détaillé
└── frontend/
    ├── src/
    │   ├── components/   # Interface React
    │   ├── config/       # Config du professeur
    │   └── services/     # API + génération
    └── .env             # Configuration frontend
```

## 🆘 Aide

Consultez le **[Guide de lancement détaillé](LAUNCH_GUIDE.md)** pour plus d'informations.

## 📝 Licence

Projet éducatif - Usage personnel

---

**Bon apprentissage ! 🎓📚**
