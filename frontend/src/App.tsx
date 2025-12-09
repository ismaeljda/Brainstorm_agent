/**
 * Application principale avec routing
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, ProtectedRoute } from './components/Auth';
import ConfigPage from './pages/Config';
import MeetingPage from './pages/Meeting';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Page d'accueil : Configuration */}
          <Route
            path="/"
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
