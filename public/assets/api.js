/**
 * Propósito: Utilitários de autenticação e gerenciamento de tokens
 * 
 * Funcionalidades:
 * ✅ Armazenamento seguro de token (localStorage com fallback)
 * ✅ Refresh automático de token expirado
 * ✅ Logout com limpeza de estado
 * ✅ Verificação de permissões por role
 */

// Storage wrapper com fallback
const Storage = {
  get: (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      return sessionStorage.getItem(key);
    }
  },
  set: (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch {
      sessionStorage.setItem(key, value);
    }
  },
  remove: (key) => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  }
};

// Gerenciamento de token JWT
export const auth = {
  // Salva token + dados do usuário
  login: (token, userData) => {
    Storage.set('finoraqi_token', token);
    Storage.set('finoraqi_user', JSON.stringify(userData));
    
    // Configura expiry (24h padrão)
    const expiry = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    Storage.set('finoraqi_token_expiry', expiry);
  },
  
  // Recupera token válido (com refresh se necessário)
  getToken: async () => {
    const token = Storage.get('finoraqi_token');
    const expiry = Storage.get('finoraqi_token_expiry');
    
    if (!token || !expiry) return null;
    
    // Se expirou, tenta refresh
    if (new Date() > new Date(expiry)) {
      return await auth.refreshToken();
    }
    
    return token;
  },
  
  // Refresh token via API
  refreshToken: async () => {
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${Storage.get('finoraqi_token')}` }
      });
      
      if (response.ok) {
        const { token, expiry } = await response.json();
        Storage.set('finoraqi_token', token);
        Storage.set('finoraqi_token_expiry', expiry);
        return token;
      }
    } catch (error) {
      console.error('❌ Falha ao refresh token:', error);
    }
    
    // Se falhar, faz logout
    auth.logout();
    return null;
  },
  
  // Logout: limpa tudo e redireciona
  logout: () => {
    Storage.remove('finoraqi_token');
    Storage.remove('finoraqi_token_expiry');
    Storage.remove('finoraqi_user');
    
    // Redireciona para login se não estiver já
    if (!window.location.pathname.includes('index.html')) {
      window.location.href = 'index.html';
    }
  },
  
  // Verifica se usuário tem permissão
  hasPermission: (requiredRole) => {
    const user = JSON.parse(Storage.get('finoraqi_user') || '{}');
    const roles = user.roles || [];
    
    // Admin tem tudo
    if (roles.includes('admin')) return true;
    
    return roles.includes(requiredRole);
  },
  
  // Dados do usuário logado
  getUser: () => {
    try {
      return JSON.parse(Storage.get('finoraqi_user'));
    } catch {
      return null;
    }
  }
};

// Inicialização: verifica sessão ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
  const token = Storage.get('finoraqi_token');
  const isAuthPage = window.location.pathname.includes('index.html');
  
  if (token && isAuthPage) {
    // Já logado e na landing page → vai pro dashboard
    window.location.href = 'dashboard.html';
  } else if (!token && !isAuthPage) {
    // Não logado e em página protegida → volta pro login
    window.location.href = 'index.html';
  }
});