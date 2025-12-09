# 🔥 Configuration Firebase pour BrainStormIA

Ce guide vous aide à configurer Firebase Authentication et Firestore pour votre application.

## 📋 Étape 1 : Créer un projet Firebase

1. Allez sur https://console.firebase.google.com/
2. Cliquez sur "Ajouter un projet"
3. Nom du projet : `BrainStormIA` (ou votre choix)
4. Suivez les étapes jusqu'à la fin

## 🔐 Étape 2 : Activer l'authentification

1. Dans votre projet Firebase, allez dans **Authentication**
2. Cliquez sur "Get started"
3. Allez dans l'onglet **Sign-in method**
4. Activez **Google** comme fournisseur
5. Configurez l'écran de consentement OAuth si demandé

## 🗄️ Étape 3 : Activer Firestore

1. Allez dans **Firestore Database**
2. Cliquez sur "Create database"
3. Choisissez le mode **Production** (avec règles de sécurité)
4. Sélectionnez un emplacement (par exemple `europe-west3` pour l'Europe)
5. Règles de sécurité recommandées :

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Les utilisateurs peuvent lire/écrire leurs propres données
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Les réunions sont accessibles par leur créateur
    match /meetings/{meetingId} {
      allow read, write: if request.auth != null &&
                            resource.data.user_uid == request.auth.uid;
    }
  }
}
```

## 📱 Étape 4 : Récupérer les credentials Frontend

1. Dans **Project Settings** (icône engrenage) > **General**
2. Scrollez jusqu'à "Vos applications"
3. Cliquez sur l'icône **Web** (`</>`)
4. Donnez un nom à votre app : `BrainStormIA Web`
5. **NE PAS** cocher "Firebase Hosting"
6. Copiez la configuration affichée

### Mettez à jour votre `.env` avec ces valeurs :

```bash
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=votre-projet.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=votre-projet
VITE_FIREBASE_STORAGE_BUCKET=votre-projet.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
```

## 🔑 Étape 5 : Récupérer les credentials Backend (Admin SDK)

1. Dans **Project Settings** > **Service accounts**
2. Cliquez sur "Generate new private key"
3. Un fichier JSON sera téléchargé
4. **Renommez-le** en `firebase-credentials.json`
5. **Placez-le** à la racine du projet : `hackaton_gand/firebase-credentials.json`
6. ⚠️ **IMPORTANT** : Ajoutez-le au `.gitignore` :

```bash
# Dans .gitignore
firebase-credentials.json
```

### Mettez à jour votre `.env` :

```bash
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_PROJECT_ID=votre-projet
FIREBASE_STORAGE_BUCKET=votre-projet.appspot.com
```

## 🚀 Étape 6 : Activer Firebase dans l'application

### 1. Supprimer le mode dev bypass dans le frontend

Ouvrez `frontend/src/components/Auth.tsx` et **supprimez ou commentez** ces lignes (120-126) :

```typescript
// MODE DEV : Bypass Firebase si clé demo
const isDev = config.firebase.apiKey === 'demo-api-key';

if (isDev) {
  // En mode dev, pas besoin d'auth
  return <>{children}</>;
}
```

### 2. Supprimer le mode dev bypass dans le backend

Ouvrez `src/middleware/firebase_auth.py` et assurez-vous que l'environnement est en **production** dans votre `.env` :

```bash
ENVIRONMENT=production
```

## 🔄 Étape 7 : Redémarrer les services

```bash
# Arrêter tous les conteneurs
docker-compose down

# Reconstruire et relancer
docker-compose up -d --build
```

## ✅ Étape 8 : Tester l'authentification

1. Ouvrez http://localhost:3000
2. Vous devriez voir un bouton "Se connecter avec Google"
3. Cliquez dessus et connectez-vous avec votre compte Google
4. Vous devriez être redirigé vers l'application
5. Vérifiez que votre profil est créé dans Firestore Console

## 📊 Vérifier que tout fonctionne

### Dans Firebase Console > Firestore Database

Vous devriez voir :
- Collection `users` avec votre utilisateur
- Collection `meetings` (vide au début)

### Dans l'application

Vous pouvez tester les endpoints API :
- `GET /api/users/me` - Récupère votre profil
- `GET /api/users/me/meetings` - Historique des réunions
- `GET /api/users/me/stats` - Vos statistiques

## 🛡️ Sécurité

### Variables sensibles à NE JAMAIS committer :

- `firebase-credentials.json`
- `.env` (utilisez `.env.example` comme template)
- Vos clés API

### Ajoutez à votre `.gitignore` :

```bash
# Firebase credentials
firebase-credentials.json

# Environment variables
.env
.env.local
.env.production

# Firebase cache
.firebase/
```

## 🐛 Dépannage

### "Firebase non initialisé"

- Vérifiez que `firebase-credentials.json` existe
- Vérifiez le chemin dans `FIREBASE_CREDENTIALS_PATH`
- Vérifiez les permissions du fichier

### "Invalid API key" dans le frontend

- Vérifiez que toutes les variables `VITE_FIREBASE_*` sont dans `.env`
- Redémarrez le frontend : `docker-compose restart frontend`

### "User not authenticated" sur les endpoints API

- Vérifiez que le token Firebase est envoyé dans le header `Authorization: Bearer <token>`
- Vérifiez que `ENVIRONMENT=production` dans `.env`

## 📚 Ressources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
