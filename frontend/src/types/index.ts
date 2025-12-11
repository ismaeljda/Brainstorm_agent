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
