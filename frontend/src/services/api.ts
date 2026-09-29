import axios from 'axios';
import {
  User,
  DashboardSummary,
  AuditDossier,
  Alert,
  SwarmStatusResponse,
  SystemHealth,
  BenchmarkDataset,
  SyntheticScenario,
  GeneratedReport,
  AuditSummaryItem,
  RegisteredDataset
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to outgoing requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('dataguard_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Clean session expiration handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      if (!url.includes('/auth/login')) {
        localStorage.removeItem('dataguard_token');
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Authentication & RBAC
  auth: {
    login: async (email: string, password: string) => {
      const res = await apiClient.post('/auth/login', { email, password });
      return res.data;
    },
    register: async (data: { email: string; full_name: string; password: string; role: string }) => {
      const res = await apiClient.post('/auth/register', data);
      return res.data;
    },
    getMe: async (): Promise<User> => {
      const res = await apiClient.get('/auth/me');
      return res.data;
    },
    seedDemoUsers: async () => {
      const res = await apiClient.post('/auth/seed-demo-users');
      return res.data;
    },
  },

  // Multi-Agent & Dashboard Operations
  agents: {
    getDashboardSummary: async (): Promise<DashboardSummary> => {
      const res = await apiClient.get('/agents/dashboard/summary');
      return res.data;
    },
    getSwarmStatus: async (): Promise<SwarmStatusResponse> => {
      const res = await apiClient.get('/agents/status');
      return res.data;
    },
    getHealth: async (): Promise<SystemHealth> => {
      const res = await apiClient.get('/agents/health');
      return res.data;
    },
    getLatestAudit: async (): Promise<AuditDossier> => {
      const res = await apiClient.get('/agents/audits/latest');
      return res.data;
    },
    getAuditById: async (id: string): Promise<AuditDossier> => {
      const res = await apiClient.get(`/agents/audits/${id}`);
      return res.data;
    },
    listAudits: async (): Promise<AuditSummaryItem[]> => {
      const res = await apiClient.get('/agents/audits');
      return res.data;
    },
    getReports: async (): Promise<GeneratedReport[]> => {
      const res = await apiClient.get('/agents/reports');
      return res.data;
    },
    orchestrateAudit: async (dataset_path: string, limit: number = 1000): Promise<AuditDossier> => {
      const res = await apiClient.post('/agents/orchestrate', { dataset_path, limit });
      return res.data;
    },
    simulatePipeline: async (dataset_path: string, mode: string, sample_size: number = 500) => {
      const res = await apiClient.post('/agents/simulate', { dataset_path, mode, sample_size });
      return res.data;
    },
    chatCopilot: async (query: string, context?: any) => {
      const res = await apiClient.post('/agents/copilot/chat', { query, context });
      return res.data;
    },
    executeRecovery: async (dataset_path: string, actions: any[]) => {
      const res = await apiClient.post('/agents/recovery/execute', { dataset_path, actions });
      return res.data;
    },
    getAlerts: async (): Promise<{ count: number; alerts: Alert[] }> => {
      const res = await apiClient.get('/agents/alerts');
      return res.data;
    },
    markAlertsRead: async () => {
      const res = await apiClient.post('/agents/alerts/mark-read');
      return res.data;
    },
    getReportDownloadUrl: (filename: string) => {
      return `${API_BASE_URL}/agents/reports/download/${filename}`;
    },
  },

  // Dataset Registry
  datasets: {
    list: async (): Promise<RegisteredDataset[]> => {
      const res = await apiClient.get('/datasets/');
      return res.data;
    },
    create: async (data: any): Promise<RegisteredDataset> => {
      const res = await apiClient.post('/datasets/', data);
      return res.data;
    },
    upload: async (file: File): Promise<RegisteredDataset> => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post('/datasets/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return res.data;
    },
    getBenchmarks: async (): Promise<BenchmarkDataset[]> => {
      const res = await apiClient.get('/datasets/benchmarks');
      return res.data;
    },
    getSyntheticScenarios: async (): Promise<SyntheticScenario[]> => {
      const res = await apiClient.get('/datasets/synthetic-scenarios');
      return res.data;
    },
  },
};
