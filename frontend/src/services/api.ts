import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { QuestionnaireData, LoginRequest, AIProposalRequest } from '@/types';

// Custom error types for better error handling
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network connection failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(message: string, public field?: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Retry configuration
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // 1 second
  retryCondition: (error: AxiosError) => {
    // Retry on network errors or 5xx server errors
    return !error.response || (error.response.status >= 500 && error.response.status <= 599);
  },
};

// Input validation helpers
const validateRequired = (value: any, fieldName: string) => {
  if (!value || (typeof value === 'string' && !value.trim())) {
    throw new ValidationError(`${fieldName} is required`, fieldName);
  }
};

const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    throw new ValidationError('Invalid email format', 'email');
  }
};

// Retry helper
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  attempt: number = 1
): Promise<T> => {
  try {
    return await requestFn();
  } catch (error) {
    const axiosError = error as AxiosError;
    
    if (attempt < RETRY_CONFIG.maxRetries && RETRY_CONFIG.retryCondition(axiosError)) {
      await delay(RETRY_CONFIG.retryDelay * attempt);
      return retryRequest(requestFn, attempt + 1);
    }
    
    throw error;
  }
};

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    // Initialize axios instance with proper error handling
    try {
      this.api = axios.create({
        baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 seconds
      });
    } catch (error) {
      console.error('Failed to create axios instance:', error);
      throw new Error('Failed to initialize API service');
    }

    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      (config) => {
        // Get token from localStorage since AuthContext manages it there
        const authTokensStr = localStorage.getItem('auth_tokens');
        if (authTokensStr) {
          try {
            const authTokens = JSON.parse(authTokensStr);
            if (authTokens.access_token) {
              config.headers.Authorization = `Bearer ${authTokens.access_token}`;
            }
          } catch (error) {
            console.error('Failed to parse auth tokens:', error);
          }
        }
        return config;
      },
      (error) => {
        return Promise.reject(new NetworkError('Request configuration failed'));
      }
    );

    // Enhanced response interceptor for comprehensive error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        // Handle different types of errors
        if (!error.response) {
          // Network error
          if (error.code === 'ECONNABORTED') {
            return Promise.reject(new NetworkError('Request timeout'));
          }
          return Promise.reject(new NetworkError('Network connection failed'));
        }

        const { status, data } = error.response;
        const errorMessage = (data as any)?.detail || (data as any)?.message || error.message;

        // Handle specific HTTP status codes
        switch (status) {
          case 400:
            return Promise.reject(new ValidationError(errorMessage));
          case 401:
            // Authentication failed - let AuthContext handle this
            return Promise.reject(new APIError('Authentication required', 401, 'UNAUTHORIZED'));
          case 403:
            return Promise.reject(new APIError('Access forbidden', 403, 'FORBIDDEN'));
          case 404:
            return Promise.reject(new APIError('Resource not found', 404, 'NOT_FOUND'));
          case 422:
            return Promise.reject(new ValidationError(errorMessage, (data as any)?.field));
          case 429:
            return Promise.reject(new APIError('Too many requests - please try again later', 429, 'RATE_LIMITED'));
          case 500:
            return Promise.reject(new APIError('Internal server error', 500, 'INTERNAL_ERROR'));
          case 502:
          case 503:
          case 504:
            return Promise.reject(new APIError('Service temporarily unavailable', status, 'SERVICE_UNAVAILABLE'));
          default:
            return Promise.reject(new APIError(errorMessage, status, 'HTTP_ERROR', data));
        }
      }
    );
  }

  // Authentication status check
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    const authTokensStr = localStorage.getItem('auth_tokens');
    if (!authTokensStr) return false;
    try {
      const authTokens = JSON.parse(authTokensStr);
      return !!authTokens.access_token;
    } catch {
      return false;
    }
  }

  // Login method for compatibility (delegates to AuthContext)
  async login(credentials: LoginRequest): Promise<{
    access_token: string;
    user: {
      username: string;
      email: string;
      role: string;
    };
  }> {
    const response = await this.api.post('/auth/login', credentials);
    return response.data;
  }

  // Questionnaire methods
  async submitQuestionnaire(data: QuestionnaireData): Promise<{ message: string; savedAt: string }> {
    try {
      const response = await this.api.post('/questionnaire/submit', data);
      return response.data;
    } catch (error) {
      console.error('Failed to submit questionnaire:', error);
      throw new Error('Failed to submit questionnaire. Please try again.');
    }
  }

  async getQuestionnaireData(): Promise<QuestionnaireData | null> {
    try {
      const response = await this.api.get('/questionnaire/data');
      return response.data;
    } catch (error) {
      console.error('Failed to load questionnaire data:', error);
      return null;
    }
  }

  // AI Integration methods
  async generateAIProposal(request: AIProposalRequest): Promise<{
    suggestion: string;
    legalReferences: string[];
    consequences: string[];
    nextSteps: string[];
  }> {
    try {
      const response = await this.api.post('/ai/generate-proposal', request);
      return response.data;
    } catch (error) {
      console.error('Failed to generate AI proposal:', error);
      throw new Error('Failed to generate AI proposal. Please try again.');
    }
  }

  // Asset management methods
  async getAssetsSummary(): Promise<{
    totalValue: number;
    assetCount: number;
    assets: any[];
  }> {
    try {
      const response = await this.api.get('/assets/summary');
      return response.data;
    } catch (error) {
      console.error('Failed to get assets summary:', error);
      return { totalValue: 0, assetCount: 0, assets: [] };
    }
  }

  // Client management methods
  async getClients(page: number = 1, limit: number = 50, search?: string): Promise<{
    clients: any[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  }> {
    try {
      if (!this.api) {
        throw new Error('API service not initialized');
      }
      
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('limit', limit.toString());
      if (search) {
        params.append('search', search);
      }
      
      const response = await this.api.get(`/clients?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to load clients:', error);
      throw new Error('Failed to load clients. Please try again.');
    }
  }

  async searchClients(query: string): Promise<{
    clients: any[];
    total: number;
  }> {
    try {
      const response = await this.api.get(`/clients/search?q=${encodeURIComponent(query)}`);
      return response.data;
    } catch (error) {
      console.error('Failed to search clients:', error);
      throw new Error('Failed to search clients. Please try again.');
    }
  }

  async getClientDetails(clientId: string): Promise<any> {
    try {
      const response = await this.api.get(`/clients/${clientId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get client details:', error);
      throw new Error('Failed to get client details. Please try again.');
    }
  }

  async deleteClient(clientId: string): Promise<void> {
    try {
      await this.api.delete(`/clients/${clientId}`);
    } catch (error) {
      console.error('Failed to delete client:', error);
      throw new Error('Failed to delete client. Please try again.');
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('Backend service is not available.');
    }
  }

  // Dashboard statistics
  async getDashboardStatistics(): Promise<{
    statistics: {
      totalClients: number;
      completedQuestionnaires: number;
      aiProposalsGenerated: number;
      documentsCreated: number;
      activeUsers: number;
      systemUptime: string;
      recentClients: number;
    };
    recent_activities: Array<{
      type: string;
      description: string;
      time_ago: string;
      color: string;
    }>;
    clients_by_objective: Record<string, number>;
  }> {
    try {
      if (!this.api) {
        throw new Error('API service not initialized');
      }
      
      const response = await this.api.get('/dashboard/statistics');
      return response.data;
    } catch (error) {
      console.error('Failed to get dashboard statistics:', error);
      throw new Error('Failed to get dashboard statistics. Please try again.');
    }
  }

  // Generic API call method
  async apiCall<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any
  ): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.api.request({
        method: method.toLowerCase() as any,
        url: endpoint,
        data,
      });
      return response.data;
    } catch (error) {
      console.error(`API call failed [${method} ${endpoint}]:`, error);
      throw error;
    }
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;