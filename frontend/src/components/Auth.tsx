/**
 * Composant d'authentification Firebase
 */

import React, { useState, useEffect } from 'react';
import {
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  User
} from 'firebase/auth';
import { auth, googleProvider } from '../firebase';
import { config } from '../config';

interface AuthProps {
  children: React.ReactNode;
}

export const AuthContext = React.createContext<{
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}>({
  user: null,
  loading: true,
  signIn: async () => {},
  signOut: async () => {},
});

export const AuthProvider: React.FC<AuthProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const handleSignIn = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error('Erreur connexion:', error);
      throw error;
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Erreur déconnexion:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn: handleSignIn,
        signOut: handleSignOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Composant Login simple
export const LoginButton: React.FC = () => {
  const { user, signIn, signOut } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    setLoading(true);
    try {
      if (user) {
        await signOut();
      } else {
        await signIn();
      }
    } catch (error) {
      alert('Erreur authentification');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleAuth}
      disabled={loading}
      className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90
                 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      {loading ? '...' : user ? 'Se déconnecter' : 'Se connecter avec Google'}
    </button>
  );
};

// Guard pour routes protégées
export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  // MODE DEV : Bypass Firebase si clé demo
  const isDev = config.firebase.apiKey === 'demo-api-key';

  if (isDev) {
    // En mode dev, pas besoin d'auth
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Chargement...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <h1 className="text-2xl font-bold">Authentification requise</h1>
        <LoginButton />
      </div>
    );
  }

  return <>{children}</>;
};
