import axios from 'axios';

// Configure axios base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout for LLM queries
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API functions
export const checkHealth = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export const getSystemStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};

export const queryRAGSystem = async (question, k = 5) => {
  const response = await api.post('/api/query', {
    question,
    k
  });
  return response.data;
};

export const getDocuments = async () => {
  const response = await api.get('/api/documents');
  return response.data;
};

export const getConfiguration = async () => {
  const response = await api.get('/api/config');
  return response.data;
};

// RAG Management API functions
export const getRAGFiles = async () => {
  const response = await api.get('/api/rag/files');
  return response.data;
};

export const getRAGStats = async () => {
  const response = await api.get('/api/rag/stats');
  return response.data;
};

export const uploadFiles = async (files, onProgress = null) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await api.post('/api/rag/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });
  return response.data;
};

export const deleteFile = async (fileId) => {
  const response = await api.delete(`/api/rag/files/${fileId}`);
  return response.data;
};

export const rebuildRAGSystem = async () => {
  const response = await api.post('/api/rag/rebuild', {}, {
    timeout: 300000, // 5 minutes for rebuild
  });
  return response.data;
};

export const resetRAGSystem = async () => {
  const response = await api.post('/api/rag/reset');
  return response.data;
};

export default api;