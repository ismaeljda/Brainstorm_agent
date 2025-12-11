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
    const saved = localStorage.getItem('learningFolder');
    if (saved) {
      return JSON.parse(saved);
    }
    return {
      projectName: 'Mon Espace d\'Apprentissage',
      context: '',
      consultations: [],
      deliverables: [],
      documents: [],
      createdAt: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
    };
  });

  useEffect(() => {
    localStorage.setItem('learningFolder', JSON.stringify(businessPlanFolder));
  }, [businessPlanFolder]);

  const handleStartCall = (agent: Agent, context: string) => {
    setSelectedAgent(agent);
    setCompanyContext(context);

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
    setBusinessPlanFolder(prev => ({
      ...prev,
      consultations: [...prev.consultations, note],
      deliverables: [...prev.deliverables, deliverable],
      lastUpdated: new Date().toISOString(),
    }));

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
