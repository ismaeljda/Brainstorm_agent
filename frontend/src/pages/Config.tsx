/**
 * Page de configuration de la réunion
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { ref, uploadBytes } from 'firebase/storage';
import { storage } from '../firebase';

export const ConfigPage: React.FC = () => {
  const navigate = useNavigate();

  // État du formulaire
  const [objective, setObjective] = useState('');
  const [contextStatic, setContextStatic] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);

  // Upload de fichier pour RAG
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploadingFile(true);

    try {
      for (const file of Array.from(files)) {
        // Upload vers backend pour indexation RAG
        const result = await apiService.uploadDocument(file);
        console.log('📄 Document uploadé:', result);

        // Optionnel : aussi uploader vers Firebase Storage
        const storageRef = ref(storage, `documents/${file.name}`);
        await uploadBytes(storageRef, file);

        setUploadedFiles(prev => [...prev, file.name]);
      }

      alert('Document(s) uploadé(s) et indexé(s) avec succès !');
    } catch (error) {
      console.error('Erreur upload:', error);
      alert('Erreur lors de l\'upload');
    } finally {
      setUploadingFile(false);
    }
  };

  // Démarrer la réunion
  const handleStartMeeting = async () => {
    if (!objective.trim()) {
      alert('Veuillez saisir un objectif de réunion');
      return;
    }

    setLoading(true);

    try {
      // Sauvegarder le contexte statique seulement si rempli
      if (contextStatic.trim()) {
        try {
          await apiService.saveContext({
            company_name: 'Ma Société',
            description: contextStatic,
            values: [],
            constraints: [],
            objectives: [objective]
          });
        } catch (error) {
          console.warn('Erreur sauvegarde contexte (ignorée):', error);
          // On continue même si ça échoue
        }
      }

      // Démarrer la réunion via Celery + WebSocket
      const result = await apiService.startMeeting(objective);

      console.log('🚀 Réunion démarrée:', result);

      // Naviguer vers la page de meeting avec le vrai job_id
      navigate(`/meeting/${result.job_id}`);
    } catch (error) {
      console.error('Erreur démarrage réunion:', error);
      alert('Erreur lors du démarrage de la réunion. Vérifiez que le backend est lancé.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🧠 BrainStormIA
          </h1>
          <p className="text-gray-600">
            Configurez votre réunion multi-agents augmentée par IA
          </p>
        </div>

        {/* Formulaire */}
        <div className="bg-white rounded-lg shadow-lg p-8 space-y-6">
          {/* Objectif */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Objectif de la réunion *
            </label>
            <input
              type="text"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Ex: Lancer une nouvelle app mobile de fitness"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg
                       focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Contexte Statique */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Contexte d'entreprise (injection directe)
            </label>
            <textarea
              value={contextStatic}
              onChange={(e) => setContextStatic(e.target.value)}
              placeholder="Ex: Nous sommes une startup fintech qui souhaite se lancer dans le B2C..."
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg
                       focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <p className="text-sm text-gray-500 mt-1">
              Ce contexte sera directement injecté dans les prompts des agents
            </p>
          </div>

          {/* Upload Documents RAG */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Documents de contexte (RAG)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6
                          hover:border-primary transition-colors">
              <input
                type="file"
                onChange={handleFileUpload}
                multiple
                accept=".pdf,.txt,.doc,.docx,.xls,.xlsx"
                disabled={uploadingFile}
                className="block w-full text-sm text-gray-500
                         file:mr-4 file:py-2 file:px-4
                         file:rounded-lg file:border-0
                         file:text-sm file:font-semibold
                         file:bg-primary file:text-white
                         hover:file:bg-primary/90
                         disabled:opacity-50"
              />
              <p className="text-sm text-gray-500 mt-2">
                {uploadingFile
                  ? 'Upload en cours...'
                  : 'PDF, TXT, DOC, DOCX, XLS, XLSX (max 16MB)'}
              </p>
            </div>

            {/* Liste des fichiers uploadés */}
            {uploadedFiles.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Fichiers indexés ({uploadedFiles.length}) :
                </p>
                <ul className="space-y-1">
                  {uploadedFiles.map((file, idx) => (
                    <li key={idx} className="text-sm text-gray-600 flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      {file}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Agents (optionnel - pour affichage) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Agents participants
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'facilitateur', name: 'Facilitateur', emoji: '🎯' },
                { id: 'strategie', name: 'Stratège Business', emoji: '💼' },
                { id: 'tech', name: 'Tech Lead', emoji: '💻' },
                { id: 'creatif', name: 'Creative Thinker', emoji: '🎨' },
              ].map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg
                           bg-gray-50"
                >
                  <span className="text-2xl">{agent.emoji}</span>
                  <span className="text-sm font-medium">{agent.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bouton Démarrer */}
          <button
            onClick={handleStartMeeting}
            disabled={loading || !objective.trim()}
            className="w-full py-3 px-6 bg-primary text-white font-semibold rounded-lg
                     hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          >
            {loading ? 'Démarrage en cours...' : '🚀 Démarrer la réunion'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfigPage;
