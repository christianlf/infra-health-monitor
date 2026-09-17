"""
Prometheus Metrics Exporter
Exposes infrastructure health metrics in Prometheus format
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry
import time


class PrometheusExporter:
    """Export metrics for Prometheus scraping"""
    
    def __init__(self):
        # Create custom registry to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Define metrics
        self.check_total = Counter(
            'infra_health_checks_total',
            'Total number of health checks performed',
            ['target', 'type', 'status'],
            registry=self.registry
        )
        
        self.check_latency = Histogram(
            'infra_health_check_latency_ms',
            'Latency of health checks in milliseconds',
            ['target', 'type'],
            buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000],
            registry=self.registry
        )
        
        self.target_up = Gauge(
            'infra_health_target_up',
            'Target availability (1=up, 0=down)',
            ['target', 'type'],
            registry=self.registry
        )
        
        self.consecutive_failures = Gauge(
            'infra_health_consecutive_failures',
            'Number of consecutive failures for a target',
            ['target'],
            registry=self.registry
        )
        
        self.uptime_percent = Gauge(
            'infra_health_uptime_percent',
            'Uptime percentage for each target',
            ['target'],
            registry=self.registry
        )
    
    def record_check(self, target, check_type, status, latency_ms=0):
        """Record a health check result"""
        # Increment counter
        self.check_total.labels(
            target=target,
            type=check_type,
            status=status
        ).inc()
        
        # Record latency for successful checks
        if status == 'success' and latency_ms > 0:
            self.check_latency.labels(
                target=target,
                type=check_type
            ).observe(latency_ms)
        
        # Update target availability
        self.target_up.labels(
            target=target,
            type=check_type
        ).set(1 if status == 'success' else 0)
    
    def update_consecutive_failures(self, target, count):
        """Update consecutive failures counter"""
        self.consecutive_failures.labels(target=target).set(count)
    
    def update_uptime(self, target, uptime_percent):
        """Update uptime percentage"""
        self.uptime_percent.labels(target=target).set(uptime_percent)
    
    def export_metrics(self):
        """Generate Prometheus metrics output"""
        return generate_latest(self.registry)
