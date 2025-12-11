import { useState } from 'react';
import SetupScreen from './components/SetupScreen';
import CallScreen from './components/CallScreen';
import type { Agent } from './types';
import './App.css';

function App() {
  const [currentScreen, setCurrentScreen] = useState<'setup' | 'call'>('setup');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [companyContext, setCompanyContext] = useState('');

  const handleStartCall = (agent: Agent, context: string) => {
    setSelectedAgent(agent);
    setCompanyContext(context);
    setCurrentScreen('call');
  };

  const handleEndCall = () => {
    setCurrentScreen('setup');
    setSelectedAgent(null);
    setCompanyContext('');
  };

  return (
    <div className="app">
      {currentScreen === 'setup' && <SetupScreen onStartCall={handleStartCall} />}
      {currentScreen === 'call' && selectedAgent && (
        <CallScreen agent={selectedAgent} context={companyContext} onEndCall={handleEndCall} />
      )}
    </div>
  );
}

export default App;
