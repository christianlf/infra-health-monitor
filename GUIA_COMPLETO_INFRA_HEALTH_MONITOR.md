# 🔍 GUIA COMPLETO: Infra Health Monitor

## 📋 ÍNDICE

1. [Resumo Executivo](#resumo-executivo)
2. [Funcionalidades Principais](#funcionalidades-principais)
3. [Arquitetura e Componentes](#arquitetura-e-componentes)
4. [Adaptações e Customizações](#adaptações-e-customizações)
5. [Integração com Sistemas Externos](#integração-com-sistemas-externos)
6. [Casos de Uso Reais](#casos-de-uso-reais)
7. [Guia de Implementação](#guia-de-implementação)
8. [Troubleshooting e FAQ](#troubleshooting-e-faq)

---

## 1. 📊 RESUMO EXECUTIVO

### O que é?

O **Infra Health Monitor** é uma ferramenta CLI (Command-Line Interface) em Python que automatiza o monitoramento de saúde de infraestrutura de TI. Ele realiza verificações automáticas de disponibilidade, armazena histórico, gera alertas e produz relatórios.

### Para quem serve?

- ✅ **MSPs (Managed Service Providers)** gerenciando 10-50 clientes
- ✅ **Times de DevOps/SRE** em startups e PMEs
- ✅ **Suporte de TI Nível 1/2** para troubleshooting rápido
- ✅ **Administradores de sistemas** em ambientes corporativos
- ✅ **Desenvolvedores** validando ambientes antes de deploy

### Problema que resolve:

**Antes (Manual):**
- ⏱️ 15-30 minutos/dia testando ping, telnet, curl manualmente
- 📝 Logs em Excel/planilhas (propenso a erros)
- 🔥 Descoberta reativa de falhas (cliente reclama primeiro)
- 📉 Sem histórico para análise de padrões

**Depois (Automatizado):**
- ⚡ 30 segundos para verificar 50 endpoints (paralelo)
- 💾 Histórico persistente em SQLite (queries SQL)
- 🚨 Alertas proativos (threshold configurável)
- 📊 Relatórios CSV/JSON para análise

---

## 2. 🎯 FUNCIONALIDADES PRINCIPAIS

### 2.1 Tipos de Verificação (Checkers)

#### **A) Ping (ICMP)**
Verifica conectividade básica de rede via protocolo ICMP.

**O que faz:**
- Envia pacotes ICMP echo request
- Mede tempo de resposta (latência)
- Detecta perda de pacotes

**Use quando:**
- Testar se um servidor está "vivo" na rede
- Medir latência de links WAN/VPN
- Diagnosticar problemas de roteamento

**Exemplo de configuração:**
```yaml
targets:
  - name: "Gateway Principal"
    type: "ping"
    host: "10.0.0.1"
    enabled: true
  
  - name: "Servidor DNS Google"
    type: "ping"
    host: "8.8.8.8"
    enabled: true
```

**Recursos técnicos:**
- ✅ Retry logic (3 tentativas com exponential backoff)
- ✅ Input sanitization (previne command injection)
- ✅ Validação RFC 1123 para hostnames
- ✅ Suporte IPv4 e IPv6

---

#### **B) TCP Port Check**
Testa se uma porta TCP específica está aberta e aceitando conexões.

**O que faz:**
- Tenta estabelecer conexão TCP na porta especificada
- Verifica timeout de conexão
- Não envia dados (apenas handshake TCP)

**Use quando:**
- Verificar se um serviço está rodando (ex: MySQL na porta 3306)
- Testar firewall/regras de segurança
- Diagnosticar problemas de bind/listen

**Exemplo de configuração:**
```yaml
targets:
  - name: "Banco de Dados PostgreSQL"
    type: "port"
    host: "db.empresa.com"
    port: 5432
    enabled: true
  
  - name: "SSH Servidor Produção"
    type: "port"
    host: "prod.empresa.com"
    port: 22
    enabled: true
  
  - name: "Redis Cache"
    type: "port"
    host: "cache.empresa.com"
    port: 6379
    enabled: true
```

**Portas comuns:**
- 22 (SSH)
- 80/443 (HTTP/HTTPS)
- 3306 (MySQL)
- 5432 (PostgreSQL)
- 27017 (MongoDB)
- 6379 (Redis)
- 1433 (SQL Server)
- 3389 (RDP)

---

#### **C) HTTP/HTTPS Check**
Valida endpoints web através de requisições HTTP/HTTPS.

**O que faz:**
- Faz requisição GET no endpoint
- Verifica código de status HTTP (200, 404, 500, etc.)
- Mede tempo de resposta
- Valida certificados SSL/TLS

**Use quando:**
- Monitorar APIs REST
- Verificar uptime de sites/aplicações web
- Testar balanceadores de carga
- Validar health checks de microserviços

**Exemplo de configuração:**
```yaml
targets:
  - name: "API Produção"
    type: "http"
    url: "https://api.empresa.com/health"
    expected_status: 200
    enabled: true
  
  - name: "Website Público"
    type: "http"
    url: "https://www.empresa.com"
    expected_status: 200
    enabled: true
  
  - name: "Admin Panel"
    type: "http"
    url: "https://admin.empresa.com/login"
    expected_status: 200
    enabled: true
```

**Status codes suportados:**
- 200 (OK)
- 301/302 (Redirect)
- 401 (Unauthorized)
- 404 (Not Found)
- 500 (Internal Server Error)
- 503 (Service Unavailable)

---

### 2.2 Sistema de Armazenamento (Storage)

#### **SQLite Database**

**Esquema de tabelas:**

```sql
-- Tabela principal: histórico de verificações
CREATE TABLE checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_name TEXT NOT NULL,
    check_type TEXT NOT NULL,
    target_host TEXT,
    status TEXT NOT NULL,           -- 'ok' ou 'fail'
    response_time REAL,             -- em milissegundos
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índices para queries rápidas
CREATE INDEX idx_timestamp ON checks(timestamp);
CREATE INDEX idx_target_name ON checks(target_name);
CREATE INDEX idx_status ON checks(status);
```

**Funcionalidades:**
- ✅ ACID transactions (dados nunca corrompem)
- ✅ WAL mode (Write-Ahead Logging para melhor concorrência)
- ✅ Queries SQL diretas para análise customizada
- ✅ Backup simples (copiar arquivo `.db`)

**Queries úteis:**
```sql
-- Últimas 24h de falhas
SELECT * FROM checks 
WHERE status = 'fail' 
  AND timestamp > datetime('now', '-24 hours')
ORDER BY timestamp DESC;

-- Latência média por target (última semana)
SELECT target_name, 
       AVG(response_time) as avg_latency,
       COUNT(*) as total_checks
FROM checks 
WHERE timestamp > datetime('now', '-7 days')
  AND status = 'ok'
GROUP BY target_name;

-- Taxa de disponibilidade (uptime %)
SELECT target_name,
       (SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as uptime_percent
FROM checks
WHERE timestamp > datetime('now', '-30 days')
GROUP BY target_name;
```

---

### 2.3 Sistema de Alertas (Alerts)

#### **Threshold-Based Alerting**

**Como funciona:**
1. Monitora falhas consecutivas por target
2. Quando atinge threshold configurado → dispara alerta
3. Registra em log local (`alerts.log`)
4. Opcionalmente envia webhook (Discord/Slack/Teams)

**Configuração:**
```bash
# .env
ALERT_THRESHOLD=3              # Alerta após 3 falhas seguidas
ALERT_LOG_PATH=alerts.log      # Arquivo de log local
ALERT_WEBHOOK_URL=https://...  # Webhook externo (opcional)
```

**Exemplo de alerta:**
```
[2026-09-16 16:30:45] ALERT: API Produção está DOWN
  - Tipo: http
  - Host: https://api.empresa.com/health
  - Falhas consecutivas: 3
  - Último erro: Connection timeout after 5s
  - Ação recomendada: Verificar status do servidor
```

#### **Recovery Notifications**

Quando um target volta a funcionar após falha:
```
[2026-09-16 16:35:12] RECOVERY: API Produção está UP
  - Tempo de downtime: 4 minutos e 27 segundos
  - Checks falhados: 3
  - Latência atual: 120ms
```

---

### 2.4 Sistema de Relatórios (Reports)

#### **A) CSV Export**
Ideal para análise em Excel/LibreOffice Calc.

```bash
python main.py report --format csv --last 24h
```

**Output:** `report_YYYYMMDD_HHMMSS.csv`
```csv
target_name,check_type,target_host,status,response_time,error_message,timestamp
API Produção,http,https://api.empresa.com/health,ok,120.5,,2026-09-16 16:30:00
Gateway,ping,10.0.0.1,ok,15.2,,2026-09-16 16:30:05
Database,port,db.empresa.com:5432,fail,5000,Connection timeout,2026-09-16 16:30:10
```

---

#### **B) JSON Export**
Ideal para integração com ferramentas de análise (Python scripts, APIs).

```bash
python main.py report --format json --last 7d
```

**Output:** `report_YYYYMMDD_HHMMSS.json`
```json
[
  {
    "target_name": "API Produção",
    "check_type": "http",
    "target_host": "https://api.empresa.com/health",
    "status": "ok",
    "response_time": 120.5,
    "error_message": null,
    "timestamp": "2026-09-16T16:30:00"
  },
  {
    "target_name": "Database",
    "check_type": "port",
    "target_host": "db.empresa.com:5432",
    "status": "fail",
    "response_time": 5000.0,
    "error_message": "Connection timeout",
    "timestamp": "2026-09-16T16:30:10"
  }
]
```

---

#### **C) Summary Report**
Visão consolidada com estatísticas.

```bash
python main.py report --format summary --last 30d
```

**Output (terminal):**
```
╔══════════════════════════════════════════════════════════════╗
║            INFRASTRUCTURE HEALTH SUMMARY                     ║
║            Período: Últimos 30 dias                          ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────┬──────────┬─────────┬────────────┬──────────┐
│ Target              │ Checks   │ Uptime  │ Avg Latency│ Failures │
├─────────────────────┼──────────┼─────────┼────────────┼──────────┤
│ API Produção        │ 8,640    │ 99.85%  │ 125ms      │ 13       │
│ Gateway Principal   │ 8,640    │ 100.00% │ 12ms       │ 0        │
│ Database PostgreSQL │ 8,640    │ 98.20%  │ 8ms        │ 155      │
│ Website Público     │ 8,640    │ 99.95%  │ 180ms      │ 4        │
└─────────────────────┴──────────┴─────────┴────────────┴──────────┘

🎯 Overall Infrastructure Health: 99.50%
⚠️  Total Incidents: 172
⏱️  Average Response Time: 81ms
```

---

### 2.5 CLI Interface (Command-Line)

#### **Comando: check**
Execução única de todas as verificações.

```bash
python main.py check

# Output:
┌─────────────────────┬────────┬──────────────┬──────────┐
│ Target              │ Type   │ Status       │ Latency  │
├─────────────────────┼────────┼──────────────┼──────────┤
│ API Produção        │ http   │ ✅ OK        │ 120ms    │
│ Gateway Principal   │ ping   │ ✅ OK        │ 15ms     │
│ Database            │ port   │ ❌ FAIL      │ timeout  │
│ Website             │ http   │ ✅ OK        │ 200ms    │
└─────────────────────┴────────┴──────────────┴──────────┘

✅ 3 targets OK
❌ 1 target FAILED
```

---

#### **Comando: monitor**
Execução contínua com intervalo configurável.

```bash
# Roda a cada 5 minutos (300 segundos)
python main.py monitor --interval 300

# Output (logs contínuos):
[2026-09-16 16:00:00] Starting monitoring cycle...
[2026-09-16 16:00:05] ✅ API Produção: OK (120ms)
[2026-09-16 16:00:06] ✅ Gateway: OK (15ms)
[2026-09-16 16:00:07] ❌ Database: FAIL (timeout)
[2026-09-16 16:00:08] ✅ Website: OK (200ms)
[2026-09-16 16:00:08] Cycle completed. Next run in 300s...
[2026-09-16 16:05:00] Starting monitoring cycle...
```

**Uso com systemd (Linux):**
```ini
# /etc/systemd/system/infra-monitor.service
[Unit]
Description=Infrastructure Health Monitor
After=network.target

[Service]
Type=simple
User=monitoring
WorkingDirectory=/opt/infra-health-monitor
ExecStart=/usr/bin/python3 main.py monitor --interval 300
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable infra-monitor.service
sudo systemctl start infra-monitor.service
sudo systemctl status infra-monitor.service
```

---

#### **Comando: report**
Gera relatórios em diferentes formatos.

```bash
# CSV (últimas 24 horas)
python main.py report --format csv --last 24h

# JSON (últimos 7 dias)
python main.py report --format json --last 7d

# Summary (últimos 30 dias)
python main.py report --format summary --last 30d

# Período customizado
python main.py report --format csv --start "2026-09-01" --end "2026-09-15"
```

---

## 3. 🏗️ ARQUITETURA E COMPONENTES

### 3.1 Estrutura de Diretórios

```
infra-health-monitor/
├── src/
│   ├── __init__.py
│   ├── config.py                    # Carrega .env e configurações
│   ├── executor.py                  # Execução paralela (ThreadPoolExecutor)
│   │
│   ├── checkers/                    # Módulos de verificação
│   │   ├── __init__.py
│   │   ├── ping_checker.py          # Ping ICMP
│   │   ├── port_checker.py          # TCP port check
│   │   └── http_checker.py          # HTTP/HTTPS check
│   │
│   ├── storage/                     # Persistência de dados
│   │   ├── __init__.py
│   │   └── database.py              # SQLite operations
│   │
│   ├── alerts/                      # Sistema de alertas
│   │   ├── __init__.py
│   │   └── alert_manager.py         # Threshold detection + webhooks
│   │
│   └── reports/                     # Geração de relatórios
│       ├── __init__.py
│       └── report_generator.py      # CSV/JSON/Summary export
│
├── tests/                           # Testes unitários
│   ├── __init__.py
│   ├── test_ping_checker.py
│   ├── test_port_checker.py
│   ├── test_http_checker.py
│   ├── test_database.py
│   ├── test_ping_checker_v2.py      # Testes retry logic
│   └── test_alert_manager_v2.py     # Testes webhooks
│
├── main.py                          # CLI entry point
├── targets.yaml                     # Configuração de alvos
├── .env                             # Variáveis de ambiente (não commitado)
├── .env.example                     # Template de configuração
├── requirements.txt                 # Dependências Python
├── README.md                        # Documentação principal
├── TECHNICAL_CASE_STUDY.md          # Análise técnica detalhada
└── REFACTORING_REPORT.md            # Documentação v2.0
```

---

### 3.2 Fluxo de Execução

```
┌─────────────────────────────────────────────────────────────┐
│                      main.py (CLI)                          │
│              argparse: check / monitor / report             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │ config.py (load .env)   │
         │ targets.yaml (load)     │
         └─────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │   executor.py (ParallelExecutor) │
    │   ThreadPoolExecutor (10 workers)│
    └───────┬──────────────────────────┘
            │
            ▼
   ┌────────────────────────┐
   │  checkers/             │
   │  - ping_checker.py     │
   │  - port_checker.py     │──┐
   │  - http_checker.py     │  │
   └────────────────────────┘  │
                               │
            ┌──────────────────┘
            │
            ▼
   ┌────────────────────────┐
   │  storage/database.py   │
   │  SQLite: INSERT result │
   └─────────┬──────────────┘
             │
             ▼
   ┌────────────────────────────┐
   │  alerts/alert_manager.py   │
   │  - Check threshold         │
   │  - Log to file             │
   │  - Send webhook (optional) │
   └─────────┬──────────────────┘
             │
             ▼
   ┌────────────────────────────┐
   │  reports/report_generator  │
   │  - CSV export              │
   │  - JSON export             │
   │  - Summary display         │
   └────────────────────────────┘
```

---

### 3.3 Componentes Técnicos

#### **config.py**
```python
class Config:
    def __init__(self):
        load_dotenv()
        self.default_timeout = int(os.getenv('DEFAULT_TIMEOUT', 5))
        self.alert_threshold = int(os.getenv('ALERT_THRESHOLD', 3))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.retry_delay = float(os.getenv('RETRY_DELAY', 1.0))
        self.database_path = os.getenv('DATABASE_PATH', 'monitor.db')
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL', '')
```

---

#### **executor.py (Parallel Execution)**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class ParallelExecutor:
    def __init__(self, max_workers=10):
        self.max_workers = max_workers
    
    def execute_checks(self, targets):
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._perform_check, t): t 
                for t in targets
            }
            for future in as_completed(futures):
                results.append(future.result())
        return results
```

**Performance:**
- 50 targets × 5s timeout = 250s (sequencial)
- 50 targets ÷ 10 workers = 25s (paralelo)
- **Ganho: 10x mais rápido**

---

## 4. 🔧 ADAPTAÇÕES E CUSTOMIZAÇÕES

### 4.1 Adicionar Novo Tipo de Checker

**Exemplo: DNS Resolution Check**

**Passo 1:** Criar `src/checkers/dns_checker.py`
```python
import socket
import time
from typing import Dict, Any

class DNSChecker:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
    
    def check(self, hostname: str, record_type: str = 'A') -> Dict[str, Any]:
        start_time = time.time()
        try:
            socket.setdefaulttimeout(self.timeout)
            
            if record_type == 'A':
                result = socket.gethostbyname(hostname)
            elif record_type == 'AAAA':
                result = socket.getaddrinfo(hostname, None, socket.AF_INET6)[0][4][0]
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'ok',
                'resolved_ip': result,
                'response_time': round(response_time, 2),
                'error': None
            }
        except socket.gaierror as e:
            return {
                'status': 'fail',
                'resolved_ip': None,
                'response_time': None,
                'error': f'DNS resolution failed: {str(e)}'
            }
```

**Passo 2:** Adicionar no `targets.yaml`
```yaml
targets:
  - name: "DNS Check - Google"
    type: "dns"
    hostname: "google.com"
    record_type: "A"
    enabled: true
```

**Passo 3:** Integrar no `executor.py`
```python
from src.checkers.dns_checker import DNSChecker

def _perform_single_check(self, target):
    if target['type'] == 'dns':
        checker = DNSChecker(timeout=self.config.default_timeout)
        result = checker.check(target['hostname'], target.get('record_type', 'A'))
    # ... outros tipos
```

---

### 4.2 Adicionar Novo Formato de Relatório

**Exemplo: HTML Report com Gráficos**

**Passo 1:** Instalar dependências
```bash
pip install jinja2 plotly
```

**Passo 2:** Adicionar método em `report_generator.py`
```python
import plotly.graph_objects as go
from jinja2 import Template

def generate_html_report(self, period: str):
    checks = self.db.get_checks_last_period(period)
    
    # Processar dados para gráficos
    uptime_data = self._calculate_uptime_by_target(checks)
    
    # Criar gráfico com Plotly
    fig = go.Figure(data=[
        go.Bar(
            x=list(uptime_data.keys()),
            y=list(uptime_data.values()),
            marker_color='lightblue'
        )
    ])
    fig.update_layout(title='Uptime % por Target')
    graph_html = fig.to_html(include_plotlyjs='cdn')
    
    # Template HTML
    html_template = """
    <!DOCTYPE html>
    <html>
    <head><title>Infrastructure Health Report</title></head>
    <body>
        <h1>Infrastructure Health Report</h1>
        <p>Período: {{ period }}</p>
        {{ graph_html | safe }}
        <table>
            <tr><th>Target</th><th>Status</th><th>Uptime</th></tr>
            {% for target, uptime in uptime_data.items() %}
            <tr><td>{{ target }}</td><td>{{ uptime }}%</td></tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_output = template.render(
        period=period,
        graph_html=graph_html,
        uptime_data=uptime_data
    )
    
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, 'w') as f:
        f.write(html_output)
    
    return filename
```

**Passo 3:** Adicionar comando CLI
```bash
python main.py report --format html --last 7d
```

---

### 4.3 Integrar com Banco de Dados Externo

**Exemplo: PostgreSQL ao invés de SQLite**

**Passo 1:** Instalar driver
```bash
pip install psycopg2-binary
```

**Passo 2:** Adicionar configuração
```bash
# .env
DATABASE_TYPE=postgresql
POSTGRES_HOST=db.empresa.com
POSTGRES_PORT=5432
POSTGRES_DB=monitoring
POSTGRES_USER=monitor_user
POSTGRES_PASSWORD=senha_segura
```

**Passo 3:** Criar `src/storage/postgres_database.py`
```python
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, List

class PostgresDatabase:
    def __init__(self, config):
        self.conn = psycopg2.connect(
            host=config.postgres_host,
            port=config.postgres_port,
            database=config.postgres_db,
            user=config.postgres_user,
            password=config.postgres_password
        )
        self._init_schema()
    
    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id SERIAL PRIMARY KEY,
                target_name VARCHAR(255) NOT NULL,
                check_type VARCHAR(50) NOT NULL,
                target_host TEXT,
                status VARCHAR(10) NOT NULL,
                response_time REAL,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_timestamp (timestamp),
                INDEX idx_target (target_name),
                INDEX idx_status (status)
            );
        """)
        self.conn.commit()
    
    def insert_check(self, data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO checks (target_name, check_type, target_host, 
                                status, response_time, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['target_name'],
            data['check_type'],
            data['target_host'],
            data['status'],
            data.get('response_time'),
            data.get('error_message')
        ))
        self.conn.commit()
```

**Passo 4:** Modificar factory em `main.py`
```python
from src.storage.database import Database
from src.storage.postgres_database import PostgresDatabase

def get_database(config):
    if config.database_type == 'postgresql':
        return PostgresDatabase(config)
    else:
        return Database(config.database_path)
```

---

### 4.4 Customizar Lógica de Alertas

**Exemplo: Alertas por Severidade (Critical/Warning/Info)**

**Passo 1:** Adicionar níveis de severidade em `targets.yaml`
```yaml
targets:
  - name: "API Produção"
    type: "http"
    url: "https://api.empresa.com/health"
    severity: "critical"    # critical | warning | info
    alert_threshold: 2      # Alerta após 2 falhas (critical)
    enabled: true
  
  - name: "Website Institucional"
    type: "http"
    url: "https://www.empresa.com"
    severity: "warning"
    alert_threshold: 5      # Alerta após 5 falhas (menos crítico)
    enabled: true
```

**Passo 2:** Modificar `alert_manager.py`
```python
def _trigger_alert(self, target, consecutive_failures):
    severity = target.get('severity', 'info')
    threshold = target.get('alert_threshold', self.default_threshold)
    
    if consecutive_failures < threshold:
        return  # Não atingiu threshold
    
    # Emoji por severidade
    severity_emoji = {
        'critical': '🔴',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    message = f"{severity_emoji[severity]} [{severity.upper()}] ALERT: {target['name']} está DOWN\n"
    message += f"  - Falhas consecutivas: {consecutive_failures}\n"
    message += f"  - Threshold: {threshold}\n"
    
    # Log local
    self._log_to_file(message)
    
    # Webhook (apenas critical e warning)
    if severity in ['critical', 'warning'] and self.webhook_url:
        self._send_webhook(message, severity)
```

---

## 5. 🔗 INTEGRAÇÃO COM SISTEMAS EXTERNOS

### 5.1 Discord Webhook

**Configuração:**
```bash
# .env
ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/AbCdEfGhIjKlMnOpQrStUvWxYz
```

**Formato de mensagem (já implementado):**
```json
{
  "content": "🔴 ALERT: API Produção está DOWN",
  "embeds": [
    {
      "title": "Infrastructure Alert",
      "description": "API Produção falhou 3 vezes consecutivas",
      "color": 15158332,
      "fields": [
        {"name": "Target", "value": "API Produção", "inline": true},
        {"name": "Type", "value": "http", "inline": true},
        {"name": "Failures", "value": "3", "inline": true}
      ],
      "timestamp": "2026-09-16T16:30:00Z"
    }
  ]
}
```

**Customização avançada:**
```python
def _send_discord_webhook(self, target, consecutive_failures):
    payload = {
        "content": f"🔴 **ALERT:** {target['name']} está DOWN",
        "embeds": [{
            "title": "Infrastructure Health Alert",
            "description": f"Target falhou {consecutive_failures} vezes consecutivas",
            "color": 15158332,  # Vermelho
            "fields": [
                {"name": "🎯 Target", "value": target['name'], "inline": True},
                {"name": "📊 Type", "value": target['type'], "inline": True},
                {"name": "❌ Failures", "value": str(consecutive_failures), "inline": True},
                {"name": "🔗 Host", "value": target.get('host', target.get('url', 'N/A')), "inline": False}
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Infra Health Monitor"}
        }]
    }
    requests.post(self.webhook_url, json=payload)
```

---

### 5.2 Slack Webhook

**Configuração:**
```bash
# .env
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

**Formato de mensagem:**
```python
def _send_slack_webhook(self, target, consecutive_failures):
    payload = {
        "text": f"🔴 *ALERT:* {target['name']} está DOWN",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Infrastructure Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Target:*\n{target['name']}"},
                    {"type": "mrkdwn", "text": f"*Type:*\n{target['type']}"},
                    {"type": "mrkdwn", "text": f"*Failures:*\n{consecutive_failures}"},
                    {"type": "mrkdwn", "text": f"*Host:*\n{target.get('host', 'N/A')}"}
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
    }
    requests.post(self.webhook_url, json=payload)
```

---

### 5.3 Microsoft Teams Webhook

**Configuração:**
```bash
# .env
ALERT_WEBHOOK_URL=https://outlook.office.com/webhook/abcd-1234.../IncomingWebhook/xyz-5678...
```

**Formato de mensagem:**
```python
def _send_teams_webhook(self, target, consecutive_failures):
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"Alert: {target['name']} is DOWN",
        "themeColor": "FF0000",
        "title": "🚨 Infrastructure Health Alert",
        "sections": [
            {
                "activityTitle": f"**{target['name']}** está DOWN",
                "activitySubtitle": f"Falhas consecutivas: {consecutive_failures}",
                "facts": [
                    {"name": "Target:", "value": target['name']},
                    {"name": "Type:", "value": target['type']},
                    {"name": "Failures:", "value": str(consecutive_failures)},
                    {"name": "Host:", "value": target.get('host', 'N/A')},
                    {"name": "Timestamp:", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                ]
            }
        ]
    }
    requests.post(self.webhook_url, json=payload)
```

---

### 5.4 Prometheus Exporter

**Expor métricas para Prometheus coletar.**

**Passo 1:** Instalar dependência
```bash
pip install prometheus-client
```

**Passo 2:** Criar `src/exporters/prometheus_exporter.py`
```python
from prometheus_client import start_http_server, Gauge, Counter
import time

class PrometheusExporter:
    def __init__(self, port=9090):
        self.port = port
        
        # Métricas
        self.target_up = Gauge(
            'infra_monitor_target_up',
            'Target is up (1) or down (0)',
            ['target_name', 'check_type']
        )
        
        self.response_time = Gauge(
            'infra_monitor_response_time_ms',
            'Response time in milliseconds',
            ['target_name', 'check_type']
        )
        
        self.total_checks = Counter(
            'infra_monitor_checks_total',
            'Total number of checks performed',
            ['target_name', 'check_type', 'status']
        )
    
    def start(self):
        start_http_server(self.port)
        print(f"Prometheus exporter running on port {self.port}")
    
    def update_metrics(self, target, result):
        labels = {
            'target_name': target['name'],
            'check_type': target['type']
        }
        
        # Target up/down
        self.target_up.labels(**labels).set(1 if result['status'] == 'ok' else 0)
        
        # Response time
        if result.get('response_time'):
            self.response_time.labels(**labels).set(result['response_time'])
        
        # Total checks
        self.total_checks.labels(status=result['status'], **labels).inc()
```

**Passo 3:** Integrar no `main.py`
```python
from src.exporters.prometheus_exporter import PrometheusExporter

exporter = PrometheusExporter(port=9090)
exporter.start()

# No loop de monitoring:
result = executor.execute_checks(targets)
for r in result:
    exporter.update_metrics(target, r)
```

**Passo 4:** Configurar Prometheus (`prometheus.yml`)
```yaml
scrape_configs:
  - job_name: 'infra-health-monitor'
    static_configs:
      - targets: ['localhost:9090']
```

**Queries PromQL:**
```promql
# Taxa de uptime por target
avg_over_time(infra_monitor_target_up[5m])

# Latência média (últimos 5 minutos)
avg_over_time(infra_monitor_response_time_ms[5m])

# Total de falhas (última hora)
increase(infra_monitor_checks_total{status="fail"}[1h])
```

---

### 5.5 Grafana Dashboard

**Importar métricas do Prometheus e criar painéis.**

**Exemplo de painel:**

**Panel 1: Uptime Status**
```json
{
  "title": "Target Uptime Status",
  "targets": [
    {
      "expr": "infra_monitor_target_up",
      "legendFormat": "{{target_name}}"
    }
  ],
  "type": "stat",
  "options": {
    "colorMode": "background",
    "graphMode": "area",
    "orientation": "horizontal"
  }
}
```

**Panel 2: Response Time**
```json
{
  "title": "Response Time (ms)",
  "targets": [
    {
      "expr": "infra_monitor_response_time_ms",
      "legendFormat": "{{target_name}}"
    }
  ],
  "type": "graph",
  "yaxes": [{"format": "ms"}]
}
```

---

### 5.6 Elasticsearch + Kibana

**Enviar logs para Elasticsearch para análise.**

**Passo 1:** Instalar cliente
```bash
pip install elasticsearch
```

**Passo 2:** Criar `src/exporters/elasticsearch_exporter.py`
```python
from elasticsearch import Elasticsearch
from datetime import datetime

class ElasticsearchExporter:
    def __init__(self, hosts=['localhost:9200']):
        self.es = Elasticsearch(hosts)
        self.index_name = 'infra-monitor-checks'
        self._create_index()
    
    def _create_index(self):
        mapping = {
            "mappings": {
                "properties": {
                    "target_name": {"type": "keyword"},
                    "check_type": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "response_time": {"type": "float"},
                    "error_message": {"type": "text"},
                    "timestamp": {"type": "date"}
                }
            }
        }
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, body=mapping)
    
    def send_check(self, target, result):
        document = {
            "target_name": target['name'],
            "check_type": target['type'],
            "target_host": target.get('host', target.get('url')),
            "status": result['status'],
            "response_time": result.get('response_time'),
            "error_message": result.get('error'),
            "timestamp": datetime.utcnow()
        }
        self.es.index(index=self.index_name, body=document)
```

**Kibana Queries:**
```
# Falhas nas últimas 24h
status: "fail" AND timestamp:[now-24h TO now]

# Latência acima de 500ms
response_time: >500

# Erros por tipo de check
status: "fail" | stats count by check_type
```

---

## 6. 📚 CASOS DE USO REAIS

### Caso 1: MSP com 30 Clientes

**Cenário:**
Empresa de TI gerencia infraestrutura de 30 clientes (5-10 servidores cada).

**Configuração:**
```yaml
# targets.yaml
targets:
  # Cliente A
  - name: "[ClienteA] Servidor Web"
    type: "http"
    url: "https://www.clientea.com"
    severity: "critical"
    enabled: true
  
  - name: "[ClienteA] Banco de Dados"
    type: "port"
    host: "db.clientea.com"
    port: 3306
    severity: "critical"
    enabled: true
  
  # Cliente B
  - name: "[ClienteB] Gateway VPN"
    type: "ping"
    host: "vpn.clienteb.com"
    severity: "warning"
    enabled: true
  
  # ... (repetir para 30 clientes)
```

**Execução:**
```bash
# Rodar a cada 5 minutos
python main.py monitor --interval 300

# Gerar relatório semanal para cada cliente
python main.py report --format csv --last 7d --filter "ClienteA"
```

**Benefícios:**
- ✅ Detecção proativa de falhas (antes do cliente reclamar)
- ✅ Relatórios semanais/mensais para SLA
- ✅ Histórico de disponibilidade (prova de uptime)
- ✅ Redução de tempo de troubleshooting

---

### Caso 2: DevOps em Startup

**Cenário:**
Time de 5 desenvolvedores com microserviços em Kubernetes.

**Configuração:**
```yaml
targets:
  # Microserviços
  - name: "Auth Service"
    type: "http"
    url: "http://auth-service.default.svc.cluster.local:8080/health"
    expected_status: 200
    enabled: true
  
  - name: "User Service"
    type: "http"
    url: "http://user-service.default.svc.cluster.local:8080/health"
    expected_status: 200
    enabled: true
  
  # Bancos de dados
  - name: "PostgreSQL Master"
    type: "port"
    host: "postgres-master.default.svc.cluster.local"
    port: 5432
    enabled: true
  
  # Infraestrutura
  - name: "Kubernetes API"
    type: "https"
    url: "https://kubernetes.default.svc.cluster.local:443"
    expected_status: 401  # Esperado (sem auth)
    enabled: true
```

**Integração CI/CD:**
```bash
# .gitlab-ci.yml ou .github/workflows/check.yml
pre-deploy-check:
  script:
    - python main.py check
    - if [ $? -ne 0 ]; then echo "Health check failed! Aborting deploy."; exit 1; fi
```

**Benefícios:**
- ✅ Pre-deploy validation (evita deploy em ambiente com problemas)
- ✅ Monitoring de health checks internos
- ✅ Alertas no Slack para downtime crítico

---

### Caso 3: Suporte de TI Corporativo

**Cenário:**
Empresa com 200 funcionários, 50 servidores locais.

**Configuração:**
```yaml
targets:
  # Infraestrutura crítica
  - name: "Active Directory DC1"
    type: "port"
    host: "dc1.empresa.local"
    port: 389  # LDAP
    severity: "critical"
    enabled: true
  
  - name: "Exchange Server"
    type: "port"
    host: "mail.empresa.local"
    port: 25  # SMTP
    severity: "critical"
    enabled: true
  
  - name: "File Server"
    type: "port"
    host: "fs1.empresa.local"
    port: 445  # SMB
    severity: "warning"
    enabled: true
  
  # Impressoras de rede
  - name: "Impressora RH"
    type: "ping"
    host: "10.0.0.50"
    severity: "info"
    enabled: true
```

**Dashboard HTML:**
```bash
# Gerar dashboard HTML a cada hora (cron job)
0 * * * * cd /opt/infra-monitor && python main.py report --format html --last 24h && cp report.html /var/www/html/status.html
```

**Benefícios:**
- ✅ Dashboard web para equipe de suporte visualizar status
- ✅ Alertas proativos (ex: impressora offline)
- ✅ Histórico para análise de incidentes recorrentes

---

### Caso 4: E-commerce em Black Friday

**Cenário:**
Loja online com pico de tráfego em datas especiais.

**Configuração:**
```yaml
targets:
  # Front-end
  - name: "Website Home"
    type: "http"
    url: "https://www.loja.com"
    expected_status: 200
    severity: "critical"
    enabled: true
  
  - name: "API Checkout"
    type: "http"
    url: "https://api.loja.com/v1/checkout/status"
    expected_status: 200
    severity: "critical"
    enabled: true
  
  # Pagamento
  - name: "Gateway Pagamento"
    type: "http"
    url: "https://payment-gateway.provider.com/health"
    expected_status: 200
    severity: "critical"
    enabled: true
  
  # Banco de dados
  - name: "Database Read Replica"
    type: "port"
    host: "db-read.loja.com"
    port: 5432
    severity: "warning"
    enabled: true
```

**Configuração agressiva:**
```bash
# .env
DEFAULT_TIMEOUT=3              # Timeout mais curto
ALERT_THRESHOLD=1              # Alerta na primeira falha
MAX_RETRIES=5                  # Mais retries (evitar falso positivo)
RETRY_DELAY=0.5                # Retry mais rápido
```

**Monitoramento intensivo:**
```bash
# Rodar a cada 30 segundos durante Black Friday
python main.py monitor --interval 30
```

**Benefícios:**
- ✅ Detecção de falhas em <1 minuto
- ✅ Alertas críticos no Teams para equipe de plantão
- ✅ Logs detalhados para post-mortem

---

## 7. 🚀 GUIA DE IMPLEMENTAÇÃO

### 7.1 Instalação do Zero

**Passo 1:** Clonar repositório
```bash
git clone https://github.com/christianlf/infra-health-monitor.git
cd infra-health-monitor
```

**Passo 2:** Criar ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

**Passo 3:** Instalar dependências
```bash
pip install -r requirements.txt
```

**Passo 4:** Configurar environment
```bash
cp .env.example .env
nano .env  # ou vim, code, notepad++
```

**Editar `.env`:**
```bash
DEFAULT_TIMEOUT=5
ALERT_THRESHOLD=3
MAX_RETRIES=3
RETRY_DELAY=1.0
DATABASE_PATH=monitor.db
ALERT_LOG_PATH=alerts.log
LOG_LEVEL=INFO
ALERT_WEBHOOK_URL=  # Deixe vazio se não usar webhook
```

**Passo 5:** Configurar targets
```bash
nano targets.yaml
```

**Exemplo básico:**
```yaml
targets:
  - name: "Google DNS"
    type: "ping"
    host: "8.8.8.8"
    enabled: true
  
  - name: "Meu Site"
    type: "http"
    url: "https://meusite.com"
    expected_status: 200
    enabled: true
```

**Passo 6:** Testar
```bash
python main.py check
```

---

### 7.2 Deploy em Produção (Linux)

**Opção A: Systemd Service**

**Criar service file:**
```bash
sudo nano /etc/systemd/system/infra-monitor.service
```

**Conteúdo:**
```ini
[Unit]
Description=Infrastructure Health Monitor
After=network.target

[Service]
Type=simple
User=monitoring
Group=monitoring
WorkingDirectory=/opt/infra-health-monitor
ExecStart=/opt/infra-health-monitor/venv/bin/python main.py monitor --interval 300
Restart=on-failure
RestartSec=10s
StandardOutput=append:/var/log/infra-monitor/output.log
StandardError=append:/var/log/infra-monitor/error.log

[Install]
WantedBy=multi-user.target
```

**Ativar:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable infra-monitor.service
sudo systemctl start infra-monitor.service
sudo systemctl status infra-monitor.service
```

**Logs:**
```bash
sudo journalctl -u infra-monitor.service -f
```

---

**Opção B: Docker Container**

**Criar `Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Volume para persistência
VOLUME ["/app/data"]

# Environment variables
ENV DATABASE_PATH=/app/data/monitor.db
ENV ALERT_LOG_PATH=/app/data/alerts.log

# Comando padrão
CMD ["python", "main.py", "monitor", "--interval", "300"]
```

**Build:**
```bash
docker build -t infra-health-monitor:v2.0 .
```

**Run:**
```bash
docker run -d \
  --name infra-monitor \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/targets.yaml:/app/targets.yaml:ro \
  -v $(pwd)/.env:/app/.env:ro \
  infra-health-monitor:v2.0
```

**Logs:**
```bash
docker logs -f infra-monitor
```

---

**Opção C: Kubernetes CronJob**

**Criar `k8s-cronjob.yaml`:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: infra-health-monitor
  namespace: monitoring
spec:
  schedule: "*/5 * * * *"  # A cada 5 minutos
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: monitor
            image: infra-health-monitor:v2.0
            command: ["python", "main.py", "check"]
            env:
            - name: DATABASE_PATH
              value: "/data/monitor.db"
            - name: ALERT_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: monitor-secrets
                  key: webhook-url
            volumeMounts:
            - name: config
              mountPath: /app/targets.yaml
              subPath: targets.yaml
            - name: data
              mountPath: /data
          volumes:
          - name: config
            configMap:
              name: monitor-config
          - name: data
            persistentVolumeClaim:
              claimName: monitor-data-pvc
          restartPolicy: OnFailure
```

**Deploy:**
```bash
kubectl apply -f k8s-cronjob.yaml
```

---

### 7.3 Configuração Avançada

#### **Multi-Environment Setup**

**Estrutura:**
```
infra-health-monitor/
├── configs/
│   ├── production.yaml
│   ├── staging.yaml
│   └── development.yaml
├── .env.production
├── .env.staging
└── .env.development
```

**Rodar com ambiente específico:**
```bash
# Produção
export ENV=production
python main.py monitor --config configs/production.yaml

# Staging
export ENV=staging
python main.py monitor --config configs/staging.yaml
```

---

#### **Log Rotation**

**Configurar logrotate:**
```bash
sudo nano /etc/logrotate.d/infra-monitor
```

**Conteúdo:**
```
/var/log/infra-monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 monitoring monitoring
    sharedscripts
    postrotate
        systemctl reload infra-monitor.service > /dev/null 2>&1 || true
    endscript
}
```

---

## 8. 🔧 TROUBLESHOOTING E FAQ

### FAQ 1: "Por que meu ping está falhando sempre?"

**Possíveis causas:**

1. **Firewall bloqueando ICMP:**
```bash
# Testar manualmente
ping -c 1 8.8.8.8

# Se funcionar manualmente mas falha no monitor:
# Verificar permissões de usuário
```

2. **Hostname inválido:**
```bash
# Checar validação
# O monitor rejeita hostnames com caracteres especiais
# Aceito: "server.com", "10.0.0.1"
# Rejeitado: "server; malicious", "$(whoami)"
```

3. **Timeout muito curto:**
```bash
# .env
DEFAULT_TIMEOUT=10  # Aumentar para 10 segundos
```

---

### FAQ 2: "Como exportar apenas falhas no relatório?"

**SQL Query customizada:**
```bash
sqlite3 monitor.db "SELECT * FROM checks WHERE status='fail' AND timestamp > datetime('now', '-24 hours');" > failures.txt
```

**Ou adicionar filtro no código:**
```python
# src/reports/report_generator.py
def generate_failures_only_report(self, period):
    query = """
        SELECT * FROM checks 
        WHERE status = 'fail' 
          AND timestamp > datetime('now', ?)
        ORDER BY timestamp DESC
    """
    # ... resto do código
```

---

### FAQ 3: "Webhook não está funcionando"

**Checklist de debug:**

1. **Testar webhook manualmente:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content": "Test message"}' \
  https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

2. **Verificar logs:**
```bash
tail -f /var/log/infra-monitor/error.log | grep webhook
```

3. **Validar URL no `.env`:**
```bash
# Correto
ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/123456/abcdef

# Incorreto (espaços, quebra de linha)
ALERT_WEBHOOK_URL = https://discord...  # Espaços antes/depois do =
```

4. **Verificar firewall/proxy:**
```bash
# Testar conectividade
curl -I https://discord.com
```

---

### FAQ 4: "Banco de dados está travando"

**Sintomas:**
- `database is locked` error
- Checks muito lentos

**Soluções:**

1. **Habilitar WAL mode:**
```python
# src/storage/database.py
def __init__(self, db_path):
    self.conn = sqlite3.connect(db_path)
    self.conn.execute("PRAGMA journal_mode=WAL")  # Adicionar esta linha
```

2. **Reduzir workers paralelos:**
```bash
# .env
MAX_WORKERS=5  # Reduzir de 10 para 5
```

3. **Migrar para PostgreSQL** (se >100 targets)

---

### FAQ 5: "Como monitorar o próprio monitor?"

**Watchdog script:**
```bash
#!/bin/bash
# /usr/local/bin/monitor-watchdog.sh

# Verificar se processo está rodando
if ! pgrep -f "main.py monitor" > /dev/null; then
    echo "[$(date)] Monitor process not running. Restarting..."
    systemctl restart infra-monitor.service
    
    # Enviar alerta crítico
    curl -X POST -H "Content-Type: application/json" \
      -d '{"content": "🔴 CRITICAL: Infra Monitor stopped and was restarted"}' \
      "$WEBHOOK_URL"
fi

# Verificar se database está acessível
if ! sqlite3 /opt/infra-monitor/monitor.db "SELECT 1;" > /dev/null 2>&1; then
    echo "[$(date)] Database check failed"
    # Alerta
fi
```

**Cron job:**
```bash
# Rodar a cada 5 minutos
*/5 * * * * /usr/local/bin/monitor-watchdog.sh >> /var/log/monitor-watchdog.log 2>&1
```

---

### FAQ 6: "Performance está lenta com muitos targets"

**Otimizações:**

1. **Aumentar workers:**
```bash
# .env
MAX_WORKERS=20  # Padrão é 10
```

2. **Reduzir timeout:**
```bash
DEFAULT_TIMEOUT=3  # Padrão é 5
```

3. **Desabilitar targets não críticos:**
```yaml
targets:
  - name: "Target Opcional"
    enabled: false  # Desabilita temporariamente
```

4. **Sharding (múltiplas instâncias):**
```bash
# Instância 1: Targets 1-50
python main.py monitor --config targets-1-50.yaml

# Instância 2: Targets 51-100
python main.py monitor --config targets-51-100.yaml
```

---

## 📊 RESUMO FINAL

### ✅ Funcionalidades Core

| Funcionalidade | Descrição | Status |
|----------------|-----------|--------|
| **Ping (ICMP)** | Verificação de conectividade básica | ✅ Completo |
| **Port Check** | Teste de portas TCP | ✅ Completo |
| **HTTP Check** | Validação de endpoints HTTP/HTTPS | ✅ Completo |
| **Retry Logic** | 3 tentativas com exponential backoff | ✅ v2.0 |
| **Input Sanitization** | Prevenção command injection | ✅ v2.0 |
| **SQLite Storage** | Persistência ACID com WAL mode | ✅ Completo |
| **Threshold Alerts** | Alertas após N falhas consecutivas | ✅ Completo |
| **Webhook Integration** | Discord/Slack/Teams | ✅ v2.0 |
| **Parallel Execution** | ThreadPoolExecutor (10x speedup) | ✅ v2.0 |
| **CSV Export** | Relatórios em CSV | ✅ Completo |
| **JSON Export** | Relatórios em JSON | ✅ Completo |
| **Summary Report** | Estatísticas consolidadas | ✅ Completo |
| **CLI Interface** | Comandos check/monitor/report | ✅ Completo |

---

### 🔧 Adaptações Possíveis

| Adaptação | Complexidade | Tempo estimado |
|-----------|--------------|----------------|
| Adicionar novo checker (DNS, SSL cert) | Baixa | 2-3 horas |
| Integrar PostgreSQL | Média | 4-6 horas |
| Criar dashboard HTML | Média | 6-8 horas |
| Prometheus exporter | Média | 4-5 horas |
| Elasticsearch integration | Alta | 8-10 horas |
| Multi-tenant support | Alta | 15-20 horas |
| API REST interface | Alta | 20-30 horas |

---

### 🔗 Sistemas Compatíveis

**Webhooks nativos:**
- ✅ Discord
- ✅ Slack
- ✅ Microsoft Teams
- ✅ Mattermost
- ✅ Rocket.Chat

**Métricas/Observabilidade:**
- ✅ Prometheus
- ✅ Grafana
- ✅ Elasticsearch + Kibana
- ✅ InfluxDB + Chronograf
- ⚠️ Datadog (requer adapter)
- ⚠️ New Relic (requer adapter)

**Bancos de dados:**
- ✅ SQLite (nativo)
- ✅ PostgreSQL (fácil adaptação)
- ✅ MySQL/MariaDB (fácil adaptação)
- ⚠️ MongoDB (requer redesign de schema)

**Deployment:**
- ✅ Linux (systemd)
- ✅ Docker
- ✅ Kubernetes
- ✅ Windows (Task Scheduler)
- ✅ MacOS (launchd)

---

### 📈 Limites Recomendados

| Cenário | Max Targets | Interval | Workers | Database |
|---------|-------------|----------|---------|----------|
| **Pequeno** | 10-20 | 5 min | 5 | SQLite |
| **Médio** | 20-50 | 5 min | 10 | SQLite + WAL |
| **Grande** | 50-100 | 3 min | 15-20 | PostgreSQL |
| **Enterprise** | 100+ | 1 min | 30+ | PostgreSQL + sharding |

---

## 🎉 CONCLUSÃO

O **Infra Health Monitor** é uma ferramenta completa, modular e extensível para automação de monitoramento de infraestrutura. Com arquitetura limpa e boa documentação, permite desde uso básico (ping/port checks) até integrações avançadas (Prometheus, Grafana, Elasticsearch).

**Pontos fortes:**
- ✅ Zero-config para começar (SQLite + YAML)
- ✅ Resiliente (retry logic, graceful degradation)
- ✅ Seguro (input validation, no shell injection)
- ✅ Performático (10x speedup com paralelização)
- ✅ Extensível (fácil adicionar novos checkers/exporters)

**Para dúvidas:**
- 📧 Email: christianlindoso18@gmail.com
- 🐙 GitHub: https://github.com/christianlf/infra-health-monitor
- 📄 Technical Case Study: [PDF](https://github.com/christianlf/infra-health-monitor/blob/main/TECHNICAL_CASE_STUDY.pdf)

**Bom monitoramento! 🚀**
