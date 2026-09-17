# 🚀 New Features - Infrastructure Health Monitor v2.0

## 📊 1. Web Dashboard (Real-Time Monitoring)

**NEW!** Beautiful HTML dashboard with real-time status updates!

### Features:
- ✅ **Real-time monitoring** - Updates every 10 seconds
- ✅ **Visual status indicators** - Green (online) / Red (offline)
- ✅ **Uptime metrics** - Per-target uptime percentage
- ✅ **Latency tracking** - See response times at a glance
- ✅ **Responsive design** - Works on desktop, tablet, and mobile

### Usage:
```bash
# Start dashboard server
python dashboard.py

# Access at: http://localhost:8080
```

### Screenshots:
The dashboard shows:
- Overall uptime percentage
- Total checks performed
- Number of monitored targets
- Individual target cards with:
  - Real-time status (online/offline)
  - Current latency
  - Last check time
  - Uptime percentage with progress bar
  - Error messages (if any)

---

## 📈 2. Prometheus Integration

**NEW!** Export metrics for Prometheus + Grafana monitoring!

### Metrics Exposed:
- `infra_health_checks_total` - Total health checks (by target, type, status)
- `infra_health_check_latency_ms` - Latency histogram
- `infra_health_target_up` - Target availability (1=up, 0=down)
- `infra_health_consecutive_failures` - Consecutive failure count
- `infra_health_uptime_percent` - Uptime percentage per target

### Setup:

**1. Enable in `.env`:**
```env
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

**2. Configure Prometheus:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'infra-health-monitor'
    static_configs:
      - targets: ['localhost:9090']
```

**3. View in Grafana:**
- Import pre-built dashboard (coming soon)
- Create custom dashboards with PromQL queries

### Example Queries:
```promql
# Overall uptime
avg(infra_health_uptime_percent)

# Failed checks in last hour
rate(infra_health_checks_total{status="failed"}[1h])

# P95 latency
histogram_quantile(0.95, infra_health_check_latency_ms)
```

---

## 🤖 3. AI-Powered Failure Prediction

**NEW!** Machine Learning predicts failures BEFORE they happen!

### How It Works:
Uses statistical analysis to detect:
- 📈 **Increasing latency trends** - Gradual slowdowns
- 📉 **Rising failure rates** - More frequent errors
- 🔄 **Failure clustering** - Multiple failures close together

### Usage:
```bash
# Run prediction analysis
python predict.py
```

### Output Example:
```
🤖 AI-Powered Failure Prediction
============================================================

📊 Analyzing all targets...

╔════╤══════════════════╤════════════╤════════════╤═══════════════════════════════════╗
║    │ Target           │ Risk Level │ Confidence │ Prediction                        ║
╠════╪══════════════════╪════════════╪════════════╪═══════════════════════════════════╣
║ ✅ │ Google DNS       │ LOW        │ 80%        │ Operating normally                ║
║ ⚡ │ MySQL Server     │ MEDIUM     │ 60%        │ Shows signs of degradation        ║
║ ⚠️  │ ERP System       │ HIGH       │ 90%        │ May fail within 1-2 hours         ║
╚════╧══════════════════╧════════════╧════════════╧═══════════════════════════════════╝

============================================================
⚠️  HIGH RISK TARGETS - IMMEDIATE ATTENTION REQUIRED
============================================================

🚨 ERP System
   Risk: HIGH (confidence: 90%)
   Prediction: ERP System may fail within 1-2 hours
   Indicators:
     • Latency increased 75.3% (120ms → 210ms)
     • Failure rate: 18.2% (11/60 checks)
     • Recent instability: 4 failures in last 10 checks
```

### Predictive Indicators:
- **Latency Analysis**: Detects >50% latency increases
- **Failure Rate**: Triggers on >15% failure rate
- **Pattern Recognition**: Identifies failure clustering
- **Confidence Scoring**: Higher confidence = more reliable prediction

### Benefits:
- 🎯 **Proactive maintenance** - Fix before it breaks
- ⏰ **Reduced downtime** - Catch issues early
- 💰 **Cost savings** - Prevent major outages

---

## 📧 4. Email Notifications (SMTP)

**NEW!** Professional email alerts with HTML formatting!

### Features:
- ✅ **Alert emails** - Service down/recovered
- ✅ **Daily summaries** - Comprehensive reports
- ✅ **HTML formatting** - Professional appearance
- ✅ **Multiple recipients** - Team-wide notifications
- ✅ **SMTP support** - Gmail, Office 365, custom servers

### Setup:

**Gmail (Recommended):**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=InfraHealthMonitor <your-email@gmail.com>
SMTP_TO=admin@example.com,team@example.com
SMTP_USE_TLS=true
```

**⚠️ Gmail Note:** Use [App Password](https://support.google.com/accounts/answer/185833), not regular password!

**Office 365:**
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-password
```

### Email Types:

**1. Alert Email (Service Down):**
```
Subject: 🚨 ALERT: MySQL Database is DOWN

Target: MySQL Database
Status: OFFLINE
Time: 2026-09-17 15:30:22

Host: 192.168.1.15:3306
Type: port
Consecutive Failures: 3
Error: Connection refused
```

**2. Recovery Email:**
```
Subject: ✅ RECOVERED: MySQL Database is back online

Target: MySQL Database
Status: ONLINE
Time: 2026-09-17 15:35:10

Downtime: 5 minutes
Latency: 8ms
```

**3. Daily Summary:**
```
Subject: 📊 Daily Infrastructure Health Report - 2026-09-17

Date: 2026-09-17
Total Checks: 1440
Overall Uptime: 98.5%

Per-Target Statistics:
┌─────────────────┬────────┬────────────┬────────────┬──────────┐
│ Target          │ Checks │ Successful │ Failed     │ Uptime   │
├─────────────────┼────────┼────────────┼────────────┼──────────┤
│ Google DNS      │ 240    │ 240        │ 0          │ 100.0%   │
│ MySQL DB        │ 240    │ 235        │ 5          │ 97.9%    │
└─────────────────┴────────┴────────────┴────────────┴──────────┘
```

---

## 🔒 5. SSL Certificate Monitoring

**NEW!** Monitor SSL/TLS certificates and get alerts BEFORE expiration!

### Features:
- ✅ **Expiration tracking** - Days until certificate expires
- ✅ **Warning levels** - 30 days (warning), 7 days (critical)
- ✅ **Multi-host checking** - Check multiple sites at once
- ✅ **Certificate details** - Issuer, subject, SAN
- ✅ **Expired detection** - Identifies already-expired certs

### Usage:
```bash
# Check single host
python check_ssl.py google.com

# Check multiple hosts
python check_ssl.py google.com github.com stackoverflow.com

# Custom thresholds
python check_ssl.py google.com --warning-days 45 --critical-days 14
```

### Output Example:
```
🔒 SSL Certificate Monitor
================================================================================
Checking 3 host(s)...

╔════╤═════════════════════╤══════════╤═══════════╤═════════════════════╤══════════════════╤════════════════╗
║    │ Host                │ Status   │ Days Left │ Expires             │ Issuer           │ Message        ║
╠════╪═════════════════════╪══════════╪═══════════╪═════════════════════╪══════════════════╪════════════════╣
║ ✅ │ google.com          │ OK       │ 87 days   │ Dec 15 2026         │ Google Trust     │ Valid          ║
║ ⚠️  │ myapp.com           │ WARNING  │ 25 days   │ Oct 12 2026         │ Let's Encrypt    │ Expires soon   ║
║ 🚨 │ legacy-system.com   │ CRITICAL │ 3 days    │ Sep 20 2026         │ DigiCert         │ URGENT         ║
╚════╧═════════════════════╧══════════╧═══════════╧═════════════════════╧══════════════════╧════════════════╝

================================================================================
⚠️  CERTIFICATES REQUIRING ATTENTION
================================================================================

🔔 myapp.com
   Subject: myapp.com
   Issuer: Let's Encrypt Authority X3
   Expires: Oct 12 23:59:59 2026 (25 days)
   Alt Names: myapp.com, www.myapp.com, api.myapp.com

🔔 legacy-system.com
   Subject: legacy-system.com
   Issuer: DigiCert SHA2
   Expires: Sep 20 14:30:00 2026 (3 days)
   Alt Names: legacy-system.com
```

### Integration:
```yaml
# Add to targets.yaml
targets:
  - name: Main Website SSL
    type: ssl
    host: https://www.mycompany.com
    warning_days: 30
    critical_days: 7
```

---

## 📦 Installation & Setup

### 1. Install Dependencies:
```bash
pip install -r requirements.txt
```

New dependencies:
- `flask` - Web dashboard
- `flask-cors` - CORS support
- `prometheus-client` - Metrics export
- `numpy` - ML calculations

### 2. Update Configuration:
```bash
# Copy new config template
cp .env.example .env

# Edit settings
nano .env
```

### 3. Test New Features:
```bash
# Test dashboard
python dashboard.py
# → http://localhost:8080

# Test predictions
python predict.py

# Test SSL monitoring
python check_ssl.py google.com github.com

# Test email (if configured)
python -c "from src.notifications.email_notifier import EmailNotifier; n = EmailNotifier(); print(n.test_connection())"
```

---

## 🎯 Quick Start Guide

### Basic Usage (Unchanged):
```bash
# Single check
python main.py check

# Continuous monitoring
python main.py monitor --interval 60

# Generate reports
python main.py report summary
```

### New Commands:
```bash
# Start web dashboard
python dashboard.py

# Run AI predictions
python predict.py

# Check SSL certificates
python check_ssl.py yoursite.com
```

---

## 🔧 Advanced Configuration

### Prometheus + Grafana Stack:
```yaml
# docker-compose.yml
version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### Email Automation:
```python
# Send daily summaries at 8 AM
# Use cron: 0 8 * * * /usr/bin/python3 /path/to/send_daily_summary.py
```

### ML Tuning:
```env
# Adjust sensitivity
ML_LATENCY_THRESHOLD_PERCENT=50  # Lower = more sensitive
ML_FAILURE_RATE_THRESHOLD=0.15   # Lower = earlier warnings
ML_PREDICTION_WINDOW_HOURS=6     # Longer = more data, slower detection
```

---

## 📚 Documentation

- **README.md** - General documentation
- **TESTING_GUIDE.md** - How to test locally
- **WINDOWS_GUIDE.md** - Windows-specific setup
- **FEATURES.md** (this file) - New features
- **TECHNICAL_CASE_STUDY.md** - Architecture deep-dive

---

## 🤝 Contributing

Have ideas for more features? Open an issue or PR!

**Wishlist:**
- [ ] Telegram bot notifications
- [ ] Mobile app (React Native)
- [ ] Anomaly detection (unsupervised ML)
- [ ] Auto-remediation scripts
- [ ] Multi-region monitoring

---

## 📄 License

MIT License - See LICENSE file

---

**Christian Lindoso Froz**  
📧 christianlindoso18@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/christian-lindoso-froz)  
🐙 [GitHub](https://github.com/christianlf)
