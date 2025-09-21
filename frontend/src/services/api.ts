import axios from 'axios';
import { ProductComparisonRequest } from '../types';

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
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
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.error('Unauthorized access');
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// Analysis-related API calls
export const analysisAPI = {
  // Start a new analysis
  startAnalysis: (analysisData: any) => 
    api.post('/analysis', analysisData),
  
  // Get analysis status
  getAnalysisStatus: (requestId: string) => 
    api.get(`/analysis/${requestId}/status`),
  
  // Get analysis result
  getAnalysisResult: (requestId: string) => 
    api.get(`/analysis/${requestId}`),
  
  // List all analyses
  listAnalyses: (params?: any) => 
    api.get('/analysis', { params }),
  
  // Get competitors for an analysis
  getAnalysisCompetitors: (requestId: string) => 
    api.get(`/analysis/${requestId}/competitors`),
  
  // Get recommendations for an analysis
  getAnalysisRecommendations: (requestId: string) => 
    api.get(`/analysis/${requestId}/recommendations`),
  
  // Delete an analysis
  deleteAnalysis: (requestId: string) => 
    api.delete(`/analysis/${requestId}`),
  
  // Get search logs for debugging
  getSearchLogs: (requestId: string) => 
    api.get(`/analysis/${requestId}/search-logs`),
  
  // Restart an analysis
  restartAnalysis: (requestId: string) => 
    api.post(`/analysis/${requestId}/restart`),
  
  // Get quality review data
  getQualityReview: (requestId: string) =>
    api.get(`/analysis/${requestId}/quality-review`),
  
  // Submit quality review decision
  submitQualityDecision: (requestId: string, decision: any) =>
    api.post(`/analysis/${requestId}/quality-review/decision`, decision),
  
  // Demo mode management
  getDemoModeStatus: () => 
    api.get('/demo-mode/status'),
  
  toggleDemoMode: () => 
    api.post('/demo-mode/toggle'),
};

// Product-related API calls
export const productsAPI = {
  // Start a new product comparison
  startProductComparison: (comparisonData: ProductComparisonRequest) => 
    api.post('/product-comparison', comparisonData),
  
  // Get list of products
  listProducts: (params?: { category?: string; company?: string; limit?: number }) => 
    api.get('/products', { params }),
  
  // Get specific product details
  getProduct: (productId: string) => 
    api.get(`/products/${productId}`),
  
  // Update product details
  updateProduct: (productId: string, updates: any) => 
    api.put(`/products/${productId}`, { product_id: productId, updates }),
  
  // Compare two products directly
  compareProducts: (productId: string, competitorId: string, criteria?: string[]) => 
    api.post(`/products/${productId}/compare/${competitorId}`, null, { 
      params: criteria ? { criteria } : {} 
    }),
  
  // Get product comparison results
  getProductComparisonResults: (requestId: string) => 
    api.get(`/product-comparisons/${requestId}`),
};

// Reports-related API calls
export const reportsAPI = {
  // List all reports
  listReports: (params?: any) => 
    api.get('/reports', { params }),
  
  // Get a specific report
  getReport: (reportId: string) => 
    api.get(`/reports/${reportId}`),
  
  // Get report by analysis ID
  getReportByAnalysis: (analysisId: string) => 
    api.get(`/analysis/${analysisId}/report`),
  
  // Get executive summary
  getExecutiveSummary: (reportId: string) => 
    api.get(`/reports/${reportId}/executive-summary`),
  
  // Get specific report section
  getReportSection: (reportId: string, sectionName: string) => 
    api.get(`/reports/${reportId}/sections/${sectionName}`),
  
  // Get competitor profiles
  getCompetitorProfiles: (reportId: string) => 
    api.get(`/reports/${reportId}/competitor-profiles`),
  
  // Get report statistics
  getReportStatistics: () => 
    api.get('/reports/statistics'),
  
  // Generate new report
  generateReport: (analysisId: string) => 
    api.post(`/analysis/${analysisId}/generate-report`),
};

// WebSocket connection for real-time updates
export class AnalysisWebSocket {
  private ws: WebSocket | null = null;
  private requestId: string;
  private onMessage: (data: any) => void;
  private onError: (error: any) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(
    requestId: string, 
    onMessage: (data: any) => void, 
    onError: (error: any) => void = console.error
  ) {
    this.requestId = requestId;
    this.onMessage = onMessage;
    this.onError = onError;
  }

  connect() {
    try {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
      this.ws = new WebSocket(`${wsUrl}/ws/analysis/${this.requestId}`);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for analysis ${this.requestId}`);
        this.reconnectAttempts = 0;
        
        // Send initial ping
        this.send({ type: 'ping' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        
        // Attempt to reconnect if not manually closed
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            this.connect();
          }, 1000 * Math.pow(2, this.reconnectAttempts)); // Exponential backoff
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.onError(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.onError(error);
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  getStatus() {
    this.send({ type: 'get_status' });
  }
}

// Health check
export const healthCheck = () => api.get('/health', { baseURL: 'http://localhost:8000' });

// Helper functions for common operations
export const startProductComparison = async (comparisonData: ProductComparisonRequest) => {
  const response = await productsAPI.startProductComparison(comparisonData);
  return response.data;
};

export default api;