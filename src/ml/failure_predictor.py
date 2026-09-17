"""
Machine Learning Failure Predictor
Predicts potential infrastructure failures based on historical patterns
"""

import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


class FailurePredictor:
    """
    Predicts infrastructure failures using statistical analysis
    
    Uses moving averages and trend analysis to detect:
    - Increasing latency patterns
    - Increasing failure rates
    - Degradation trends
    """
    
    def __init__(self, database):
        self.database = database
        self.thresholds = {
            'latency_increase_percent': 50,  # 50% increase in latency
            'failure_rate_threshold': 0.15,  # 15% failure rate
            'trend_window_hours': 6,         # Look back 6 hours
            'prediction_confidence_min': 0.6  # 60% confidence minimum
        }
    
    def analyze_target(self, target_name):
        """
        Analyze a target for potential failures
        
        Returns:
            dict: {
                'risk_level': str ('low', 'medium', 'high'),
                'confidence': float (0-1),
                'indicators': list of warning signs,
                'prediction': str (human-readable)
            }
        """
        # Get recent checks (last 6 hours)
        hours = self.thresholds['trend_window_hours']
        checks = self.database.get_checks_by_target(target_name, limit=hours * 60)
        
        if len(checks) < 30:  # Need minimum data
            return {
                'risk_level': 'unknown',
                'confidence': 0.0,
                'indicators': [],
                'prediction': 'Insufficient data for prediction'
            }
        
        # Analyze different indicators
        latency_risk = self._analyze_latency_trend(checks)
        failure_risk = self._analyze_failure_rate(checks)
        pattern_risk = self._analyze_failure_pattern(checks)
        
        # Combine risks
        indicators = []
        risk_scores = []
        
        if latency_risk['risk'] > 0:
            indicators.append(latency_risk['message'])
            risk_scores.append(latency_risk['risk'])
        
        if failure_risk['risk'] > 0:
            indicators.append(failure_risk['message'])
            risk_scores.append(failure_risk['risk'])
        
        if pattern_risk['risk'] > 0:
            indicators.append(pattern_risk['message'])
            risk_scores.append(pattern_risk['risk'])
        
        # Calculate overall risk
        if not risk_scores:
            risk_level = 'low'
            confidence = 0.8
            prediction = f"✅ {target_name} is operating normally"
        else:
            avg_risk = sum(risk_scores) / len(risk_scores)
            confidence = min(len(indicators) * 0.3, 1.0)  # More indicators = higher confidence
            
            if avg_risk >= 0.7:
                risk_level = 'high'
                prediction = f"⚠️ {target_name} may fail within 1-2 hours"
            elif avg_risk >= 0.4:
                risk_level = 'medium'
                prediction = f"⚡ {target_name} shows signs of degradation"
            else:
                risk_level = 'low'
                prediction = f"✅ {target_name} is stable with minor fluctuations"
        
        return {
            'risk_level': risk_level,
            'confidence': confidence,
            'indicators': indicators,
            'prediction': prediction
        }
    
    def _analyze_latency_trend(self, checks):
        """Detect increasing latency trend"""
        # Split into two halves
        mid = len(checks) // 2
        recent_half = checks[:mid]
        older_half = checks[mid:]
        
        # Calculate average latency for successful checks
        recent_latencies = [c['latency_ms'] for c in recent_half 
                           if c['status'] == 'success' and c.get('latency_ms')]
        older_latencies = [c['latency_ms'] for c in older_half 
                          if c['status'] == 'success' and c.get('latency_ms')]
        
        if not recent_latencies or not older_latencies:
            return {'risk': 0, 'message': ''}
        
        avg_recent = np.mean(recent_latencies)
        avg_older = np.mean(older_latencies)
        
        # Check for significant increase
        if avg_older > 0:
            increase_percent = ((avg_recent - avg_older) / avg_older) * 100
            
            if increase_percent > self.thresholds['latency_increase_percent']:
                return {
                    'risk': min(increase_percent / 100, 1.0),
                    'message': f'Latency increased {increase_percent:.1f}% ({avg_older:.0f}ms → {avg_recent:.0f}ms)'
                }
        
        return {'risk': 0, 'message': ''}
    
    def _analyze_failure_rate(self, checks):
        """Check for elevated failure rate"""
        total = len(checks)
        failures = sum(1 for c in checks if c['status'] == 'failed')
        failure_rate = failures / total if total > 0 else 0
        
        if failure_rate > self.thresholds['failure_rate_threshold']:
            return {
                'risk': min(failure_rate * 2, 1.0),
                'message': f'Failure rate: {failure_rate*100:.1f}% ({failures}/{total} checks)'
            }
        
        return {'risk': 0, 'message': ''}
    
    def _analyze_failure_pattern(self, checks):
        """Detect patterns in failures (clustering)"""
        # Look for clustered failures (multiple failures close together)
        recent_10 = checks[:10]
        recent_failures = sum(1 for c in recent_10 if c['status'] == 'failed')
        
        if recent_failures >= 3:
            return {
                'risk': recent_failures / 10,
                'message': f'Recent instability: {recent_failures} failures in last 10 checks'
            }
        
        return {'risk': 0, 'message': ''}
    
    def predict_all_targets(self):
        """Run prediction for all monitored targets"""
        stats = self.database.get_statistics()
        predictions = {}
        
        for target_name in stats.keys():
            predictions[target_name] = self.analyze_target(target_name)
        
        return predictions
    
    def get_high_risk_targets(self):
        """Get list of targets at high risk"""
        predictions = self.predict_all_targets()
        
        high_risk = []
        for target, pred in predictions.items():
            if pred['risk_level'] == 'high' and pred['confidence'] >= self.thresholds['prediction_confidence_min']:
                high_risk.append({
                    'target': target,
                    **pred
                })
        
        return high_risk
