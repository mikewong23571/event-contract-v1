"use client";

import { useEffect, useMemo, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import { Button, Card } from '@/components/ui';

type Alert = {
  id: string;
  timestamp: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  symbol?: string;
  metadata?: any;
};

export default function AlertsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws/alerts');
      
      ws.onopen = () => {
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const alertData = JSON.parse(event.data);
          if (alertData.type === 'alert') {
            const newAlert: Alert = {
              id: `alert-${Date.now()}-${Math.random()}`,
              timestamp: alertData.timestamp || new Date().toISOString(),
              alert_type: alertData.data.alert_type,
              severity: alertData.data.severity,
              message: alertData.data.message,
              symbol: alertData.data.symbol,
              metadata: alertData.data.metadata,
            };
            setAlerts(prev => [newAlert, ...prev].slice(0, 50)); // Keep last 50 alerts
          }
        } catch (e) {
          console.error('Failed to parse alert message:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        setError('WebSocket connection failed');
        setConnected(false);
      };

    } catch (e) {
      setError('Failed to connect to alerts WebSocket');
    }
  };

  useEffect(() => {
    connectWebSocket();
  }, []);

  const getSeverityColor = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'error': return 'bg-red-50 text-red-700 border-red-200';
      case 'warning': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'info': return 'bg-blue-50 text-blue-700 border-blue-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType) {
      case 'risk_limit_reached': return '⚠️';
      case 'signal_generation_failed': return '❌';
      case 'market_data_stale': return '📊';
      case 'high_probability_signal': return '🚀';
      case 'system_maintenance': return '🔧';
      default: return '📢';
    }
  };

  const clearAlerts = () => {
    setAlerts([]);
  };

  const header = useMemo(() => (
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Alerts</h2>
        <p className="text-sm text-gray-500">Real-time trading alerts and notifications</p>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <Button variant="secondary" onClick={connectWebSocket} disabled={connected}>
          Reconnect
        </Button>
        <Button variant="secondary" onClick={clearAlerts}>
          Clear Alerts
        </Button>
      </div>
    </div>
  ), [connected]);

  return (
    <Dashboard currentPage="Alerts">
      <div className="space-y-6">
        {header}
        {error && (
          <Card variant="outlined" className="border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </Card>
        )}
        
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-2">📢</div>
              <p>No alerts yet. Alerts will appear here in real-time.</p>
              {!connected && (
                <p className="text-sm mt-2">
                  Connecting to alert stream...
                </p>
              )}
            </div>
          ) : (
            alerts.map((alert) => (
              <Card
                key={alert.id}
                className={`${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start gap-3">
                  <div className="text-xl">
                    {getAlertTypeIcon(alert.alert_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm uppercase tracking-wide">
                        {alert.alert_type.replace(/_/g, ' ')}
                      </span>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      {alert.symbol && (
                        <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
                          {alert.symbol}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium mb-1">{alert.message}</p>
                    <p className="text-xs text-gray-600">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                    {alert.metadata && Object.keys(alert.metadata).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-gray-600 cursor-pointer">
                          View Details
                        </summary>
                        <pre className="text-xs bg-white bg-opacity-50 p-2 rounded mt-1 overflow-auto">
                          {JSON.stringify(alert.metadata, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </div>
    </Dashboard>
  );
}