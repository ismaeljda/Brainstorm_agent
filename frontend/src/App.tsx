/**
 * Application principale avec routing
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, ProtectedRoute } from './components/Auth';
import { Login } from './pages/Login';
import ConfigPage from './pages/Config';
import MeetingPage from './pages/Meeting';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Page de login */}
          <Route path="/login" element={<Login />} />

          {/* Page d'accueil : rediriger vers config si authentifié, sinon login */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Navigate to="/config" replace />
              </ProtectedRoute>
            }
          />

          {/* Page de configuration */}
          <Route
            path="/config"
            element={
              <ProtectedRoute>
                <ConfigPage />
              </ProtectedRoute>
            }
          />

          {/* Page de réunion */}
          <Route
            path="/meeting/:jobId"
            element={
              <ProtectedRoute>
                <MeetingPage />
              </ProtectedRoute>
            }
          />

          {/* Redirect par défaut */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
