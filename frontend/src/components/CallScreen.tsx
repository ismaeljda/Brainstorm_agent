import React, { useEffect, useRef, useState } from 'react';
import { createClient } from '@anam-ai/js-sdk';
import type { Agent } from '../types';
import { createSessionToken, searchDocuments } from '../services/api';
import './CallScreen.css';

interface CallScreenProps {
  agent: Agent;
  context: string;
  onEndCall: () => void;
}

const CallScreen: React.FC<CallScreenProps> = ({ agent, context, onEndCall }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState('Connexion en cours...');
  const [isConnected, setIsConnected] = useState(false);
  const anamClientRef = useRef<any>(null);

  useEffect(() => {
    initializeCall();

    return () => {
      // Cleanup on unmount
      if (anamClientRef.current) {
        try {
          anamClientRef.current.disconnect();
        } catch (error) {
          console.error('Error disconnecting:', error);
        }
      }
    };
  }, []);

  const initializeCall = async () => {
    try {
      setStatus('Création de la session...');

      // Enrichir le system prompt avec le contexte
      const enrichedSystemPrompt = context
        ? `${agent.systemPrompt}\n\n# Contexte de l'utilisateur\n${context}`
        : agent.systemPrompt;

      // Créer la configuration de persona avec le tool RAG
      const personaConfig = {
        name: agent.name,
        avatarId: agent.avatarId,
        voiceId: agent.voiceId,
        llmId: agent.llmId,
        systemPrompt: enrichedSystemPrompt,
        tools: [
          {
            type: 'client',
            name: 'search_documents',
            description:
              "UTILISE CET OUTIL IMMÉDIATEMENT dès que l'utilisateur mentionne 'mes documents', 'mon fichier', 'ce que j'ai uploadé' ou demande des informations qui pourraient être dans ses documents uploadés. Recherche sémantique dans la base documentaire.",
            parameters: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description:
                    'La requête de recherche pour trouver des informations pertinentes dans les documents',
                },
              },
              required: ['query'],
            },
            handler: async (params: { query: string }) => {
              console.log('🔍 RAG Tool called with query:', params.query);
              try {
                const results = await searchDocuments(params.query, 3);
                console.log('✅ RAG results:', results.length, 'chunks found');
                console.log('📄 Results:', results);

                return {
                  results: results.map(r => ({
                    text: r.text,
                    source: r.source,
                    relevance: r.relevance,
                  })),
                };
              } catch (error: any) {
                console.error('❌ RAG error:', error);
                return { error: error.message };
              }
            },
          },
        ],
      };

      // Créer le token de session
      const sessionToken = await createSessionToken(personaConfig);

      setStatus('Connexion à l\'agent...');

      // Créer le client ANAM
      const anamClient = createClient(sessionToken);
      anamClientRef.current = anamClient;

      // Connecter la vidéo
      if (videoRef.current) {
        await anamClient.streamToVideoElement(videoRef.current.id);
      }

      setStatus('Connecté ! Vous pouvez parler');
      setIsConnected(true);

      console.log('🎉 Call initialized successfully');
    } catch (error) {
      console.error('Failed to initialize call:', error);
      setStatus('Erreur de connexion. Vérifiez la console.');
    }
  };

  const handleEndCall = () => {
    if (anamClientRef.current) {
      try {
        anamClientRef.current.disconnect();
      } catch (error) {
        console.error('Error disconnecting:', error);
      }
    }
    onEndCall();
  };

  return (
    <div className="call-screen">
      <div className="call-header">
        <div className="call-info">
          <h2>{agent.name}</h2>
          <p>{agent.description}</p>
        </div>
        <button className="end-call-button" onClick={handleEndCall}>
          Terminer l'appel
        </button>
      </div>

      <div className="call-container">
        <div className="video-wrapper">
          <video id="persona-video" ref={videoRef} autoPlay playsInline />
          <div className={`call-status ${isConnected ? 'connected' : ''}`}>
            {status}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CallScreen;
