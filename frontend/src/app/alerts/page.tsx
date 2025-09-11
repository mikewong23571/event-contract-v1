"use client";

import { useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import { 
  Button, 
  PageHeader, 
  ControlBar, 
  StatusIndicator, 
  ErrorBanner 
} from '@/components/ui';

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



  return (
    <Dashboard currentPage="Alerts">
      <div className="space-y-6">
        <PageHeader 
          title="实时告警" 
          subtitle="实时交易告警和通知"
        />
        
        <ControlBar>
          <div className="flex items-center justify-between w-full">
            <StatusIndicator 
               status={connected ? 'success' : 'error'}
               text={connected ? '已连接' : '未连接'}
               size="sm"
             />
            <div className="flex gap-2">
              <Button 
                variant="secondary" 
                onClick={connectWebSocket} 
                disabled={connected}
              >
                重新连接
              </Button>
              <Button 
                variant="secondary" 
                onClick={clearAlerts}
              >
                清空告警
              </Button>
            </div>
          </div>
        </ControlBar>
        
        {error && (
          <ErrorBanner 
            message={error} 
            onClose={() => setError(null)}
          />
        )}
        
        <div className="bg-white rounded-lg border p-6">
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">📢</div>
                <p>暂无告警信息，告警将在此处实时显示。</p>
                {!connected && (
                  <p className="text-sm mt-2">
                    正在连接告警流...
                  </p>
                )}
              </div>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
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
                            查看详情
                          </summary>
                          <pre className="text-xs bg-white bg-opacity-50 p-2 rounded mt-1 overflow-auto">
                            {JSON.stringify(alert.metadata, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Dashboard>
  );
}