/**
 * Service WebSocket pour streaming temps réel
 */

import { config } from '../config';

export type WebSocketMessage =
  | { type: 'connected'; job_id: string; message: string }
  | { type: 'turn'; agent: string; text: string; audio_url?: string; job_id: string }
  | { type: 'end'; job_id: string; summary: string; turns: number }
  | { type: 'completed'; job_id: string; result: any }
  | { type: 'error'; error: string };

export type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: MessageHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(jobId: string): void {
    const WS_BASE_URL = config.api.wsUrl;
    const url = `${WS_BASE_URL}/ws/meeting/${jobId}`;

    console.log('🔌 Connexion WebSocket:', url);

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connecté');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('📨 Message reçu:', message);

        // Notifier tous les handlers
        this.handlers.forEach(handler => handler(message));

        // Auto-fermer si message de fin
        if (message.type === 'end' || message.type === 'completed') {
          console.log('🏁 Fin de la réunion');
          setTimeout(() => this.disconnect(), 1000);
        }
      } catch (error) {
        console.error('❌ Erreur parsing message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ Erreur WebSocket:', error);
    };

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket fermé:', event.code, event.reason);

      // Tentative de reconnexion si fermeture anormale
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`🔄 Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);

        setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CLOSED) {
            this.connect(jobId);
          }
        }, this.reconnectDelay * this.reconnectAttempts);
      }
    };
  }

  disconnect(): void {
    if (this.ws) {
      console.log('🔌 Fermeture WebSocket');
      this.ws.close();
      this.ws = null;
    }
    this.handlers = [];
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.push(handler);

    // Retourner fonction de cleanup
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('❌ WebSocket non connecté');
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
export default wsService;
