const API_BASE = import.meta.env?.VITE_API_BASE_URL || 'http://localhost:8000';

class APIClient {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('finoraqi_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
            ...options.headers
        };
        
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erro na requisição');
        }
        
        return await response.json();
    }
    
    async processPayment(data) {
        return this.request('/api/v1/payment/process', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    async uploadSpreadsheet(file, options) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('options', JSON.stringify(options));
        
        return this.request('/api/v1/spreadsheet/upload', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }
}
