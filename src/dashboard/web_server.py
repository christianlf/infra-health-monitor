"""
Web Dashboard Server
Provides real-time HTML dashboard for infrastructure monitoring
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.storage.database import Database


class DashboardServer:
    """Web server for monitoring dashboard"""
    
    def __init__(self, database_path='infra_health.db', host='0.0.0.0', port=8080):
        self.app = Flask(__name__, 
                        template_folder='../../templates',
                        static_folder='../../static')
        CORS(self.app)
        
        self.database = Database(database_path)
        self.host = host
        self.port = port
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Configure Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def api_status():
            """Get current status of all targets"""
            try:
                # Get last check for each target
                stats = self.database.get_statistics()
                
                targets_status = []
                for target_name, target_stats in stats.items():
                    # Get last 10 checks for this target
                    recent_checks = self.database.get_checks_by_target(target_name, limit=10)
                    
                    if recent_checks:
                        last_check = recent_checks[0]
                        status = {
                            'name': target_name,
                            'status': last_check['status'],
                            'last_check': last_check['timestamp'],
                            'latency_ms': last_check.get('latency_ms', 0),
                            'uptime_percent': target_stats['success_rate'],
                            'total_checks': target_stats['total_checks'],
                            'last_error': last_check.get('error_message', '') if last_check['status'] == 'failed' else ''
                        }
                        targets_status.append(status)
                
                return jsonify({
                    'status': 'ok',
                    'timestamp': datetime.now().isoformat(),
                    'targets': targets_status
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/history/<target_name>')
        def api_history(target_name):
            """Get historical data for a specific target"""
            try:
                hours = int(request.args.get('hours', 24))
                checks = self.database.get_checks_by_target(target_name, limit=hours * 60)
                
                history = []
                for check in checks:
                    history.append({
                        'timestamp': check['timestamp'],
                        'status': check['status'],
                        'latency_ms': check.get('latency_ms', 0)
                    })
                
                return jsonify({
                    'status': 'ok',
                    'target': target_name,
                    'history': history
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/api/summary')
        def api_summary():
            """Get overall summary statistics"""
            try:
                stats = self.database.get_statistics()
                
                total_checks = sum(s['total_checks'] for s in stats.values())
                total_success = sum(s['successful'] for s in stats.values())
                total_failed = sum(s['failed'] for s in stats.values())
                
                return jsonify({
                    'status': 'ok',
                    'summary': {
                        'total_targets': len(stats),
                        'total_checks': total_checks,
                        'successful': total_success,
                        'failed': total_failed,
                        'overall_uptime': (total_success / total_checks * 100) if total_checks > 0 else 0
                    }
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def run(self):
        """Start the dashboard server"""
        print(f"🌐 Dashboard server starting on http://{self.host}:{self.port}")
        print(f"📊 Access dashboard at: http://localhost:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)


if __name__ == '__main__':
    # Run standalone
    server = DashboardServer()
    server.run()
