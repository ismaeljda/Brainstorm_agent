# AI Consultant Platform - Frontend

Une plateforme moderne de consultation IA avec React, TypeScript et Vite.

## 🚀 Fonctionnalités

- **Interface de configuration** : Ajoutez du contexte entreprise et uploadez des documents
- **Sélection d'agents** : Choisissez parmi plusieurs consultants IA spécialisés
- **RAG intégré** : Les agents peuvent chercher dans vos documents uploadés
- **Appel vidéo** : Communication vocale en temps réel avec les agents
- **Design moderne** : Interface élégante avec animations et gradients

## 📋 Prérequis

- Node.js 18+
- Le serveur RAG doit être lancé sur `http://localhost:5000`
- Une clé API ANAM valide

## 🛠️ Installation

```bash
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

Le frontend sera accessible sur `http://localhost:5173`

## 🏗️ Structure du projet

```
frontend/
├── src/
│   ├── components/
│   │   ├── SetupScreen.tsx      # Écran de configuration
│   │   ├── SetupScreen.css
│   │   ├── CallScreen.tsx       # Écran d'appel vidéo
│   │   └── CallScreen.css
│   ├── config/
│   │   └── agents.ts            # Configuration des agents
│   ├── services/
│   │   └── api.ts               # Services API (RAG + ANAM)
│   ├── types/
│   │   └── index.ts             # Types TypeScript
│   ├── App.tsx                  # Composant principal
│   ├── App.css
│   ├── index.css                # Styles globaux
│   └── main.tsx
└── package.json
```

## 🤖 Agents disponibles

1. **Alexandre** 💼 - Consultant stratégique senior
2. **Marie** 📊 - Analyste marketing et acquisition
3. **Thomas** 💡 - Expert innovation et transformation
4. **Sophie** 💰 - Conseillère financière

## 🔧 Configuration

Pour modifier la clé API ANAM, éditez le fichier `src/services/api.ts`.

Pour ajouter de nouveaux agents, modifiez `src/config/agents.ts`.

## 📦 Build de production

```bash
npm run build
```

Les fichiers buildés seront dans le dossier `dist/`.

## 🎨 Technologies utilisées

- **React 18** - Bibliothèque UI
- **TypeScript** - Typage statique
- **Vite** - Build tool ultra-rapide
- **Axios** - Client HTTP
- **@anam-ai/js-sdk** - SDK pour les appels vidéo IA
- **CSS Modules** - Styles scoped

## 🔗 Intégration avec le backend

Le frontend communique avec deux services :

1. **RAG Server** (`http://localhost:5000`) :
   - Upload de documents
   - Recherche sémantique
   - Gestion des documents

2. **ANAM API** (`https://api.anam.ai/v1`) :
   - Création de sessions
   - Appels vidéo avec les agents
   - Outils RAG côté client

## 📝 Notes de développement

- Les agents utilisent un outil `search_documents` qui se déclenche automatiquement
- Le contexte entreprise est injecté dans le system prompt de l'agent
- Les documents sont indexés dans Qdrant via le serveur RAG
- La vidéo utilise WebRTC via le SDK ANAM
