import React, { useState, useEffect } from 'react';
import type { Agent, UploadedDocument } from '../types';
import { agents } from '../config/agents';
import { uploadDocument, listDocuments } from '../services/api';
import './SetupScreen.css';

interface SetupScreenProps {
  onStartCall: (agent: Agent, context: string) => void;
}

const SetupScreen: React.FC<SetupScreenProps> = ({ onStartCall }) => {
  const [companyContext, setCompanyContext] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    loadExistingDocuments();
  }, []);

  const loadExistingDocuments = async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleFileSelect = async (files: FileList | null) => {
    if (!files) return;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const tempDoc: UploadedDocument = {
        id: `temp-${Date.now()}-${i}`,
        filename: file.name,
        status: 'uploading',
      };
      setDocuments(prev => [tempDoc, ...prev]);

      try {
        const uploadedDoc = await uploadDocument(file);
        setDocuments(prev =>
          prev.map(doc => (doc.id === tempDoc.id ? uploadedDoc : doc))
        );
      } catch (error: any) {
        setDocuments(prev =>
          prev.map(doc =>
            doc.id === tempDoc.id
              ? { ...doc, status: 'failed', error: error.message }
              : doc
          )
        );
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleStartCall = () => {
    if (selectedAgent) {
      onStartCall(selectedAgent, companyContext);
    }
  };

  const isReadyToStart = selectedAgent !== null;

  return (
    <div className="setup-screen">
      <div className="setup-card">
        <div className="setup-header">
          <h1>AI Consultant Platform</h1>
          <p>Configurez votre session et choisissez votre agent IA</p>
        </div>

        <div className="setup-content">
          <div className="setup-section">
            <h2>📋 Contexte Entreprise</h2>
            <textarea
              className="context-textarea"
              value={companyContext}
              onChange={e => setCompanyContext(e.target.value)}
              placeholder="Décrivez votre entreprise, son secteur d'activité, ses objectifs, ses défis actuels...

Ex: Nous sommes une startup fintech spécialisée dans les paiements B2B. Nous cherchons à optimiser notre stratégie de croissance et à améliorer notre taux de conversion..."
            />
          </div>

          <div className="setup-section">
            <h2>📄 Documents</h2>
            <p className="section-description">
              Importez vos documents (stratégie, données marché, rapports...)
            </p>
            <div
              className={`upload-zone ${isDragging ? 'dragover' : ''}`}
              onClick={() => document.getElementById('fileInput')?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="upload-icon">📁</div>
              <div>
                <strong>Cliquez ou glissez vos fichiers ici</strong>
              </div>
              <div className="upload-hint">PDF, DOCX, TXT, MD, CSV, JSON, LOG</div>
            </div>
            <input
              type="file"
              id="fileInput"
              multiple
              accept=".pdf,.txt,.md,.docx,.csv,.json,.log"
              style={{ display: 'none' }}
              onChange={e => handleFileSelect(e.target.files)}
            />
            {documents.length > 0 && (
              <div className="file-list">
                {documents.map(doc => (
                  <div key={doc.id} className={`file-item ${doc.status}`}>
                    <span className="file-name">{doc.filename}</span>
                    <span className="file-status">
                      {doc.status === 'uploading' && '⏳ Upload...'}
                      {doc.status === 'ready' && `✓ ${doc.chunks} chunks`}
                      {doc.status === 'failed' && '❌ Échec'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="setup-section agents-section">
            <h2>🤖 Choisissez votre Agent</h2>
            <div className="agents-grid">
              {agents.map(agent => (
                <div
                  key={agent.id}
                  className={`agent-card ${selectedAgent?.id === agent.id ? 'selected' : ''}`}
                  onClick={() => setSelectedAgent(agent)}
                >
                  <div className="agent-icon">{agent.icon}</div>
                  <div className="agent-name">{agent.name}</div>
                  <div className="agent-description">{agent.description}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <button
          className="start-button"
          onClick={handleStartCall}
          disabled={!isReadyToStart}
        >
          {isReadyToStart
            ? `Lancer la consultation avec ${selectedAgent?.name}`
            : 'Sélectionnez un agent pour continuer'}
        </button>
      </div>
    </div>
  );
};

export default SetupScreen;
