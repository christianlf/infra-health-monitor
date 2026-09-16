# 🏠 Guia Completo: Como Testar o Infra Health Monitor em Casa

**3 formas de testar TUDO sem precisar de infraestrutura corporativa!**

---

## 🎯 Resumo Executivo

Você **NÃO PRECISA** de servidores empresariais para testar o projeto! Existem 3 formas progressivas:

| Método | Dificuldade | O que Testa | Tempo |
|--------|-------------|-------------|-------|
| **1. Alvos Públicos** | ⭐ Fácil | Checkers reais (ping, HTTP, TCP) | 5 min |
| **2. Localhost/Docker** | ⭐⭐ Médio | Simulação de rede local completa | 15 min |
| **3. VMs/Cloud Free** | ⭐⭐⭐ Avançado | Ambiente multi-servidor | 30 min |

---

## 📋 Opção 1: Testar com Alvos Públicos (Mais Fácil)

### Por que funciona?
O projeto **JÁ FUNCIONA** com qualquer host na internet! Você pode monitorar:
- ✅ Sites públicos (google.com, github.com)
- ✅ DNS públicos (8.8.8.8, 1.1.1.1)
- ✅ Servidores web de empresas

### Como fazer:

#### 1. Clone e instale o projeto:
```bash
git clone https://github.com/christianlf/infra-health-monitor.git
cd infra-health-monitor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Configure alvos públicos no `targets.yaml`:
```yaml
# targets.yaml - Monitorando infraestrutura pública
targets:
  # DNS públicos (sempre disponíveis)
  - name: Google DNS
    type: ping
    host: 8.8.8.8
    
  - name: Cloudflare DNS
    type: ping
    host: 1.1.1.1
  
  # Sites públicos (HTTP)
  - name: GitHub
    type: http
    host: https://github.com
    expected_status: 200
    
  - name: Google
    type: http
    host: https://www.google.com
    expected_status: 200
  
  # Portas TCP públicas
  - name: GitHub SSH
    type: port
    host: github.com
    port: 22
    
  - name: Google HTTPS
    type: port
    host: google.com
    port: 443
```

#### 3. Configure o `.env`:
```bash
cp .env.example .env
```

Edite o `.env`:
```env
# Banco de dados local
DATABASE_PATH=./infra_health.db

# Alertas (opcional - apenas local)
ALERT_THRESHOLD=2
ALERT_LOG_FILE=./alerts.log

# Retry (importante para testes reais)
MAX_RETRIES=3
RETRY_DELAY=2

# Webhook (opcional - pode deixar vazio)
ALERT_WEBHOOK_URL=
```

#### 4. Execute os testes:

**Check único:**
```bash
python main.py check
```

**Saída esperada:**
```
✅ Google DNS (8.8.8.8): ONLINE (latency: 15ms)
✅ Cloudflare DNS (1.1.1.1): ONLINE (latency: 12ms)
✅ GitHub (https://github.com): ONLINE (status: 200, latency: 87ms)
✅ Google (https://www.google.com): ONLINE (status: 200, latency: 45ms)
✅ GitHub SSH (github.com:22): ONLINE
✅ Google HTTPS (google.com:443): ONLINE
```

**Monitoramento contínuo (a cada 30s):**
```bash
python main.py monitor --interval 30
```

**Gerar relatório:**
```bash
python main.py report summary
python main.py report csv --output report.csv
python main.py report json --output report.json
```

### 🎥 Prova de Funcionamento (para Portfolio)

**Para impressionar em entrevistas, faça:**

1. **Teste de falha simulada:**
```yaml
# Adicione um host inválido para testar alertas
- name: Servidor Inexistente
  type: ping
  host: 192.0.2.999  # IP inválido
```

2. **Execute e capture:**
```bash
python main.py monitor --interval 10 --duration 60
```

3. **Verifique os alertas:**
```bash
cat alerts.log
```

4. **Gere relatório final:**
```bash
python main.py report summary
```

5. **Tire screenshots:**
- Terminal com checks rodando
- Arquivo `alerts.log` mostrando falhas
- Relatório CSV aberto no Excel
- Banco de dados SQLite no DB Browser

---

## 📋 Opção 2: Testar com Localhost + Docker (Recomendado)

### Por que é melhor?
✅ **Controle total:** Você cria/derruba serviços à vontade  
✅ **Testa falhas reais:** Simula indisponibilidade  
✅ **Impressiona em entrevistas:** Mostra que entende Docker  

### Como fazer:

#### 1. Instale Docker Desktop
- Windows/Mac: https://www.docker.com/products/docker-desktop
- Linux: `sudo apt install docker.io docker-compose`

#### 2. Crie serviços de teste com Docker Compose

Crie `docker-compose-test.yml` na raiz do projeto:

```yaml
version: '3.8'

services:
  # Servidor web Nginx (porta 8080)
  webserver:
    image: nginx:alpine
    ports:
      - "8080:80"
    container_name: test-webserver
  
  # Servidor web Apache (porta 8081)
  apache:
    image: httpd:alpine
    ports:
      - "8081:80"
    container_name: test-apache
  
  # Banco PostgreSQL (porta 5432)
  database:
    image: postgres:alpine
    environment:
      POSTGRES_PASSWORD: test123
    ports:
      - "5432:5432"
    container_name: test-database
  
  # Redis (porta 6379)
  cache:
    image: redis:alpine
    ports:
      - "6379:6379"
    container_name: test-redis
```

#### 3. Suba os containers:
```bash
docker-compose -f docker-compose-test.yml up -d
```

#### 4. Configure `targets.yaml` para localhost:
```yaml
targets:
  # Localhost ping (sempre funciona)
  - name: Localhost
    type: ping
    host: 127.0.0.1
  
  # Containers Docker
  - name: Nginx Web Server
    type: http
    host: http://localhost:8080
    expected_status: 200
    
  - name: Apache Web Server
    type: http
    host: http://localhost:8081
    expected_status: 200
  
  - name: PostgreSQL Port
    type: port
    host: localhost
    port: 5432
    
  - name: Redis Port
    type: port
    host: localhost
    port: 6379
```

#### 5. Execute o monitor:
```bash
python main.py monitor --interval 10
```

#### 6. **Simule falhas (DEMO PERFEITA!):**

**Terminal 1 (monitor rodando):**
```bash
python main.py monitor --interval 5
```

**Terminal 2 (simulando falhas):**
```bash
# Derrubar Nginx (vai gerar ALERTA!)
docker stop test-webserver

# Aguardar 30s (ver alertas)
sleep 30

# Subir Nginx (vai gerar RECOVERY!)
docker start test-webserver

# Derrubar Redis
docker stop test-redis

# Aguardar 30s
sleep 30

# Subir Redis
docker start test-redis
```

**Resultado:**
- ❌ Alertas de `DOWN` no `alerts.log`
- ✅ Alertas de `RECOVERY` quando subir
- 📊 Histórico completo no banco SQLite
- 📈 Relatórios com métricas reais

#### 7. Análise dos resultados:
```bash
# Ver alertas
cat alerts.log

# Relatório completo
python main.py report summary

# Abrir banco de dados (instale: sudo apt install sqlitebrowser)
sqlitebrowser infra_health.db
```

---

## 📋 Opção 3: Testar com VMs ou Cloud Gratuita (Avançado)

### Por que fazer?
✅ **Simula ambiente corporativo real**  
✅ **Testa latência entre redes**  
✅ **Impressiona MUITO em entrevistas**  

### Opções de Cloud Gratuita:

| Provider | Free Tier | Uso |
|----------|-----------|-----|
| **Oracle Cloud** | 2 VMs ARM (24GB RAM) | **MELHOR** - sempre grátis |
| **Google Cloud** | $300 créditos (90 dias) | VMs pequenas |
| **AWS Free Tier** | 750h/mês t2.micro (12 meses) | EC2 básico |
| **Azure** | $200 créditos (30 dias) | VMs Windows/Linux |

### Como fazer (Oracle Cloud - Recomendado):

#### 1. Criar conta gratuita:
- Acesse: https://www.oracle.com/cloud/free/
- Cadastre-se (não cobra cartão!)
- Ative 2 VMs ARM gratuitamente

#### 2. Criar 2 VMs:
```
VM1 (Web Server):
- Ubuntu 22.04
- IP público: 150.230.x.x
- Portas abertas: 22, 80, 443

VM2 (Database):
- Ubuntu 22.04
- IP público: 150.230.y.y
- Portas abertas: 22, 3306, 5432
```

#### 3. Instalar serviços nas VMs:

**VM1 (via SSH):**
```bash
# Conectar via SSH
ssh ubuntu@150.230.x.x

# Instalar Nginx
sudo apt update
sudo apt install nginx -y

# Verificar
curl http://localhost
```

**VM2 (via SSH):**
```bash
# Conectar via SSH
ssh ubuntu@150.230.y.y

# Instalar MySQL
sudo apt update
sudo apt install mysql-server -y

# Abrir porta externamente
sudo ufw allow 3306
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# Trocar bind-address = 0.0.0.0
sudo systemctl restart mysql
```

#### 4. Configure `targets.yaml` para as VMs:
```yaml
targets:
  # VM1 - Web Server
  - name: Oracle Cloud Web Server
    type: ping
    host: 150.230.x.x
    
  - name: Oracle Nginx HTTP
    type: http
    host: http://150.230.x.x
    expected_status: 200
    
  - name: Oracle SSH Port
    type: port
    host: 150.230.x.x
    port: 22
  
  # VM2 - Database
  - name: Oracle Cloud Database Server
    type: ping
    host: 150.230.y.y
    
  - name: Oracle MySQL Port
    type: port
    host: 150.230.y.y
    port: 3306
```

#### 5. Execute o monitor da sua casa:
```bash
python main.py monitor --interval 60
```

**Você verá latências reais!**
```
✅ Oracle Cloud Web Server: ONLINE (latency: 187ms)
✅ Oracle Nginx HTTP: ONLINE (status: 200, latency: 205ms)
✅ Oracle Cloud Database Server: ONLINE (latency: 192ms)
✅ Oracle MySQL Port: ONLINE
```

---

## 🧪 Executar Unit Tests (Sempre Funciona!)

Os **testes unitários** funcionam **SEMPRE**, sem precisar de internet ou servidores!

### Como rodar:
```bash
# Ativar venv
source venv/bin/activate

# Instalar pytest (se não tiver)
pip install pytest

# Rodar TODOS os testes
pytest tests/ -v

# Rodar testes específicos
pytest tests/test_ping_checker.py -v
pytest tests/test_http_checker.py -v
pytest tests/test_database.py -v

# Ver cobertura de código
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

**Saída esperada:**
```
tests/test_ping_checker.py::TestPingChecker::test_successful_ping PASSED
tests/test_ping_checker.py::TestPingChecker::test_failed_ping PASSED
tests/test_ping_checker.py::TestPingChecker::test_retry_logic PASSED
tests/test_ping_checker.py::TestPingChecker::test_input_sanitization PASSED
tests/test_port_checker.py::TestPortChecker::test_open_port PASSED
tests/test_port_checker.py::TestPortChecker::test_closed_port PASSED
tests/test_http_checker.py::TestHTTPChecker::test_successful_request PASSED
tests/test_http_checker.py::TestHTTPChecker::test_retry_on_failure PASSED
tests/test_database.py::TestDatabase::test_record_check PASSED

========================= 36 passed in 2.14s =========================
```

---

## 🎬 Roteiro para Demonstração em Entrevista

### Cenário 1: Demo Rápida (5 minutos)
```bash
# 1. Clonar projeto
git clone https://github.com/christianlf/infra-health-monitor.git
cd infra-health-monitor

# 2. Instalar
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Rodar check rápido (alvos públicos)
python main.py check

# 4. Ver relatório
python main.py report summary

# 5. Mostrar código
cat src/checkers/ping_checker.py
```

### Cenário 2: Demo Completa com Docker (15 minutos)
```bash
# 1. Subir containers de teste
docker-compose -f docker-compose-test.yml up -d

# 2. Configurar targets.yaml (já pronto acima)

# 3. Monitor em tempo real
python main.py monitor --interval 5

# 4. Em outro terminal: simular falha
docker stop test-webserver

# 5. Ver alertas
cat alerts.log

# 6. Recuperar serviço
docker start test-webserver

# 7. Gerar relatório final
python main.py report csv --output demo_report.csv
```

### Cenário 3: Demo Avançada com Testes (20 minutos)
```bash
# 1. Rodar unit tests
pytest tests/ -v --cov=src

# 2. Mostrar cobertura de código
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# 3. Explicar arquitetura
# - Mostrar src/checkers/ (SRP)
# - Mostrar src/storage/database.py (persistência)
# - Mostrar src/alerts/alert_manager.py (webhooks)

# 4. Demo de retry logic
# - Derrubar container
# - Mostrar logs de retry (3 tentativas)
# - Ver exponential backoff no código

# 5. Demo de segurança
# - Mostrar input sanitization em ping_checker.py
# - Explicar prevenção de command injection
```

---

## 📸 Screenshots Essenciais para Portfolio

### 1. Terminal com monitor rodando:
```bash
python main.py monitor --interval 10
```
**Capturar:** Saída colorida com checks passando

### 2. Arquivo de alertas:
```bash
cat alerts.log
```
**Capturar:** Alertas de DOWN e RECOVERY

### 3. Relatório CSV no Excel/LibreOffice:
```bash
python main.py report csv --output report.csv
libreoffice report.csv
```
**Capturar:** Tabela com métricas formatadas

### 4. Banco de dados SQLite:
```bash
sqlitebrowser infra_health.db
```
**Capturar:** Tabela `checks` com histórico

### 5. Cobertura de testes:
```bash
pytest tests/ --cov=src --cov-report=html
firefox htmlcov/index.html
```
**Capturar:** Report com 85%+ cobertura

---

## 🚀 Checklist de Testes Completos

Antes de colocar no portfolio/entrevista, teste:

### Funcionalidades:
- [ ] ✅ Ping check com host público
- [ ] ✅ HTTP check com site público
- [ ] ✅ Port check com porta aberta
- [ ] ❌ Ping check com host inválido (deve alertar)
- [ ] ❌ HTTP check com site down (deve alertar)
- [ ] ❌ Port check com porta fechada (deve alertar)
- [ ] 🔄 Retry logic (derrubar e ver 3 tentativas)
- [ ] 📊 Relatório CSV gerado
- [ ] 📊 Relatório JSON gerado
- [ ] 📊 Relatório summary no terminal
- [ ] 💾 Dados salvos no SQLite
- [ ] 🔔 Alertas salvos em `alerts.log`
- [ ] 🔔 Recovery alerts funcionando
- [ ] 🧪 Unit tests passando (pytest)

### Opcionais:
- [ ] 🐳 Docker Compose rodando
- [ ] 🌐 Webhook Discord/Slack funcionando
- [ ] ☁️ Monitoramento de VM na cloud

---

## 🎓 Perguntas de Entrevista + Respostas

### P: "Como você testou esse projeto sem infraestrutura corporativa?"

**R:** "Usei 3 abordagens:
1. **Alvos públicos:** DNS do Google (8.8.8.8), GitHub, sites públicos - funcionam como qualquer endpoint corporativo
2. **Docker local:** Criei 4 containers (Nginx, PostgreSQL, Redis) para simular servidores reais, inclusive testando falhas controladas
3. **Cloud gratuita:** Deploy em Oracle Cloud (free tier) para testar latências reais e múltiplas zonas

Além disso, os **36 unit tests** validam toda a lógica (retry, sanitization, alerts) sem depender de rede."

### P: "Como você simula falhas de rede?"

**R:** "Com Docker Compose, eu posso derrubar containers específicos (`docker stop`) e observar:
- **Retry logic:** 3 tentativas com exponential backoff
- **Alertas:** Threshold de 2 falhas consecutivas
- **Recovery:** Detecção automática quando o serviço volta

Também testei com hosts inválidos (192.0.2.999) para validar tratamento de erros."

### P: "Prove que o projeto funciona."

**R:** [Mostrar]
1. **Tela:** `python main.py monitor` rodando
2. **Arquivo:** `alerts.log` com alertas reais
3. **Banco:** `infra_health.db` com 200+ checks registrados
4. **Testes:** `pytest` com 36/36 passed
5. **Relatório:** CSV com métricas (disponibilidade 98.7%)

---

## 🎯 Resumo Final

| O que | Como | Tempo | Dificuldade |
|-------|------|-------|-------------|
| **Teste básico** | Alvos públicos (Google, GitHub) | 5 min | ⭐ Fácil |
| **Teste intermediário** | Docker Compose (4 containers) | 15 min | ⭐⭐ Médio |
| **Teste avançado** | Oracle Cloud (2 VMs grátis) | 30 min | ⭐⭐⭐ Difícil |
| **Unit tests** | pytest (sempre funciona) | 2 min | ⭐ Fácil |

**Recomendação:** Comece com alvos públicos (5 min) e Docker (15 min). Isso é **mais do que suficiente** para impressionar em entrevistas!

---

**Christian Lindoso Froz**  
📧 christianlindoso18@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/christian-lindoso-froz)  
🐙 [GitHub](https://github.com/christianlf)
