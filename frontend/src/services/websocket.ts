import { useState, useEffect } from 'react';

/**
 * WebSocket Client Service
 * Real-time communication service for market data, signals, and alerts.
 * Provides connection management, message handling, and automatic reconnection.
 *
 * Features:
 * - Automatic connection management
 * - Message type routing
 * - Reconnection with exponential backoff
 * - Connection state management
 * - Type-safe message handling
 */

export type WebSocketState = 'connecting' | 'connected' | 'disconnecting' | 'disconnected' | 'error';

export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
}

export interface TradingSignal {
  id: string;
  timestamp: string;
  symbol: string;
  direction: 'UP' | 'DOWN';
  predicted_probability: number;
  confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
  expiry_time: string;
}

export interface MarketDataPoint {
  timestamp: string;
  symbol: string;
  price: number;
  volume?: number;
  bid?: number;
  ask?: number;
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  data?: any;
}

export type MessageHandler<T = any> = (data: T) => void;
export type StateChangeHandler = (state: WebSocketState) => void;
export type ErrorHandler = (error: Event | Error) => void;

interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  reconnectBackoffMultiplier?: number;
  heartbeatInterval?: number;
}

interface Subscription {
  channel: string;
  handler: MessageHandler;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: WebSocketState = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private heartbeatIntervalId: NodeJS.Timeout | null = null;
  private subscriptions = new Map<string, Set<MessageHandler>>();
  private stateChangeHandlers = new Set<StateChangeHandler>();
  private errorHandlers = new Set<ErrorHandler>();

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 1000,
      maxReconnectAttempts: 10,
      reconnectBackoffMultiplier: 1.5,
      heartbeatInterval: 30000,
      ...config,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.state === 'connected' || this.state === 'connecting') {
        resolve();
        return;
      }

      this.setState('connecting');

      try {
        this.ws = new WebSocket(this.config.url);

        this.ws.onopen = () => {
          this.setState('connected');
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          this.setState('disconnected');
          this.stopHeartbeat();
          this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
          this.setState('error');
          this.notifyErrorHandlers(error);
          reject(error);
        };
      } catch (error) {
        this.setState('error');
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.setState('disconnecting');
    this.clearReconnectTimeout();
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.setState('disconnected');
  }

  /**
   * Subscribe to a specific message type
   */
  subscribe<T = any>(type: string, handler: MessageHandler<T>): () => void {
    if (!this.subscriptions.has(type)) {
      this.subscriptions.set(type, new Set());
    }
    
    this.subscriptions.get(type)!.add(handler);

    // Send subscription message to server
    this.send({
      type: 'subscribe',
      data: { channel: type },
      timestamp: new Date().toISOString(),
    });

    // Return unsubscribe function
    return () => {
      const handlers = this.subscriptions.get(type);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.subscriptions.delete(type);
          // Send unsubscription message to server
          this.send({
            type: 'unsubscribe',
            data: { channel: type },
            timestamp: new Date().toISOString(),
          });
        }
      }
    };
  }

  /**
   * Subscribe to trading signals
   */
  subscribeToSignals(handler: MessageHandler<TradingSignal>): () => void {
    return this.subscribe('signals', handler);
  }

  /**
   * Subscribe to market data
   */
  subscribeToMarketData(handler: MessageHandler<MarketDataPoint>): () => void {
    return this.subscribe('market-data', handler);
  }

  /**
   * Subscribe to alerts
   */
  subscribeToAlerts(handler: MessageHandler<Alert>): () => void {
    return this.subscribe('alerts', handler);
  }

  /**
   * Send a message to the server
   */
  send(message: WebSocketMessage): void {
    if (this.state !== 'connected' || !this.ws) {
      console.warn('WebSocket not connected, message not sent:', message);
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      this.notifyErrorHandlers(error as Error);
    }
  }

  /**
   * Get current connection state
   */
  getState(): WebSocketState {
    return this.state;
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.state === 'connected';
  }

  /**
   * Add state change handler
   */
  onStateChange(handler: StateChangeHandler): () => void {
    this.stateChangeHandlers.add(handler);
    return () => {
      this.stateChangeHandlers.delete(handler);
    };
  }

  /**
   * Add error handler
   */
  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => {
      this.errorHandlers.delete(handler);
    };
  }

  private setState(newState: WebSocketState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.stateChangeHandlers.forEach(handler => {
        try {
          handler(newState);
        } catch (error) {
          console.error('State change handler error:', error);
        }
      });
    }
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.subscriptions.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data);
        } catch (error) {
          console.error(`Handler error for message type ${message.type}:`, error);
        }
      });
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.warn('Max reconnect attempts reached');
      return;
    }

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(this.config.reconnectBackoffMultiplier, this.reconnectAttempts),
      30000 // Cap at 30 seconds
    );

    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);
      this.connect().catch(error => {
        console.error('Reconnect failed:', error);
      });
    }, delay);
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
  }

  private startHeartbeat(): void {
    this.heartbeatIntervalId = setInterval(() => {
      this.send({
        type: 'ping',
        data: {},
        timestamp: new Date().toISOString(),
      });
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId);
      this.heartbeatIntervalId = null;
    }
  }

  private notifyErrorHandlers(error: Event | Error): void {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (handlerError) {
        console.error('Error handler error:', handlerError);
      }
    });
  }
}

// Default WebSocket client instance
let defaultClient: WebSocketClient | null = null;

/**
 * Get or create the default WebSocket client
 */
export function getWebSocketClient(): WebSocketClient {
  if (!defaultClient) {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    defaultClient = new WebSocketClient({ url: wsUrl });
  }
  return defaultClient;
}

/**
 * React hook for WebSocket connection state
 */
export function useWebSocketState(): WebSocketState {
  const client = getWebSocketClient();
  const [state, setState] = useState<WebSocketState>(client.getState());

  useEffect(() => {
    const unsubscribe = client.onStateChange(setState);
    return unsubscribe;
  }, [client]);

  return state;
}

/**
 * React hook for WebSocket subscriptions
 */
export function useWebSocketSubscription<T = any>(
  type: string,
  handler: MessageHandler<T>,
  autoConnect = true
): WebSocketState {
  const client = getWebSocketClient();
  const state = useWebSocketState();

  useEffect(() => {
    if (autoConnect && !client.isConnected()) {
      client.connect().catch(error => {
        console.error('Failed to connect WebSocket:', error);
      });
    }

    const unsubscribe = client.subscribe(type, handler);
    return unsubscribe;
  }, [client, type, handler, autoConnect]);

  return state;
}

// Re-export types for convenience
export type { WebSocketConfig, Subscription };