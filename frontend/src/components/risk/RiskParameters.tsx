/* Using the automatic JSX runtime; no explicit React import required. */

import { useState } from 'react';

/**
 * RiskParameters
 * Component for displaying and editing risk management parameters.
 * Allows users to configure position sizing, stop losses, and other risk controls.
 *
 * Features:
 * - Form-based parameter editing
 * - Real-time validation
 * - Save/reset functionality
 * - Visual feedback for changes
 */

export interface RiskParametersData {
  id: string;
  max_position_size: number; // Maximum position size as percentage (0.0-1.0)
  stop_loss_percentage: number; // Stop loss as percentage (0.0-1.0)
  take_profit_percentage: number; // Take profit as percentage (0.0-1.0)
  max_daily_loss: number; // Maximum daily loss as percentage (0.0-1.0)
  max_concurrent_trades: number; // Maximum number of concurrent trades
  min_confidence_level: 'LOW' | 'MEDIUM' | 'HIGH'; // Minimum confidence level for trades
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface RiskParametersProps {
  parameters: RiskParametersData;
  onSave: (parameters: Partial<RiskParametersData>) => void;
  className?: string;
  isLoading?: boolean;
}

const confidenceLevels = ['LOW', 'MEDIUM', 'HIGH'] as const;

function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function parsePercentage(value: string): number {
  const num = parseFloat(value.replace('%', ''));
  return Number.isNaN(num) ? 0 : num / 100;
}

export function RiskParameters({ 
  parameters, 
  onSave, 
  className, 
  isLoading = false 
}: RiskParametersProps) {
  const [formData, setFormData] = useState(parameters);
  const [hasChanges, setHasChanges] = useState(false);

  const handleInputChange = (field: keyof RiskParametersData, value: any) => {
    const updatedData = { ...formData, [field]: value };
    setFormData(updatedData);
    setHasChanges(true);
  };

  const handleSave = () => {
    const changes: Partial<RiskParametersData> = {};
    
    (Object.keys(formData) as Array<keyof RiskParametersData>).forEach(key => {
      if (formData[key] !== parameters[key]) {
        changes[key] = formData[key] as any;
      }
    });

    if (Object.keys(changes).length > 0) {
      onSave(changes);
      setHasChanges(false);
    }
  };

  const handleReset = () => {
    setFormData(parameters);
    setHasChanges(false);
  };

  return (
    <div 
      className={['rounded-lg border border-border bg-card p-6', className]
        .filter(Boolean)
        .join(' ')}
    >
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-foreground">Risk Parameters</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure risk management settings for your trading strategy.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div>
          <label htmlFor="max-position-size" className="block text-sm font-medium text-foreground">
            Max Position Size
          </label>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="number"
              id="max-position-size"
              min="0"
              max="100"
              step="0.1"
              value={(formData.max_position_size * 100).toFixed(1)}
              onChange={(e) => handleInputChange('max_position_size', parseFloat(e.target.value) / 100)}
              className="block w-full rounded-md border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:ring-primary"
              disabled={isLoading}
            />
            <span className="inline-flex items-center rounded-r-md border border-l-0 border-input bg-muted px-3 text-sm text-muted-foreground">
              %
            </span>
          </div>
        </div>

        <div>
          <label htmlFor="stop-loss" className="block text-sm font-medium text-foreground">
            Stop Loss
          </label>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="number"
              id="stop-loss"
              min="0"
              max="100"
              step="0.1"
              value={(formData.stop_loss_percentage * 100).toFixed(1)}
              onChange={(e) => handleInputChange('stop_loss_percentage', parseFloat(e.target.value) / 100)}
              className="block w-full rounded-md border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:ring-primary"
              disabled={isLoading}
            />
            <span className="inline-flex items-center rounded-r-md border border-l-0 border-input bg-muted px-3 text-sm text-muted-foreground">
              %
            </span>
          </div>
        </div>

        <div>
          <label htmlFor="take-profit" className="block text-sm font-medium text-foreground">
            Take Profit
          </label>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="number"
              id="take-profit"
              min="0"
              max="1000"
              step="0.1"
              value={(formData.take_profit_percentage * 100).toFixed(1)}
              onChange={(e) => handleInputChange('take_profit_percentage', parseFloat(e.target.value) / 100)}
              className="block w-full rounded-md border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
              disabled={isLoading}
            />
            <span className="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-gray-50 px-3 text-sm text-gray-500">
              %
            </span>
          </div>
        </div>

        <div>
          <label htmlFor="max-daily-loss" className="block text-sm font-medium text-foreground">
            Max Daily Loss
          </label>
          <div className="mt-1 flex rounded-md shadow-sm">
            <input
              type="number"
              id="max-daily-loss"
              min="0"
              max="100"
              step="0.1"
              value={(formData.max_daily_loss * 100).toFixed(1)}
              onChange={(e) => handleInputChange('max_daily_loss', parseFloat(e.target.value) / 100)}
              className="block w-full rounded-md border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
              disabled={isLoading}
            />
            <span className="inline-flex items-center rounded-r-md border border-l-0 border-gray-300 bg-gray-50 px-3 text-sm text-gray-500">
              %
            </span>
          </div>
        </div>

        <div>
          <label htmlFor="max-concurrent-trades" className="block text-sm font-medium text-foreground">
            Max Concurrent Trades
          </label>
          <input
            type="number"
            id="max-concurrent-trades"
            min="1"
            max="100"
            step="1"
            value={formData.max_concurrent_trades}
            onChange={(e) => handleInputChange('max_concurrent_trades', parseInt(e.target.value, 10))}
            className="mt-1 block w-full rounded-md border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:ring-primary"
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="min-confidence" className="block text-sm font-medium text-foreground">
            Min Confidence Level
          </label>
          <select
            id="min-confidence"
            value={formData.min_confidence_level}
            onChange={(e) => handleInputChange('min_confidence_level', e.target.value as 'LOW' | 'MEDIUM' | 'HIGH')}
            className="mt-1 block w-full rounded-md border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:ring-primary"
            disabled={isLoading}
          >
            {confidenceLevels.map(level => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Last updated: {new Date(parameters.updated_at).toLocaleString()}
        </div>
        
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={handleReset}
            disabled={!hasChanges || isLoading}
            className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Reset
          </button>
          
          <button
            type="button"
            onClick={handleSave}
            disabled={!hasChanges || isLoading}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default RiskParameters;