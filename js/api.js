class APIClient {
    async processPayment(data) {
        const response = await fetch(`${API_BASE}/api/v1/payment/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    }
}

/**
 * Propósito: Cliente unificado para comunicação com a API backend
 * 
 * Funcionalidades:
 * Fetch wrapper com auth token automático
 * Reconexão automática de WebSocket
 * Tratamento de erros padronizado
 * Timeout configurável por endpoint
 * Logging opcional para debug
 */

// Configuração base
const API_CONFIG = {
  baseURL: import.meta.env?.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,  // 10 segundos padrão
  retries: 3,      // Tentativas de retry em falha de rede
};

// Token de autenticação (armazenado seguro)
let authToken = null;
export const setAuthToken = (token) => { authToken = token; };
export const getAuthToken = () => authToken;

// Fetch wrapper com auth e retry
export async function apiFetch(endpoint, options = {}) {
  const url = `${API_CONFIG.baseURL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(authToken && { 'Authorization': `Bearer ${authToken}` }),
      ...options.headers,
    },
    signal: AbortSignal.timeout(API_CONFIG.timeout),
    ...options,
  };
  
  // Retry logic
  let lastError;
  for (let attempt = 1; attempt <= API_CONFIG.retries; attempt++) {
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(response.status, error.detail || 'Request failed');
      }
      
      return await response.json();
      
    } catch (error) {
      lastError = error;
      if (attempt === API_CONFIG.retries) break;
      
      // Backoff exponencial antes de retry
      await new Promise(resolve => 
        setTimeout(resolve, Math.pow(2, attempt) * 100)
      );
    }
  }
  
  throw lastError;
}

// Classe de erro customizada
export class ApiError extends Error {
  constructor(status, message, details = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

// === WebSocket Manager ===
export class PaymentWebSocket {
  constructor(userId, onProgress, onResult, onError) {
    this.userId = userId;
    this.onProgress = onProgress;
    this.onResult = onResult;
    this.onError = onError;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnects = 5;
  }
  
  connect() {
    const wsUrl = `${API_CONFIG.baseURL.replace('http', 'ws')}/ws/payment/${this.userId}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('✅ WebSocket conectado');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress' && this.onProgress) {
          this.onProgress(data);
        } else if (data.type === 'result' && this.onResult) {
          this.onResult(data);
          this.close();
        }
      } catch (err) {
        console.error('❌ Erro ao processar mensagem WebSocket:', err);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      this._handleReconnect();
    };
    
    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnects) {
        this._handleReconnect();
      }
    };
  }
  
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('⚠️ WebSocket não está aberto, mensagem não enviada');
    }
  }
  
  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  _handleReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 10000);
    
    console.log(`🔄 Tentando reconectar em ${delay}ms... (${this.reconnectAttempts}/${this.maxReconnects})`);
    
    setTimeout(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        this.connect();
      }
    }, delay);
  }
}

// === Helpers de utilidade ===
export const formatCurrency = (value) => 
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

export const formatMs = (ms) => 
  ms < 1 ? `${ms.toFixed(3)} ms` : `${ms.toFixed(1)} ms`;

export const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
