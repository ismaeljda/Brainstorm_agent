/**
 * Service API HTTP avec authentification Firebase
 */

import axios, { AxiosInstance } from 'axios';
import { auth } from '../firebase';
import { config } from '../config';

// Configuration de base
const API_BASE_URL = config.api.baseUrl;

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Intercepteur pour ajouter le token Firebase
    this.client.interceptors.request.use(
      async (config) => {
        const user = auth.currentUser;

        if (user) {
          try {
            const token = await user.getIdToken();
            config.headers.Authorization = `Bearer ${token}`;
          } catch (error) {
            console.error('Erreur récupération token:', error);
          }
        }

        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // ==================== MEETINGS ====================

  async startMeeting(objective: string): Promise<{
    job_id: string;
    websocket_url: string;
  }> {
    const response = await this.client.post('/api/v1/start_meeting', {
      objective,
    });
    return response.data;
  }

  async getMeetingStatus(jobId: string) {
    const response = await this.client.get(`/api/v1/meeting_status/${jobId}`);
    return response.data;
  }

  // ==================== DOCUMENTS ====================

  async uploadDocument(file: File): Promise<{
    job_id: string;
    doc_id: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post('/api/v1/upload_document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async searchContext(query: string, topK: number = 5) {
    const response = await this.client.post('/api/context/search', {
      query,
      top_k: topK,
    });
    return response.data;
  }

  async deleteDocument(filename: string) {
    const response = await this.client.delete(`/api/context/document/${filename}`);
    return response.data;
  }

  // ==================== CONTEXT ====================

  async getContext() {
    const response = await this.client.get('/api/context');
    return response.data;
  }

  async saveContext(context: any) {
    const response = await this.client.post('/api/context', {
      context,
    });
    return response.data;
  }

  async deleteContext() {
    const response = await this.client.delete('/api/context');
    return response.data;
  }

  // ==================== HEALTH ====================

  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const apiService = new APIService();
export default apiService;
