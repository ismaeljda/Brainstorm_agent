import { useState, useEffect } from 'react';
import SetupScreen from './components/SetupScreen';
import CallScreen from './components/CallScreen';
import FolderView from './components/FolderView';
import type { Agent, BusinessPlanFolder, ConsultationNote, WorkDeliverable } from './types';
import './App.css';

function App() {
  const [currentScreen, setCurrentScreen] = useState<'setup' | 'call' | 'folder'>('setup');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [companyContext, setCompanyContext] = useState('');
  const [businessPlanFolder, setBusinessPlanFolder] = useState<BusinessPlanFolder>(() => {
    // Charger le dossier depuis le localStorage si disponible
    const saved = localStorage.getItem('businessPlanFolder');
    if (saved) {
      return JSON.parse(saved);
    }
    return {
      projectName: 'Mon Business Plan',
      context: '',
      consultations: [],
      deliverables: [],
      documents: [],
      createdAt: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
    };
  });

  // Sauvegarder le dossier dans le localStorage à chaque modification
  useEffect(() => {
    localStorage.setItem('businessPlanFolder', JSON.stringify(businessPlanFolder));
  }, [businessPlanFolder]);

  const handleStartCall = (agent: Agent, context: string) => {
    setSelectedAgent(agent);
    setCompanyContext(context);

    // Mettre à jour le contexte du dossier s'il a changé
    if (context !== businessPlanFolder.context) {
      setBusinessPlanFolder(prev => ({
        ...prev,
        context,
        lastUpdated: new Date().toISOString(),
      }));
    }

    setCurrentScreen('call');
  };

  const handleEndCall = () => {
    setCurrentScreen('setup');
    setSelectedAgent(null);
  };

  const handleConsultationComplete = (note: ConsultationNote, deliverable: WorkDeliverable) => {
    // Ajouter la consultation et le livrable au dossier
    setBusinessPlanFolder(prev => ({
      ...prev,
      consultations: [...prev.consultations, note],
      deliverables: [...prev.deliverables, deliverable],
      lastUpdated: new Date().toISOString(),
    }));

    // Afficher le dossier
    setCurrentScreen('folder');
    setSelectedAgent(null);
  };

  const handleViewFolder = () => {
    setCurrentScreen('folder');
  };

  const handleCloseFolder = () => {
    setCurrentScreen('setup');
  };

  const handleNewConsultation = () => {
    setCurrentScreen('setup');
  };

  return (
    <div className="app">
      {currentScreen === 'setup' && (
        <SetupScreen
          onStartCall={handleStartCall}
          onViewFolder={businessPlanFolder.consultations.length > 0 ? handleViewFolder : undefined}
        />
      )}
      {currentScreen === 'call' && selectedAgent && (
        <CallScreen
          agent={selectedAgent}
          context={companyContext}
          onEndCall={handleEndCall}
          onConsultationComplete={handleConsultationComplete}
        />
      )}
      {currentScreen === 'folder' && (
        <FolderView
          folder={businessPlanFolder}
          onClose={handleCloseFolder}
          onNewConsultation={handleNewConsultation}
        />
      )}
    </div>
  );
}

export default App;
