import axios from 'axios';
import type { UploadedDocument, SearchResult } from '../types';

const RAG_API = 'http://localhost:5000';
const ANAM_API = 'https://api.anam.ai/v1';
const ANAM_API_KEY = 'YmFkOTliNzQtNDc3Mi00YmNkLTlhODctZDBiN2YwZWIzMDNmOnlPVzlTVTJ1bHpJYVZlS0pSN0ZjWWxKUGlpR24rVHVvT1ZKb3RoZ0ZFY3c9';

// RAG API
export const uploadDocument = async (file: File): Promise<UploadedDocument> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${RAG_API}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return {
    id: response.data.documentId,
    filename: response.data.filename,
    status: 'ready',
    chunks: response.data.chunks,
  };
};

export const searchDocuments = async (query: string, topK: number = 3): Promise<SearchResult[]> => {
  const response = await axios.post(`${RAG_API}/search`, {
    query,
    top_k: topK,
  });

  return response.data.results.map((r: any) => ({
    text: r.text,
    source: r.filename,
    relevance: r.score,
  }));
};

export const listDocuments = async (): Promise<UploadedDocument[]> => {
  const response = await axios.get(`${RAG_API}/documents`);
  return response.data.map((doc: any) => ({
    id: doc.id,
    filename: doc.filename,
    status: 'ready' as const,
    chunks: doc.chunks_count,
  }));
};

// ANAM API
export const createSessionToken = async (personaConfig: any): Promise<string> => {
  const response = await axios.post(
    `${ANAM_API}/auth/session-token`,
    { personaConfig },
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${ANAM_API_KEY}`,
      },
    }
  );

  return response.data.sessionToken;
};
