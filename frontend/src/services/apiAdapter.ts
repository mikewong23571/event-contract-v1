/**
 * API Adapter Service
 * Adapts backend API responses to frontend expected formats.
 * Handles the contract mismatches between frontend expectations and backend reality.
 */

import { ApiClient, ApiResponse, PaginatedResponse, TradingSignal, BacktestResult, RiskParameters, MarketDataPoint } from './api';

// Backend response types (as they actually come from the backend)
interface BackendSignalsResponse {
  signals: any[];
  total_count: number;
  has_more: boolean;
}

interface BackendBacktestsResponse {
  results: Array<{
    backtest_id: string;
    status: string;
    strategy_name: string;
  }>;
}

interface BackendBacktestCreateResponse {
  backtest_id: string;
  status: string;
  created_at: string;
}

interface BackendMarketDataResponse {
  symbol: string;
  interval: string;
  data: Array<{
    symbol: string;
    timestamp: string;
    open_price: string;
    high_price: string;
    low_price: string;
    close_price: string;
    volume: string;
    quote_volume?: string;
    trade_count?: number;
  }>;
}

interface BackendRiskParameters {
  max_bet_size: number;
  max_daily_bets: number;
  max_parallel_positions: number;
  min_probability_edge: number;
  frequency_limit_minutes: number;
  max_daily_loss: number;
}

/**
 * API Adapter that wraps the base ApiClient and adapts responses
 */
export class ApiAdapter {
  private client: ApiClient;

  constructor(baseURL?: string) {
    this.client = new ApiClient(baseURL);
  }

  /**
   * Wrap backend response in frontend-expected envelope
   */
  private wrapResponse<T>(data: T, success: boolean = true): ApiResponse<T> {
    return {
      data,
      success,
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Create paginated response from backend data
   */
  private createPaginatedResponse<T>(
    data: T[], 
    totalCount: number, 
    hasMore: boolean, 
    page: number = 1, 
    pageSize: number = 50
  ): PaginatedResponse<T> {
    const totalPages = Math.ceil(totalCount / pageSize);
    
    return {
      data,
      success: true,
      timestamp: new Date().toISOString(),
      pagination: {
        page,
        page_size: pageSize,
        total_items: totalCount,
        total_pages: totalPages,
        has_next: hasMore,
        has_previous: page > 1,
      },
    };
  }

  // Trading Signals API (adapted)
  async getSignals(page = 1, pageSize = 50): Promise<PaginatedResponse<TradingSignal>> {
    // Backend uses limit instead of pagination
    const limit = pageSize;
    const response = await this.client['client'].get<BackendSignalsResponse>('/signals', {
      params: { limit },
    });

    const backendData = response.data;
    
    return this.createPaginatedResponse(
      backendData.signals,
      backendData.total_count,
      backendData.has_more,
      page,
      pageSize
    );
  }

  async generateSignal(symbol: string, timeframe?: string, risk_level?: string): Promise<ApiResponse<TradingSignal>> {
    const response = await this.client['request']<TradingSignal>('POST', '/signals/generate', {
      symbol,
      timeframe,
      risk_level,
    });

    return this.wrapResponse(response);
  }

  // Market Data API (adapted)
  async getMarketData(symbols: string[], startTime?: string, endTime?: string, timeframe?: string): Promise<ApiResponse<MarketDataPoint[]>> {
    // Backend only supports single symbol per request
    const allData: MarketDataPoint[] = [];
    
    for (const symbol of symbols) {
      try {
        const response = await this.client['client'].get<BackendMarketDataResponse>(`/market-data/${symbol}`, {
          params: {
            interval: timeframe || '1m',
            limit: 100,
          },
        });

        // Transform backend format to frontend format
        const transformedData = response.data.data.map(item => ({
          timestamp: item.timestamp,
          symbol: item.symbol,
          price: parseFloat(item.close_price),
          volume: parseFloat(item.volume),
          high: parseFloat(item.high_price),
          low: parseFloat(item.low_price),
          open: parseFloat(item.open_price),
          close: parseFloat(item.close_price),
        }));

        allData.push(...transformedData);
      } catch (error) {
        console.warn(`Failed to fetch market data for ${symbol}:`, error);
      }
    }

    return this.wrapResponse(allData);
  }

  // Risk Parameters API (adapted)
  async getRiskParameters(): Promise<ApiResponse<RiskParameters>> {
    const response = await this.client['client'].get<BackendRiskParameters>('/risk-parameters');
    const backendData = response.data;

    // Transform backend field names to frontend expected names
    const frontendRiskParams: RiskParameters = {
      id: 'default',
      max_position_size: backendData.max_bet_size,
      stop_loss_percentage: 0.05, // Default value - not in backend
      take_profit_percentage: 0.10, // Default value - not in backend  
      max_daily_loss: backendData.max_daily_loss,
      max_concurrent_trades: backendData.max_parallel_positions,
      min_confidence_level: 'MEDIUM', // Default value - backend uses min_probability_edge
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return this.wrapResponse(frontendRiskParams);
  }

  async updateRiskParameters(params: Partial<RiskParameters>): Promise<ApiResponse<RiskParameters>> {
    // Transform frontend field names to backend expected names
    const backendParams: Partial<BackendRiskParameters> = {};
    
    if (params.max_position_size !== undefined) {
      backendParams.max_bet_size = params.max_position_size;
    }
    if (params.max_daily_loss !== undefined) {
      backendParams.max_daily_loss = params.max_daily_loss;
    }
    if (params.max_concurrent_trades !== undefined) {
      backendParams.max_parallel_positions = params.max_concurrent_trades;
    }

    const response = await this.client['client'].put<BackendRiskParameters>('/risk-parameters', backendParams);
    const backendData = response.data;

    // Transform back to frontend format
    const frontendRiskParams: RiskParameters = {
      id: 'default',
      max_position_size: backendData.max_bet_size,
      stop_loss_percentage: params.stop_loss_percentage || 0.05,
      take_profit_percentage: params.take_profit_percentage || 0.10,
      max_daily_loss: backendData.max_daily_loss,
      max_concurrent_trades: backendData.max_parallel_positions,
      min_confidence_level: params.min_confidence_level || 'MEDIUM',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return this.wrapResponse(frontendRiskParams);
  }

  // Backtests API (adapted)
  async getBacktests(page = 1, pageSize = 20): Promise<PaginatedResponse<BacktestResult>> {
    const response = await this.client['client'].get<BackendBacktestsResponse>('/backtests', {
      params: {
        limit: pageSize,
      },
    });

    const backendData = response.data;
    
    // Transform backend format to frontend format
    const transformedResults: BacktestResult[] = backendData.results.map(item => ({
      id: item.backtest_id,
      name: item.strategy_name,
      status: item.status.toLowerCase() as any,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));

    return this.createPaginatedResponse(
      transformedResults,
      transformedResults.length,
      false, // Backend doesn't indicate if there are more
      page,
      pageSize
    );
  }

  async createBacktest(request: any): Promise<ApiResponse<{ backtest_id: string; status: string }>> {
    const response = await this.client['client'].post<BackendBacktestCreateResponse>('/backtests', request);
    const backendData = response.data;

    return this.wrapResponse({
      backtest_id: backendData.backtest_id,
      status: backendData.status,
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    const response = await this.client['client'].get('/health');
    return this.wrapResponse(response.data);
  }

  // Get signals by ID (newly implemented endpoint)
  async getSignalById(signalId: string): Promise<ApiResponse<TradingSignal>> {
    const response = await this.client['client'].get<TradingSignal>(`/signals/${signalId}`);
    return this.wrapResponse(response.data);
  }

  // Get performance metrics (newly implemented endpoint)
  async getPerformanceMetrics(): Promise<ApiResponse<any>> {
    const response = await this.client['client'].get('/metrics/performance');
    return this.wrapResponse(response.data);
  }
}

// Default adapter instance  
let defaultAdapter: ApiAdapter | null = null;

/**
 * Get or create the default API adapter
 */
export function getApiAdapter(): ApiAdapter {
  if (!defaultAdapter) {
    defaultAdapter = new ApiAdapter();
  }
  return defaultAdapter;
}

/**
 * Create a new API adapter with custom configuration
 */
export function createApiAdapter(baseURL?: string): ApiAdapter {
  return new ApiAdapter(baseURL);
}

// Export the adapter class and default instance
export default getApiAdapter();