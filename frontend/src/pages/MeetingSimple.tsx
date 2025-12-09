/**
 * Page de simulation de réunion (mode polling, sans WebSocket)
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

interface Message {
  agent: string;
  message: string;
  timestamp: Date;
}

const AGENT_CONFIG: Record<string, any> = {
  facilitateur: { name: 'Facilitateur', emoji: '🎯', color: 'bg-blue-100 text-blue-800' },
  strategie: { name: 'Stratège Business', emoji: '💼', color: 'bg-purple-100 text-purple-800' },
  tech: { name: 'Tech Lead', emoji: '💻', color: 'bg-green-100 text-green-800' },
  creatif: { name: 'Creative Thinker', emoji: '🎨', color: 'bg-pink-100 text-pink-800' },
  human: { name: 'Vous', emoji: '👤', color: 'bg-gray-100 text-gray-800' },
};

export const MeetingSimplePage: React.FC = () => {
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [meetingActive, setMeetingActive] = useState(false);
  const [objective, setObjective] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Polling pour récupérer les nouveaux messages
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:8000/get_messages');
        const data = await response.json();

        if (data.messages && data.messages.length > 0) {
          setMessages(prev => {
            const newMessages = data.messages.map((m: any) => ({
              ...m,
              timestamp: new Date()
            }));
            return [...prev, ...newMessages];
          });
        }

        setMeetingActive(data.meeting_active);
        setObjective(data.objective);
      } catch (error) {
        console.error('Erreur polling:', error);
      }
    }, 1000); // Poll chaque seconde

    return () => clearInterval(interval);
  }, []);

  // Retour à la config
  const handleBackToConfig = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">🧠 BrainStormIA</h1>
            {meetingActive && (
              <span className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                En direct
              </span>
            )}
            {!meetingActive && messages.length > 0 && (
              <span className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm">
                Terminée
              </span>
            )}
          </div>
          <button
            onClick={handleBackToConfig}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Retour
          </button>
        </div>
      </div>

      {/* Objective */}
      {objective && (
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
            <p className="text-sm font-medium text-primary">Objectif de la réunion :</p>
            <p className="text-gray-800">{objective}</p>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              <p className="text-xl mb-2">🎬 En attente du démarrage...</p>
              <p className="text-sm">La réunion va commencer dans un instant</p>
            </div>
          )}

          {messages.map((msg, idx) => {
            const config = AGENT_CONFIG[msg.agent] || AGENT_CONFIG.human;

            return (
              <div key={idx} className="bg-white rounded-lg shadow-sm p-6">
                {/* Agent Header */}
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{config.emoji}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{config.name}</span>
                      <span className={`px-2 py-1 rounded text-xs ${config.color}`}>
                        {msg.agent}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                {/* Message Content */}
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{msg.message}</ReactMarkdown>
                </div>
              </div>
            );
          })}

          {/* Loading indicator */}
          {meetingActive && messages.length > 0 && (
            <div className="flex items-center justify-center py-4">
              <div className="flex items-center gap-2 text-gray-500">
                <div className="animate-bounce">●</div>
                <div className="animate-bounce" style={{ animationDelay: '0.1s' }}>●</div>
                <div className="animate-bounce" style={{ animationDelay: '0.2s' }}>●</div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Bouton nouvelle réunion */}
        {!meetingActive && messages.length > 0 && (
          <div className="mt-8 text-center">
            <button
              onClick={handleBackToConfig}
              className="px-6 py-3 bg-primary text-white font-semibold rounded-lg
                       hover:bg-primary/90 transition-colors"
            >
              Nouvelle réunion
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MeetingSimplePage;
