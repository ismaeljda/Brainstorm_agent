/**
 * Configuration et helpers pour les variables d'environnement
 */

// Helper pour accéder aux variables d'environnement de manière sûre
const getEnv = (key: string, defaultValue: string = ''): string => {
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    return (import.meta.env as any)[key] || defaultValue;
  }
  return defaultValue;
};

export const config = {
  firebase: {
    apiKey: getEnv('VITE_FIREBASE_API_KEY', 'demo-api-key'),
    authDomain: getEnv('VITE_FIREBASE_AUTH_DOMAIN', 'brainstormia.firebaseapp.com'),
    projectId: getEnv('VITE_FIREBASE_PROJECT_ID', 'brainstormia'),
    storageBucket: getEnv('VITE_FIREBASE_STORAGE_BUCKET', 'brainstormia.appspot.com'),
    messagingSenderId: getEnv('VITE_FIREBASE_MESSAGING_SENDER_ID', '123456789'),
    appId: getEnv('VITE_FIREBASE_APP_ID', '1:123456789:web:abcdef'),
  },
  api: {
    baseUrl: getEnv('VITE_API_BASE_URL', 'http://localhost:8000'),
    wsUrl: getEnv('VITE_WS_BASE_URL', 'ws://localhost:8000'),
  },
};
