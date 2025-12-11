import React from 'react';
import type { BusinessPlanFolder, WorkDeliverable } from '../types';
import { downloadBusinessPlan } from '../services/workGenerator';
import './FolderView.css';

interface FolderViewProps {
  folder: BusinessPlanFolder;
  onClose: () => void;
  onNewConsultation: () => void;
}

const FolderView: React.FC<FolderViewProps> = ({ folder, onClose, onNewConsultation }) => {
  const handleDownload = () => {
    downloadBusinessPlan(
      folder.projectName,
      folder.context,
      folder.consultations,
      folder.deliverables
    );
  };

  const getDeliverableIcon = (type: WorkDeliverable['type']) => {
    switch (type) {
      case 'strategy':
        return '📋';
      case 'marketing':
        return '📊';
      case 'financial':
        return '💰';
      case 'innovation':
        return '💡';
      default:
        return '📄';
    }
  };

  const getDeliverableLabel = (type: WorkDeliverable['type']) => {
    switch (type) {
      case 'strategy':
        return 'Stratégie';
      case 'marketing':
        return 'Marketing';
      case 'financial':
        return 'Finance';
      case 'innovation':
        return 'Innovation';
      default:
        return 'Document';
    }
  };

  return (
    <div className="folder-view">
      <div className="folder-container">
        <div className="folder-header">
          <div className="folder-header-content">
            <h1 className="folder-title">Votre Dossier Business Plan</h1>
            <p className="folder-subtitle">{folder.projectName}</p>
          </div>
          <button className="folder-close-button" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="folder-content">
          {/* Summary */}
          <div className="folder-section">
            <div className="section-header">
              <span className="section-number">Résumé</span>
            </div>
            <div className="summary-grid">
              <div className="summary-card">
                <div className="summary-label">Consultations</div>
                <div className="summary-value">{folder.consultations.length}</div>
              </div>
              <div className="summary-card">
                <div className="summary-label">Livrables</div>
                <div className="summary-value">{folder.deliverables.length}</div>
              </div>
              <div className="summary-card">
                <div className="summary-label">Documents</div>
                <div className="summary-value">{folder.documents.length}</div>
              </div>
            </div>
          </div>

          {/* Deliverables */}
          {folder.deliverables.length > 0 && (
            <div className="folder-section">
              <div className="section-header">
                <span className="section-number">Livrables Générés</span>
              </div>
              <div className="deliverables-list">
                {folder.deliverables.map(deliverable => (
                  <div key={deliverable.id} className={`deliverable-card ${deliverable.status}`}>
                    <div className="deliverable-header">
                      <div className="deliverable-type">
                        <span className="deliverable-icon">{getDeliverableIcon(deliverable.type)}</span>
                        <span className="deliverable-type-label">{getDeliverableLabel(deliverable.type)}</span>
                      </div>
                      <span className="deliverable-date">
                        {new Date(deliverable.createdAt).toLocaleDateString('fr-FR', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </span>
                    </div>
                    <h3 className="deliverable-title">{deliverable.title}</h3>
                    {deliverable.status === 'ready' && (
                      <div className="deliverable-preview">
                        <pre>{deliverable.content.slice(0, 200)}...</pre>
                      </div>
                    )}
                    {deliverable.status === 'generating' && (
                      <div className="deliverable-status">Génération en cours...</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Consultations */}
          {folder.consultations.length > 0 && (
            <div className="folder-section">
              <div className="section-header">
                <span className="section-number">Historique des Consultations</span>
              </div>
              <div className="consultations-timeline">
                {folder.consultations.map((consultation, idx) => (
                  <div key={idx} className="consultation-item">
                    <div className="consultation-marker"></div>
                    <div className="consultation-content">
                      <div className="consultation-header">
                        <h3>{consultation.agentName}</h3>
                        <span className="consultation-date">
                          {new Date(consultation.timestamp).toLocaleDateString('fr-FR', {
                            day: 'numeric',
                            month: 'long',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <p className="consultation-summary">{consultation.summary}</p>
                      {consultation.keyPoints.length > 0 && (
                        <div className="consultation-points">
                          <strong>Points clés :</strong>
                          <ul>
                            {consultation.keyPoints.map((point, i) => (
                              <li key={i}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="folder-actions">
          <button className="action-button action-button-secondary" onClick={onNewConsultation}>
            Nouvelle Consultation
          </button>
          <button className="action-button action-button-primary" onClick={handleDownload}>
            Télécharger le Dossier Complet
          </button>
        </div>
      </div>
    </div>
  );
};

export default FolderView;
