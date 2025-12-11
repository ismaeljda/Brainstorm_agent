import React, { useState, useEffect } from 'react';
import type { Agent, UploadedDocument } from '../types';
import { agents } from '../config/agents';
import { uploadDocument, listDocuments } from '../services/api';
import './SetupScreen.css';

interface SetupScreenProps {
  onStartCall: (agent: Agent, context: string) => void;
  onViewFolder?: () => void;
}

const SetupScreen: React.FC<SetupScreenProps> = ({ onStartCall, onViewFolder }) => {
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
      <div className="setup-container">
        <div className="setup-header">
          <div>
            <h1 className="setup-title">Plateforme d'Apprentissage</h1>
            <p className="setup-subtitle">
              Rencontrez votre professeur personnel et progressez dans vos études avec un accompagnement sur-mesure
            </p>
          </div>
          {onViewFolder && (
            <button className="view-folder-button" onClick={onViewFolder}>
              📁 Mes leçons
            </button>
          )}
        </div>

        <div className="context-section">
          <h2 className="section-label">
            <span className="section-number">01</span>
            Vos objectifs d'apprentissage
          </h2>
          <p className="section-description">
            Décrivez ce que vous souhaitez apprendre, vos objectifs scolaires, vos difficultés et vos centres d'intérêt
          </p>
          <textarea
            className="context-textarea"
            value={companyContext}
            onChange={e => setCompanyContext(e.target.value)}
            placeholder="Exemple : Je suis en terminale scientifique et je prépare le bac. J'ai des difficultés en mathématiques, notamment sur les fonctions et les dérivées. J'aimerais améliorer mes notes et mieux comprendre ces concepts..."
          />
        </div>

        <div className="upload-section">
          <h2 className="section-label">
            <span className="section-number">02</span>
            Cours & documents
          </h2>
          <p className="section-description">
            Ajoutez vos cours, fiches de révision, exercices et tout document utile pour votre apprentissage
          </p>
          <div
            className={`upload-zone ${isDragging ? 'dragover' : ''}`}
            onClick={() => document.getElementById('fileInput')?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-icon">📂</div>
            <div>
              <strong>Cliquez pour parcourir ou glissez vos fichiers ici</strong>
            </div>
            <div className="upload-hint">Formats supportés : PDF, DOCX, TXT, MD, CSV, JSON, LOG</div>
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
                    {doc.status === 'uploading' && 'EN COURS'}
                    {doc.status === 'ready' && `PRÊT · ${doc.chunks} SECTIONS`}
                    {doc.status === 'failed' && 'ÉCHEC'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="agents-section">
          <h2 className="section-label">
            <span className="section-number">03</span>
            Votre professeur
          </h2>
          <p className="section-description">
            Sélectionnez votre professeur pour commencer une leçon interactive. Il pourra répondre à toutes vos questions.
          </p>
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

        <button
          className="start-button"
          onClick={handleStartCall}
          disabled={!isReadyToStart}
        >
          {isReadyToStart
            ? `Démarrer la leçon avec ${selectedAgent?.name}`
            : 'Sélectionnez votre professeur pour continuer'}
        </button>
      </div>
    </div>
  );
};

export default SetupScreen;
