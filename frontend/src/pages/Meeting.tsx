/**
 * Page de simulation immersive de réunion
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { wsService, WebSocketMessage } from '../services/websocket';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../components/Auth';

interface Message {
  agent: string;
  text: string;
  audioUrl?: string;
  timestamp: Date;
}

const AGENT_CONFIG = {
  facilitateur: { name: 'Facilitateur', emoji: '🎯', color: 'bg-blue-100 text-blue-800' },
  strategie: { name: 'Stratège Business', emoji: '💼', color: 'bg-purple-100 text-purple-800' },
  tech: { name: 'Tech Lead', emoji: '💻', color: 'bg-green-100 text-green-800' },
  creatif: { name: 'Creative Thinker', emoji: '🎨', color: 'bg-pink-100 text-pink-800' },
  human: { name: 'Vous', emoji: '👤', color: 'bg-gray-100 text-gray-800' },
};

export const MeetingPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  const [messages, setMessages] = useState<Message[]>([]);
  const [connected, setConnected] = useState(false);
  const [ended, setEnded] = useState(false);
  const [summary, setSummary] = useState('');
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Connexion WebSocket
  useEffect(() => {
    if (!jobId) {
      navigate('/');
      return;
    }

    console.log('🔌 Connexion au meeting:', jobId);
    wsService.connect(jobId);

    const unsubscribe = wsService.onMessage((message: WebSocketMessage) => {
      console.log('📨 Message WebSocket:', message);

      switch (message.type) {
        case 'connected':
          setConnected(true);
          break;

        case 'turn':
          // Ajouter le message
          setMessages(prev => [
            ...prev,
            {
              agent: message.agent,
              text: message.text,
              audioUrl: message.audio_url,
              timestamp: new Date(),
            },
          ]);

          // Jouer l'audio si disponible
          if (message.audio_url) {
            playAudio(message.audio_url);
          }
          break;

        case 'end':
          setEnded(true);
          setSummary(message.summary);
          break;

        case 'completed':
          setEnded(true);
          if (message.result?.summary) {
            setSummary(message.result.summary);
          }
          break;

        case 'error':
          alert(`Erreur: ${message.error}`);
          break;
      }
    });

    // Cleanup
    return () => {
      unsubscribe();
      wsService.disconnect();
      if (currentAudio) {
        currentAudio.pause();
      }
    };
  }, [jobId, navigate]);

  // Lecture audio
  const playAudio = (url: string) => {
    // Arrêter l'audio précédent
    if (currentAudio) {
      currentAudio.pause();
    }

    // Créer nouvel élément audio
    const audio = new Audio(url);
    audioRef.current = audio;
    setCurrentAudio(audio);

    audio.play().catch(error => {
      console.error('Erreur lecture audio:', error);
    });

    audio.onended = () => {
      setCurrentAudio(null);
    };
  };

  // Retour à la config
  const handleBackToConfig = () => {
    navigate('/');
  };

  if (!connected && !ended) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Connexion à la réunion...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">🧠 BrainStormIA</h1>
            {connected && !ended && (
              <span className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                En direct
              </span>
            )}
            {ended && (
              <span className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm">
                Terminée
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToConfig}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              ← Retour
            </button>

            {/* User menu */}
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
              {user?.photoURL && (
                <img
                  src={user.photoURL}
                  alt={user.displayName || 'User'}
                  className="w-7 h-7 rounded-full"
                />
              )}
              <span className="text-sm font-medium text-gray-700">
                {user?.displayName?.split(' ')[0] || 'User'}
              </span>
              <button
                onClick={() => signOut()}
                className="ml-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-900
                         hover:bg-gray-200 rounded transition-colors"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="space-y-4">
          {messages.map((message, idx) => {
            const config = AGENT_CONFIG[message.agent as keyof typeof AGENT_CONFIG] || AGENT_CONFIG.human;

            return (
              <div key={idx} className="bg-white rounded-lg shadow-sm p-6">
                {/* Agent Header */}
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{config.emoji}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{config.name}</span>
                      <span className={`px-2 py-1 rounded text-xs ${config.color}`}>
                        {message.agent}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Audio Player */}
                  {message.audioUrl && (
                    <button
                      onClick={() => playAudio(message.audioUrl!)}
                      className="px-3 py-1 bg-primary text-white rounded-lg text-sm
                               hover:bg-primary/90 transition-colors"
                    >
                      🔊 Écouter
                    </button>
                  )}
                </div>

                {/* Message Content */}
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{message.text}</ReactMarkdown>
                </div>
              </div>
            );
          })}

          {/* Loading indicator */}
          {connected && !ended && messages.length > 0 && (
            <div className="flex items-center justify-center py-4">
              <div className="flex items-center gap-2 text-gray-500">
                <div className="animate-bounce">●</div>
                <div className="animate-bounce delay-100">●</div>
                <div className="animate-bounce delay-200">●</div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Synthèse Finale */}
        {ended && summary && (
          <div className="mt-8 bg-gradient-to-r from-primary to-secondary rounded-lg shadow-lg p-8 text-white">
            <h2 className="text-2xl font-bold mb-4">📋 Synthèse Finale</h2>
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
            <div className="mt-6 flex gap-4">
              <button
                onClick={handleBackToConfig}
                className="px-6 py-3 bg-white text-primary font-semibold rounded-lg
                         hover:bg-gray-100 transition-colors"
              >
                Nouvelle réunion
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MeetingPage;
