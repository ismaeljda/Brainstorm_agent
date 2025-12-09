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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    // Rediriger vers la page de login
    window.location.href = '/login';
    return null;
  }

  return <>{children}</>;
};
