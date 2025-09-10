/**
 * API Client Service
 * HTTP client for communicating with the backend REST API.
 * Provides type-safe methods for all API endpoints.
 *
 * Features:
 * - Type-safe API calls
 * - Request/response interceptors
 * - Error handling
 * - Authentication support
 * - Automatic JSON serialization
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// Base types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
  timestamp: string;
}

// Trading Signal types
export interface TradingSignal {
  id: string;
  timestamp: string;
  symbol: string;
  direction: 'UP' | 'DOWN';
  predicted_probability: number;
  confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
  expiry_time: string;
  metadata?: Record<string, any>;
}

export interface GenerateSignalRequest {
  symbol: string;
  timeframe?: string;
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  custom_parameters?: Record<string, any>;
}

// Market Data types
export interface MarketDataPoint {
  timestamp: string;
  symbol: string;
  price: number;
  volume?: number;
  bid?: number;
  ask?: number;
  high?: number;
  low?: number;
  open?: number;
  close?: number;
}

export interface MarketDataRequest {
  symbols: string[];
  start_time?: string;
  end_time?: string;
  timeframe?: string;
  include_volume?: boolean;
}

export interface StreamMarketDataRequest {
  symbols: string[];
  stream_type: 'real_time' | 'historical';
  callback_url?: string;
}

// Risk Parameters types
export interface RiskParameters {
  id: string;
  max_position_size: number;
  stop_loss_percentage: number;
  take_profit_percentage: number;
  max_daily_loss: number;
  max_concurrent_trades: number;
  min_confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
  created_at: string;
  updated_at: string;
}

export interface UpdateRiskParametersRequest {
  max_position_size?: number;
  stop_loss_percentage?: number;
  take_profit_percentage?: number;
  max_daily_loss?: number;
  max_concurrent_trades?: number;
  min_confidence_level?: 'LOW' | 'MEDIUM' | 'HIGH';
}

// Backtest types
export interface BacktestRequest {
  name: string;
  description?: string;
  strategy_config: Record<string, any>;
  start_date: string;
  end_date: string;
  initial_capital: number;
  symbols: string[];
  risk_parameters?: Partial<RiskParameters>;
}

export interface BacktestResult {
  id: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  metrics?: {
    total_return: number;
    annualized_return: number;
    max_drawdown: number;
    sharpe_ratio: number;
    win_rate: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    avg_win: number;
    avg_loss: number;
    profit_factor: number;
    start_date: string;
    end_date: string;
    initial_capital: number;
    final_capital: number;
  };
  trades?: Array<{
    id: string;
    entry_time: string;
    exit_time: string;
    symbol: string;
    direction: 'UP' | 'DOWN';
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
    pnl_percentage: number;
    result: 'WIN' | 'LOSS';
  }>;
  portfolio_values?: Array<{
    date: string;
    value: number;
    return_pct: number;
  }>;
  created_at: string;
  updated_at: string;
}

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        return response;
      },
      (error) => {
        const apiError: ApiError = {
          message: error.response?.data?.message || error.message || 'An unknown error occurred',
          code: error.response?.data?.code,
          details: error.response?.data?.details,
          timestamp: new Date().toISOString(),
        };

        if (error.response?.status === 401) {
          // Handle authentication error
          this.handleAuthError();
        }

        return Promise.reject(apiError);
      }
    );
  }

  private getAuthToken(): string | null {
    // Get token from localStorage, sessionStorage, or cookies
    return localStorage.getItem('authToken');
  }

  private handleAuthError(): void {
    // Clear auth token and redirect to login if needed
    localStorage.removeItem('authToken');
    // Optionally redirect to login page
  }

  // Generic request method
  private async request<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.request<ApiResponse<T>>({
      method,
      url,
      data,
      ...config,
    });

    return response.data.data;
  }

  // Trading Signals API
  async getSignals(page = 1, pageSize = 50): Promise<PaginatedResponse<TradingSignal>> {
    const response = await this.client.get<PaginatedResponse<TradingSignal>>('/signals', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async generateSignal(request: GenerateSignalRequest): Promise<TradingSignal> {
    return this.request<TradingSignal>('POST', '/signals/generate', request);
  }

  // Market Data API
  async getMarketData(request: MarketDataRequest): Promise<MarketDataPoint[]> {
    return this.request<MarketDataPoint[]>('GET', '/market-data', null, {
      params: request,
    });
  }

  async streamMarketData(request: StreamMarketDataRequest): Promise<{ stream_id: string }> {
    return this.request<{ stream_id: string }>('POST', '/market-data/stream', request);
  }

  // Risk Parameters API
  async getRiskParameters(): Promise<RiskParameters> {
    return this.request<RiskParameters>('GET', '/risk-parameters');
  }

  async updateRiskParameters(request: UpdateRiskParametersRequest): Promise<RiskParameters> {
    return this.request<RiskParameters>('PUT', '/risk-parameters', request);
  }

  // Backtests API
  async createBacktest(request: BacktestRequest): Promise<BacktestResult> {
    return this.request<BacktestResult>('POST', '/backtests', request);
  }

  async getBacktest(id: string): Promise<BacktestResult> {
    return this.request<BacktestResult>('GET', `/backtests/${id}`);
  }

  async getBacktests(page = 1, pageSize = 20): Promise<PaginatedResponse<BacktestResult>> {
    const response = await this.client.get<PaginatedResponse<BacktestResult>>('/backtests', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('GET', '/health');
  }

  // Authentication methods (to be implemented based on auth strategy)
  async login(username: string, password: string): Promise<{ token: string; user: any }> {
    const response = await this.request<{ token: string; user: any }>('POST', '/auth/login', {
      username,
      password,
    });

    // Store token
    localStorage.setItem('authToken', response.token);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('POST', '/auth/logout');
    } finally {
      localStorage.removeItem('authToken');
    }
  }

  // Helper methods for common operations
  async getLatestSignals(limit = 10): Promise<TradingSignal[]> {
    const response = await this.getSignals(1, limit);
    return response.data;
  }

  async getLatestMarketData(symbol: string, limit = 100): Promise<MarketDataPoint[]> {
    return this.getMarketData({
      symbols: [symbol],
      start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // Last 24 hours
    });
  }

  async getRunningBacktests(): Promise<BacktestResult[]> {
    const response = await this.getBacktests();
    return response.data.filter(bt => ['pending', 'running'].includes(bt.status));
  }
}

// Default API client instance
let defaultClient: ApiClient | null = null;

/**
 * Get or create the default API client
 */
export function getApiClient(): ApiClient {
  if (!defaultClient) {
    defaultClient = new ApiClient();
  }
  return defaultClient;
}

/**
 * Create a new API client with custom configuration
 */
export function createApiClient(baseURL?: string): ApiClient {
  return new ApiClient(baseURL);
}

// Export the client class and default instance
export { ApiClient };
export default getApiClient();