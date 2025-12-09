# 🎨 BrainStormIA Frontend

Interface React TypeScript pour la plateforme multi-agents BrainStormIA.

## 🚀 Stack

- **React 18** + **TypeScript**
- **Vite** (build tool ultra-rapide)
- **TailwindCSS** (styling)
- **Firebase** (Auth + Storage)
- **React Router** (navigation)
- **Axios** (HTTP client)
- **WebSocket** (streaming temps réel)

## 📦 Installation

### Développement Local

```bash
cd frontend

# Installer les dépendances
npm install

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos clés Firebase

# Lancer le serveur de développement
npm run dev
```

L'application sera disponible sur **http://localhost:3000**

### Build Production

```bash
npm run build
npm run preview
```

## 🐳 Docker

Le frontend est automatiquement inclus dans le docker-compose principal :

```bash
# Depuis la racine du projet
docker-compose up --build

# Frontend accessible sur http://localhost:3000
```

## 📁 Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Auth.tsx          # Authentification Firebase
│   ├── pages/
│   │   ├── Config.tsx        # Configuration réunion
│   │   └── Meeting.tsx       # Salle de réunion immersive
│   ├── services/
│   │   ├── api.ts            # Client API HTTP
│   │   └── websocket.ts      # Service WebSocket
│   ├── firebase.ts           # Config Firebase
│   ├── App.tsx               # Router principal
│   ├── main.tsx              # Point d'entrée
│   └── index.css             # Styles globaux
├── public/                   # Assets statiques
├── Dockerfile                # Image Docker
├── nginx.conf                # Config Nginx
└── vite.config.ts            # Config Vite
```

## 🎯 Fonctionnalités

### 1. Authentification Firebase

- Connexion Google OAuth
- Protection des routes
- Tokens automatiques dans les requêtes API

### 2. Configuration de Réunion

- Saisie de l'objectif
- Contexte statique (injection directe)
- Upload documents pour RAG
- Sélection des agents

### 3. Réunion Immersive

- Streaming WebSocket temps réel
- Affichage des messages agents
- Lecture audio synchronisée (ElevenLabs)
- Synthèse finale en Markdown

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à partir de `.env.example` :

```env
# Firebase
VITE_FIREBASE_API_KEY=your-key
VITE_FIREBASE_AUTH_DOMAIN=your-domain
VITE_FIREBASE_PROJECT_ID=your-project
VITE_FIREBASE_STORAGE_BUCKET=your-bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id

# Backend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Proxy Vite (Dev)

Le fichier `vite.config.ts` configure automatiquement les proxies pour :
- `/api/*` → Backend API
- `/ws/*` → WebSocket

### Nginx (Production)

Le fichier `nginx.conf` configure :
- Reverse proxy vers l'API
- Support WebSocket
- Cache des assets statiques
- Gzip compression

## 🎨 Personnalisation

### Couleurs (Tailwind)

Modifiez `tailwind.config.js` :

```js
theme: {
  extend: {
    colors: {
      primary: '#6366f1',    // Couleur principale
      secondary: '#8b5cf6',  // Couleur secondaire
    }
  }
}
```

### Agents

Modifiez `src/pages/Meeting.tsx` pour personnaliser :

```typescript
const AGENT_CONFIG = {
  facilitateur: { name: '...', emoji: '🎯', color: 'bg-blue-100' },
  // ...
};
```

## 🧪 Tests

```bash
# Linter
npm run lint

# Build test
npm run build
```

## 📱 Responsive

L'interface est entièrement responsive :
- Mobile-first design
- Breakpoints Tailwind standard
- Grid adaptatif

## 🔒 Sécurité

- Authentification Firebase obligatoire
- Tokens JWT dans headers
- Protection CSRF
- Validation côté client

## 🚀 Déploiement

### Vercel / Netlify

```bash
npm run build
# Déployer le dossier dist/
```

### Docker Production

```bash
docker build -t brainstormia-frontend .
docker run -p 3000:80 brainstormia-frontend
```

## 📝 TODO

- [ ] Tests unitaires (Vitest)
- [ ] Tests E2E (Playwright)
- [ ] PWA support
- [ ] Internationalisation (i18n)
- [ ] Dark mode
- [ ] Accessibilité (a11y)

## 🆘 Troubleshooting

### WebSocket ne se connecte pas

Vérifiez que :
1. Le backend est bien lancé
2. Les URLs dans `.env` sont correctes
3. Pas de proxy/firewall bloquant les WebSocket

### Firebase Auth échoue

1. Vérifiez les credentials dans `.env`
2. Activez Google Auth dans Firebase Console
3. Ajoutez `localhost:3000` aux domaines autorisés

### Build échoue

```bash
# Nettoyer et réinstaller
rm -rf node_modules dist
npm install
npm run build
```

## 📄 Licence

MIT
