"""Performance Monitoring and Logging System.

This module provides comprehensive performance monitoring, detailed logging,
and real-time metrics collection for event contract backtesting operations,
including execution tracking, resource usage monitoring, and alert systems.
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import threading
from contextlib import asynccontextmanager

import structlog
from pydantic import BaseModel, Field, validator

from ..models.backtest_result import BacktestResult
from ..strategies.event_contract_strategy import EventContractSignal
from ..simulators.event_contract_simulator import EventContract, ContractSettlement


logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of performance metrics."""
    COUNTER = "counter"          # Incrementing counter
    GAUGE = "gauge"              # Current value
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Execution time measurement
    RATE = "rate"                # Rate of change


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.metric_type.value,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels,
            'description': self.description
        }


@dataclass
class SystemResourceMetrics:
    """System resource usage metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_available_mb': self.memory_available_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'process_count': self.process_count
        }


@dataclass
class BacktestExecutionMetrics:
    """Backtesting execution metrics."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Task metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    # Signal metrics
    signals_generated: int = 0
    signals_executed: int = 0
    successful_contracts: int = 0
    failed_contracts: int = 0
    
    # Performance metrics
    total_profit_loss: Decimal = Decimal('0.0')
    best_strategy_pnl: Decimal = Decimal('0.0')
    worst_strategy_pnl: Decimal = Decimal('0.0')
    average_execution_time_ms: float = 0.0
    
    # Resource metrics
    peak_memory_usage_mb: float = 0.0
    average_cpu_usage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            'task_metrics': {
                'total_tasks': self.total_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'success_rate': self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0.0
            },
            'signal_metrics': {
                'signals_generated': self.signals_generated,
                'signals_executed': self.signals_executed,
                'successful_contracts': self.successful_contracts,
                'failed_contracts': self.failed_contracts,
                'execution_rate': self.signals_executed / self.signals_generated if self.signals_generated > 0 else 0.0,
                'win_rate': self.successful_contracts / (self.successful_contracts + self.failed_contracts) if (self.successful_contracts + self.failed_contracts) > 0 else 0.0
            },
            'performance_metrics': {
                'total_profit_loss': str(self.total_profit_loss),
                'best_strategy_pnl': str(self.best_strategy_pnl),
                'worst_strategy_pnl': str(self.worst_strategy_pnl),
                'average_execution_time_ms': self.average_execution_time_ms
            },
            'resource_metrics': {
                'peak_memory_usage_mb': self.peak_memory_usage_mb,
                'average_cpu_usage': self.average_cpu_usage
            }
        }


class Alert(BaseModel):
    """System alert."""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    labels: Dict[str, str] = Field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MonitoringConfig(BaseModel):
    """Configuration for performance monitoring."""
    
    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = True
    log_file_path: Path = Field(default=Path("logs/backtest.log"))
    log_rotation_size_mb: int = 100
    log_retention_days: int = 30
    
    # Metrics collection
    enable_metrics: bool = True
    metrics_collection_interval_seconds: int = 5
    metrics_retention_hours: int = 24
    
    # Resource monitoring
    enable_resource_monitoring: bool = True
    resource_monitoring_interval_seconds: int = 1
    
    # Alerting
    enable_alerting: bool = True
    cpu_usage_threshold: float = 80.0  # Percentage
    memory_usage_threshold: float = 85.0  # Percentage
    execution_time_threshold_ms: float = 5000.0  # Milliseconds
    
    # Performance tracking
    track_individual_signals: bool = True
    track_contract_settlements: bool = True
    track_strategy_performance: bool = True
    
    # Export configuration
    export_metrics: bool = False
    export_format: str = "prometheus"  # prometheus, json, csv
    export_interval_seconds: int = 60
    
    @validator('log_file_path')
    def create_log_directory(cls, v):
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        
        # Metrics storage
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._resource_metrics: deque = deque(maxlen=1000)
        self._execution_metrics: Dict[str, BacktestExecutionMetrics] = {}
        
        # Alerts
        self._alerts: List[Alert] = []
        self._alert_handlers: List[Callable[[Alert], None]] = []
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._resource_monitoring_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._signal_timings: Dict[str, float] = {}
        self._contract_settlements: List[ContractSettlement] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(
            "PerformanceMonitor initialized",
            log_level=config.log_level.value,
            metrics_enabled=config.enable_metrics,
            alerting_enabled=config.enable_alerting
        )
    
    async def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self._monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self._monitoring_active = True
        
        # Start metrics collection
        if self.config.enable_metrics:
            self._monitoring_task = asyncio.create_task(self._metrics_collection_loop())
        
        # Start resource monitoring
        if self.config.enable_resource_monitoring:
            self._resource_monitoring_task = asyncio.create_task(self._resource_monitoring_loop())
        
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        # Cancel monitoring tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._resource_monitoring_task:
            self._resource_monitoring_task.cancel()
            try:
                await self._resource_monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _metrics_collection_loop(self) -> None:
        """Main metrics collection loop."""
        while self._monitoring_active:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.config.metrics_collection_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in metrics collection", error=str(e))
                await asyncio.sleep(1)
    
    async def _resource_monitoring_loop(self) -> None:
        """Resource monitoring loop."""
        while self._monitoring_active:
            try:
                await self._collect_resource_metrics()
                await asyncio.sleep(self.config.resource_monitoring_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in resource monitoring", error=str(e))
                await asyncio.sleep(1)
    
    async def _collect_metrics(self) -> None:
        """Collect performance metrics."""
        timestamp = datetime.now()
        
        # Collect execution metrics
        for session_id, exec_metrics in self._execution_metrics.items():
            if exec_metrics.end_time is None:  # Active session
                # Update current metrics
                self.record_metric(
                    "active_session_duration",
                    MetricType.GAUGE,
                    (timestamp - exec_metrics.start_time).total_seconds(),
                    labels={"session_id": session_id}
                )
        
        # Collect alert metrics
        active_alerts = len([a for a in self._alerts if not a.resolved])
        self.record_metric("active_alerts", MetricType.GAUGE, active_alerts)
        
        # Collect cache metrics (would integrate with actual cache systems)
        self.record_metric("metrics_buffer_size", MetricType.GAUGE, sum(len(q) for q in self._metrics.values()))
    
    async def _collect_resource_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process count
            process_count = len(psutil.pids())
            
            # Create resource metrics
            resource_metrics = SystemResourceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                process_count=process_count
            )
            
            with self._lock:
                self._resource_metrics.append(resource_metrics)
            
            # Check for alerts
            if self.config.enable_alerting:
                await self._check_resource_alerts(resource_metrics)
            
            # Record as metrics
            self.record_metric("cpu_usage_percent", MetricType.GAUGE, cpu_percent)
            self.record_metric("memory_usage_percent", MetricType.GAUGE, memory_percent)
            self.record_metric("memory_used_mb", MetricType.GAUGE, memory_used_mb)
            self.record_metric("disk_usage_percent", MetricType.GAUGE, disk_usage_percent)
            
        except Exception as e:
            logger.error("Failed to collect resource metrics", error=str(e))
    
    async def _check_resource_alerts(self, metrics: SystemResourceMetrics) -> None:
        """Check for resource-based alerts."""
        # CPU usage alert
        if metrics.cpu_percent > self.config.cpu_usage_threshold:
            await self._create_alert(
                AlertLevel.WARNING,
                "High CPU Usage",
                f"CPU usage is {metrics.cpu_percent:.1f}%, exceeding threshold of {self.config.cpu_usage_threshold}%",
                "resource_monitor",
                {"metric": "cpu_usage", "value": str(metrics.cpu_percent)}
            )
        
        # Memory usage alert
        if metrics.memory_percent > self.config.memory_usage_threshold:
            await self._create_alert(
                AlertLevel.WARNING,
                "High Memory Usage",
                f"Memory usage is {metrics.memory_percent:.1f}%, exceeding threshold of {self.config.memory_usage_threshold}%",
                "resource_monitor",
                {"metric": "memory_usage", "value": str(metrics.memory_percent)}
            )
    
    def record_metric(self, name: str, metric_type: MetricType, value: float, 
                     labels: Optional[Dict[str, str]] = None, description: str = "") -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            description=description
        )
        
        with self._lock:
            self._metrics[name].append(metric)
        
        # Log metric if debug level
        if self.config.log_level == LogLevel.DEBUG:
            logger.debug(
                "Metric recorded",
                metric_name=name,
                metric_type=metric_type.value,
                value=value,
                labels=labels
            )
    
    @asynccontextmanager
    async def time_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        
        try:
            yield
        finally:
            execution_time_ms = (time.time() - start_time) * 1000
            self.record_metric(
                f"{operation_name}_execution_time_ms",
                MetricType.TIMER,
                execution_time_ms,
                labels=labels
            )
            
            # Check for execution time alerts
            if (self.config.enable_alerting and 
                execution_time_ms > self.config.execution_time_threshold_ms):
                await self._create_alert(
                    AlertLevel.WARNING,
                    "Slow Operation",
                    f"Operation '{operation_name}' took {execution_time_ms:.1f}ms, exceeding threshold of {self.config.execution_time_threshold_ms}ms",
                    "performance_monitor",
                    {"operation": operation_name, "execution_time_ms": str(execution_time_ms)}
                )
    
    def start_backtest_session(self, session_id: str) -> None:
        """Start tracking a backtesting session."""
        exec_metrics = BacktestExecutionMetrics(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        with self._lock:
            self._execution_metrics[session_id] = exec_metrics
        
        logger.info("Backtest session started", session_id=session_id)
        self.record_metric("backtest_sessions_started", MetricType.COUNTER, 1)
    
    def end_backtest_session(self, session_id: str) -> Optional[BacktestExecutionMetrics]:
        """End tracking a backtesting session."""
        with self._lock:
            if session_id in self._execution_metrics:
                exec_metrics = self._execution_metrics[session_id]
                exec_metrics.end_time = datetime.now()
                
                logger.info(
                    "Backtest session completed",
                    session_id=session_id,
                    duration_seconds=(exec_metrics.end_time - exec_metrics.start_time).total_seconds(),
                    total_tasks=exec_metrics.total_tasks,
                    success_rate=exec_metrics.completed_tasks / exec_metrics.total_tasks if exec_metrics.total_tasks > 0 else 0.0
                )
                
                self.record_metric("backtest_sessions_completed", MetricType.COUNTER, 1)
                return exec_metrics
        
        return None
    
    def update_session_metrics(self, session_id: str, **kwargs) -> None:
        """Update metrics for a backtesting session."""
        with self._lock:
            if session_id in self._execution_metrics:
                exec_metrics = self._execution_metrics[session_id]
                
                for key, value in kwargs.items():
                    if hasattr(exec_metrics, key):
                        setattr(exec_metrics, key, value)
    
    def track_signal_generation(self, session_id: str, signal: EventContractSignal) -> None:
        """Track signal generation."""
        if self.config.track_individual_signals:
            self.record_metric(
                "signals_generated",
                MetricType.COUNTER,
                1,
                labels={
                    "session_id": session_id,
                    "symbol": signal.symbol,
                    "direction": signal.direction.value,
                    "strength": signal.strength.value
                }
            )
            
            # Track signal timing
            signal_key = f"{session_id}_{signal.id}"
            self._signal_timings[signal_key] = time.time()
        
        # Update session metrics
        self.update_session_metrics(session_id, signals_generated=
            self._execution_metrics.get(session_id, BacktestExecutionMetrics("", datetime.now())).signals_generated + 1
        )
    
    def track_contract_settlement(self, session_id: str, settlement: ContractSettlement) -> None:
        """Track contract settlement."""
        if self.config.track_contract_settlements:
            self._contract_settlements.append(settlement)
            
            self.record_metric(
                "contracts_settled",
                MetricType.COUNTER,
                1,
                labels={
                    "session_id": session_id,
                    "successful": str(settlement.was_successful)
                }
            )
            
            self.record_metric(
                "contract_profit_loss",
                MetricType.HISTOGRAM,
                float(settlement.profit_loss),
                labels={"session_id": session_id}
            )
        
        # Update session metrics
        exec_metrics = self._execution_metrics.get(session_id)
        if exec_metrics:
            if settlement.was_successful:
                exec_metrics.successful_contracts += 1
            else:
                exec_metrics.failed_contracts += 1
            
            exec_metrics.total_profit_loss += settlement.profit_loss
    
    async def _create_alert(self, level: AlertLevel, title: str, message: str, 
                          source: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Create and process an alert."""
        alert = Alert(
            id=f"{source}_{int(time.time())}_{len(self._alerts)}",
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            labels=labels or {}
        )
        
        self._alerts.append(alert)
        
        # Log alert
        log_level = {
            AlertLevel.INFO: "info",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "error",
            AlertLevel.CRITICAL: "critical"
        }[level]
        
        getattr(logger, log_level)(
            f"Alert: {title}",
            message=message,
            source=source,
            labels=labels
        )
        
        # Call alert handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Alert handler failed", handler=str(handler), error=str(e))
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler."""
        self._alert_handlers.append(handler)
    
    def get_metrics(self, metric_name: Optional[str] = None, 
                   since: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get collected metrics."""
        with self._lock:
            if metric_name:
                metrics = list(self._metrics.get(metric_name, []))
            else:
                metrics = []
                for metric_queue in self._metrics.values():
                    metrics.extend(metric_queue)
        
        # Filter by time if specified
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return sorted(metrics, key=lambda m: m.timestamp)
    
    def get_resource_metrics(self, since: Optional[datetime] = None) -> List[SystemResourceMetrics]:
        """Get resource metrics."""
        with self._lock:
            metrics = list(self._resource_metrics)
        
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        return sorted(metrics, key=lambda m: m.timestamp)
    
    def get_execution_metrics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get execution metrics."""
        with self._lock:
            if session_id:
                if session_id in self._execution_metrics:
                    return {session_id: self._execution_metrics[session_id].to_dict()}
                else:
                    return {}
            else:
                return {
                    sid: metrics.to_dict() 
                    for sid, metrics in self._execution_metrics.items()
                }
    
    def get_alerts(self, resolved: Optional[bool] = None, 
                  level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get alerts with optional filtering."""
        alerts = self._alerts.copy()
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info("Alert resolved", alert_id=alert_id)
                return True
        return False
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            # Calculate summary statistics
            total_sessions = len(self._execution_metrics)
            active_sessions = len([m for m in self._execution_metrics.values() if m.end_time is None])
            completed_sessions = total_sessions - active_sessions
            
            # Resource usage summary
            recent_resources = list(self._resource_metrics)[-10:] if self._resource_metrics else []
            avg_cpu = sum(r.cpu_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0
            avg_memory = sum(r.memory_percent for r in recent_resources) / len(recent_resources) if recent_resources else 0.0
            
            # Alert summary
            active_alerts = len([a for a in self._alerts if not a.resolved])
            total_alerts = len(self._alerts)
            
            return {
                'monitoring_status': {
                    'active': self._monitoring_active,
                    'metrics_enabled': self.config.enable_metrics,
                    'resource_monitoring_enabled': self.config.enable_resource_monitoring,
                    'alerting_enabled': self.config.enable_alerting
                },
                'session_summary': {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'completed_sessions': completed_sessions
                },
                'resource_summary': {
                    'average_cpu_percent': avg_cpu,
                    'average_memory_percent': avg_memory,
                    'recent_samples': len(recent_resources)
                },
                'alert_summary': {
                    'active_alerts': active_alerts,
                    'total_alerts': total_alerts,
                    'resolution_rate': (total_alerts - active_alerts) / total_alerts if total_alerts > 0 else 0.0
                },
                'metrics_summary': {
                    'total_metrics_collected': sum(len(q) for q in self._metrics.values()),
                    'unique_metric_names': len(self._metrics),
                    'contract_settlements_tracked': len(self._contract_settlements)
                }
            }
    
    async def export_metrics(self, format_type: str = "json", 
                           output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Export metrics in specified format."""
        if format_type == "json":
            return await self._export_json_metrics(output_path)
        elif format_type == "prometheus":
            return await self._export_prometheus_metrics(output_path)
        elif format_type == "csv":
            return await self._export_csv_metrics(output_path)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _export_json_metrics(self, output_path: Optional[Path]) -> Dict[str, Any]:
        """Export metrics in JSON format."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'performance_summary': self.get_performance_summary(),
            'metrics': [m.to_dict() for m in self.get_metrics()],
            'resource_metrics': [r.to_dict() for r in self.get_resource_metrics()],
            'execution_metrics': self.get_execution_metrics(),
            'alerts': [a.dict() for a in self.get_alerts()]
        }
        
        if output_path:
            import json
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        return export_data
    
    async def _export_prometheus_metrics(self, output_path: Optional[Path]) -> Dict[str, Any]:
        """Export metrics in Prometheus format."""
        # Simplified Prometheus export
        lines = []
        
        for metric in self.get_metrics():
            labels_str = ",".join([f'{k}="{v}"' for k, v in metric.labels.items()])
            if labels_str:
                line = f'{metric.name}{{{labels_str}}} {metric.value} {int(metric.timestamp.timestamp() * 1000)}'
            else:
                line = f'{metric.name} {metric.value} {int(metric.timestamp.timestamp() * 1000)}'
            lines.append(line)
        
        prometheus_data = '\n'.join(lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(prometheus_data)
        
        return {'format': 'prometheus', 'data': prometheus_data, 'lines': len(lines)}
    
    async def _export_csv_metrics(self, output_path: Optional[Path]) -> Dict[str, Any]:
        """Export metrics in CSV format."""
        import pandas as pd
        
        # Convert metrics to DataFrame
        metrics_data = []
        for metric in self.get_metrics():
            row = {
                'name': metric.name,
                'type': metric.metric_type.value,
                'value': metric.value,
                'timestamp': metric.timestamp.isoformat(),
                'description': metric.description
            }
            # Add labels as separate columns
            for k, v in metric.labels.items():
                row[f'label_{k}'] = v
            metrics_data.append(row)
        
        if metrics_data:
            df = pd.DataFrame(metrics_data)
            
            if output_path:
                df.to_csv(output_path, index=False)
            
            return {'format': 'csv', 'rows': len(df), 'columns': list(df.columns)}
        
        return {'format': 'csv', 'rows': 0, 'columns': []}
    
    def cleanup(self) -> None:
        """Clean up monitoring resources."""
        # Clear old metrics based on retention policy
        cutoff_time = datetime.now() - timedelta(hours=self.config.metrics_retention_hours)
        
        with self._lock:
            # Clean metrics
            for metric_name in list(self._metrics.keys()):
                metric_queue = self._metrics[metric_name]
                # Remove old metrics
                while metric_queue and metric_queue[0].timestamp < cutoff_time:
                    metric_queue.popleft()
                
                # Remove empty queues
                if not metric_queue:
                    del self._metrics[metric_name]
            
            # Clean resource metrics
            while self._resource_metrics and self._resource_metrics[0].timestamp < cutoff_time:
                self._resource_metrics.popleft()
            
            # Clean old contract settlements
            self._contract_settlements = [
                s for s in self._contract_settlements 
                if s.settlement_timestamp >= cutoff_time
            ]
        
        logger.info("Monitoring cleanup completed", cutoff_time=cutoff_time.isoformat())