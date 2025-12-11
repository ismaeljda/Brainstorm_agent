import React, { useEffect, useRef, useState } from 'react';
import { createClient } from '@anam-ai/js-sdk';
import type { Agent, ConsultationNote, WorkDeliverable } from '../types';
import { createSessionToken, searchDocuments } from '../services/api';
import { generateWorkDeliverable } from '../services/workGenerator';
import './CallScreen.css';

interface CallScreenProps {
  agent: Agent;
  context: string;
  onEndCall: () => void;
  onConsultationComplete?: (note: ConsultationNote, deliverable: WorkDeliverable) => void;
}

const CallScreen: React.FC<CallScreenProps> = ({ agent, context, onEndCall, onConsultationComplete }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState('Connexion en cours...');
  const [isConnected, setIsConnected] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const anamClientRef = useRef<any>(null);
  const conversationTranscriptRef = useRef<string>('');

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

      // Enrichir le system prompt avec le contexte et les documents RAG
      let enrichedSystemPrompt = agent.systemPrompt;

      if (context) {
        setStatus('Récupération du contexte documentaire...');

        // Recherche automatique dans les documents avec le contexte fourni
        try {
          const ragResults = await searchDocuments(context, 5);

          if (ragResults.length > 0) {
            console.log('📚 Found', ragResults.length, 'relevant document chunks');

            // Construire un résumé des documents pertinents
            const documentsContext = ragResults
              .map((r, idx) => `\n[Document ${idx + 1} - ${r.source}]\n${r.text}`)
              .join('\n---\n');

            enrichedSystemPrompt = `${agent.systemPrompt}

# Contexte de l'utilisateur
${context}

# Documents pertinents uploadés par l'utilisateur
Les documents suivants ont été fournis par l'utilisateur et sont pertinents pour son contexte :
${documentsContext}

IMPORTANT : Ces informations proviennent directement des documents de l'utilisateur. Utilise-les comme base factuelle pour tes recommandations. Tu peux utiliser l'outil search_documents pour chercher des informations additionnelles si nécessaire.`;
          } else {
            enrichedSystemPrompt = `${agent.systemPrompt}\n\n# Contexte de l'utilisateur\n${context}`;
          }
        } catch (error) {
          console.error('RAG initialization failed:', error);
          enrichedSystemPrompt = `${agent.systemPrompt}\n\n# Contexte de l'utilisateur\n${context}`;
        }
      }

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

  const handleEndCall = async () => {
    if (anamClientRef.current) {
      try {
        anamClientRef.current.disconnect();
      } catch (error) {
        console.error('Error disconnecting:', error);
      }
    }

    // Générer le livrable de travail
    if (onConsultationComplete && conversationTranscriptRef.current) {
      setIsGenerating(true);
      setStatus('Génération du livrable en cours...');

      try {
        // Créer une note de consultation simulée (dans un vrai système, cela viendrait de l'analyse de la conversation)
        const consultationNote: ConsultationNote = {
          agentId: agent.id,
          agentName: agent.name,
          timestamp: new Date().toISOString(),
          summary: `Consultation avec ${agent.name} sur le projet business plan`,
          keyPoints: [
            'Discussion sur le contexte du projet',
            'Analyse des défis actuels',
            'Identification des opportunités',
          ],
          recommendations: [
            'Mise en place d\'une stratégie structurée',
            'Focus sur les quick wins',
            'Suivi régulier des métriques clés',
          ],
          nextSteps: [
            'Implémenter les recommandations prioritaires',
            'Planifier une revue dans 2 semaines',
          ],
        };

        // Générer le livrable de travail
        const deliverable = await generateWorkDeliverable({
          agent,
          context,
          conversationTranscript: conversationTranscriptRef.current,
          consultationNote,
        });

        onConsultationComplete(consultationNote, deliverable);
      } catch (error) {
        console.error('Erreur lors de la génération du livrable:', error);
        setStatus('Erreur lors de la génération du livrable');
      } finally {
        setIsGenerating(false);
      }
    } else {
      onEndCall();
    }
  };

  return (
    <div className="call-screen">
      <div className="call-header">
        <div className="call-info">
          <h2>{agent.name}</h2>
          <p>{agent.description}</p>
        </div>
        <button className="end-call-button" onClick={handleEndCall} disabled={isGenerating}>
          {isGenerating ? 'Génération...' : 'Terminer l\'appel'}
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
