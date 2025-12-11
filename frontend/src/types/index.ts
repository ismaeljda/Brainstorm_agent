export interface Agent {
  id: string;
  name: string;
  icon: string;
  description: string;
  avatarId: string;
  voiceId: string;
  llmId: string;
  systemPrompt: string;
}

export interface UploadedDocument {
  id: string;
  filename: string;
  status: 'uploading' | 'ready' | 'failed';
  chunks?: number;
  error?: string;
}

export interface CompanyContext {
  description: string;
  documents: UploadedDocument[];
}

export interface SearchResult {
  text: string;
  source: string;
  relevance: number;
}

export interface ConsultationNote {
  agentId: string;
  agentName: string;
  timestamp: string;
  summary: string;
  keyPoints: string[];
  recommendations: string[];
  nextSteps: string[];
}

export interface WorkDeliverable {
  id: string;
  type: 'lesson' | 'exercise' | 'summary' | 'quiz';
  title: string;
  content: string;
  agentId: string;
  createdAt: string;
  status: 'generating' | 'ready' | 'failed';
}

export interface BusinessPlanFolder {
  projectName: string;
  context: string;
  consultations: ConsultationNote[];
  deliverables: WorkDeliverable[];
  documents: UploadedDocument[];
  createdAt: string;
  lastUpdated: string;
}
