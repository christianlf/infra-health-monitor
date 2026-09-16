# Infrastructure Health Monitor

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Automação de Monitoramento de Saúde de Infraestrutura Corporativa**

Uma ferramenta de linha de comando em Python que realiza verificações automáticas de saúde de infraestrutura de TI (servidores, endpoints de rede, serviços web) e gera relatórios e alertas detalhados.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Motivação](#motivação)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Testes](#testes)
- [Exemplos](#exemplos)
- [Melhorias Futuras](#melhorias-futuras)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

## 🎯 Visão Geral

O **Infrastructure Health Monitor** é uma solução completa para monitoramento proativo de infraestrutura de TI. Ele permite que equipes de suporte e operações automatizem verificações de disponibilidade, meçam latência e respondam rapidamente a incidentes através de alertas configuráveis.

### Tipos de Verificação Suportados

- **Ping (ICMP)**: Verifica conectividade de rede básica
- **Porta TCP**: Testa disponibilidade de serviços em portas específicas
- **HTTP/HTTPS**: Valida status de endpoints web e APIs

## 💡 Motivação

Este projeto nasceu da necessidade de preencher a lacuna entre:
- **Suporte de TI**: Necessidade de ferramentas simples e eficazes para monitoramento básico
- **DevOps/SRE**: Práticas modernas de automação e observabilidade

Objetivos principais:
- Reduzir tempo de detecção de falhas
- Automatizar tarefas repetitivas de verificação
- Fornecer dados históricos para análise de tendências
- Facilitar troubleshooting com logs estruturados

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (CLI)                        │
│              (Orquestração e Interface do Usuário)          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Checkers   │      │   Storage    │      │    Alerts    │
├──────────────┤      ├──────────────┤      ├──────────────┤
│ PingChecker  │      │   Database   │      │AlertManager  │
│ PortChecker  │◄────►│   (SQLite)   │◄────►│   (Logs)     │
│ HTTPChecker  │      │              │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │   Reports    │
                      ├──────────────┤
                      │ReportGen     │
                      │(CSV/JSON)    │
                      └──────────────┘
```

### Componentes Principais

1. **Checkers**: Módulos especializados para cada tipo de verificação
2. **Storage**: Camada de persistência com SQLite para histórico
3. **Alerts**: Sistema de alertas baseado em limites configuráveis
4. **Reports**: Geração de relatórios em múltiplos formatos
5. **Config**: Gerenciamento centralizado de configurações

## ✨ Funcionalidades

### Verificações de Saúde

- ✅ Ping ICMP para verificar conectividade básica
- ✅ Verificação de porta TCP para serviços específicos
- ✅ Verificação HTTP/HTTPS com validação de status code
- ✅ Medição de tempo de resposta para todas as verificações
- ✅ Tratamento robusto de erros e timeouts

### Armazenamento e Histórico

- ✅ Banco de dados SQLite local para histórico completo
- ✅ Índices otimizados para consultas rápidas
- ✅ Rastreamento de falhas consecutivas
- ✅ Cálculo automático de estatísticas

### Sistema de Alertas

- ✅ Alertas baseados em limites de falhas consecutivas
- ✅ Log estruturado de alertas com timestamp
- ✅ Detecção de recuperação de serviços
- ✅ Arquitetura extensível para notificações futuras (email, webhook)

### Relatórios

- ✅ Exportação em CSV para análise em planilhas
- ✅ Exportação em JSON para integração com outras ferramentas
- ✅ Relatório de resumo legível para humanos
- ✅ Estatísticas agregadas (taxa de sucesso, tempo médio de resposta)

### Interface CLI

- ✅ Verificação única sob demanda
- ✅ Monitoramento contínuo com intervalo configurável
- ✅ Geração de relatórios com filtros por período
- ✅ Saída colorida e formatada em tabelas

## 🚀 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Passo a Passo

1. **Clone o repositório**

```bash
git clone <repository-url>
cd infra-health-monitor
```

2. **Crie um ambiente virtual (recomendado)**

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. **Instale as dependências**

```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**

```bash
cp .env.example .env
# Edite .env conforme necessário (valores padrão já funcionam)
```

5. **Configure os alvos de monitoramento**

Edite o arquivo `targets.yaml` para adicionar seus próprios hosts e serviços:

```yaml
targets:
  - name: "Meu Servidor Web"
    type: "http"
    url: "https://meusite.com"
    expected_status: 200
    enabled: true
```

## ⚙️ Configuração

### Arquivo .env

Configure o comportamento da aplicação através do arquivo `.env`:

```bash
# Timeout padrão para operações de rede (segundos)
DEFAULT_TIMEOUT=5

# Número de falhas consecutivas antes de gerar alerta
ALERT_THRESHOLD=3

# Caminho do banco de dados
DATABASE_PATH=health_monitor.db

# Caminho do log de alertas
ALERT_LOG_PATH=alerts.log

# Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

### Arquivo targets.yaml

Defina os alvos a serem monitorados:

```yaml
targets:
  # Verificação de Ping
  - name: "Google DNS"
    type: "ping"
    host: "8.8.8.8"
    enabled: true

  # Verificação de Porta TCP
  - name: "Servidor SSH"
    type: "port"
    host: "192.168.1.10"
    port: 22
    enabled: true

  # Verificação HTTP/HTTPS
  - name: "API de Produção"
    type: "http"
    url: "https://api.minhaempresa.com/health"
    expected_status: 200
    enabled: true
```

## 📖 Uso

### Comando: check

Executa uma verificação única em todos os alvos configurados.

```bash
python main.py check
```

**Exemplo de saída:**

```
+------------------+------+--------+---------------+-------+
| Target           | Type | Status | Response Time | Error |
+==================+======+========+===============+=======+
| Google DNS       | ping | ✓ OK   | 12.45ms       |       |
| GitHub API       | http | ✓ OK   | 234.12ms      |       |
| Local Server     | port | ✗ FAIL | N/A           | Timeout|
+------------------+------+--------+---------------+-------+

Summary:
  Total: 3
  Successful: 2
  Failed: 1
  Success Rate: 66.7%
```

### Comando: monitor

Executa monitoramento contínuo com intervalo especificado.

```bash
python main.py monitor --interval 60
```

**Opções:**
- `--interval`: Intervalo entre verificações em segundos (padrão: 60)

**Exemplo:**

```bash
# Monitorar a cada 5 minutos
python main.py monitor --interval 300

# Parar com Ctrl+C
```

### Comando: report

Gera relatórios a partir do histórico armazenado.

```bash
python main.py report --format csv --last 24h
```

**Opções:**
- `--format`: Formato do relatório (csv, json, summary, all)
- `--last`: Período de tempo (ex: 24h, 7d, 30d)

**Exemplos:**

```bash
# Relatório CSV das últimas 24 horas
python main.py report --format csv --last 24h

# Relatório JSON da última semana
python main.py report --format json --last 7d

# Todos os formatos do último mês
python main.py report --format all --last 30d

# Resumo legível das últimas 12 horas
python main.py report --format summary --last 12h
```

### Opções Globais

```bash
# Usar arquivo de alvos customizado
python main.py --targets custom_targets.yaml check
```

## 📁 Estrutura do Projeto

```
infra-health-monitor/
│
├── src/                          # Código fonte principal
│   ├── __init__.py
│   ├── config.py                 # Configuração e variáveis de ambiente
│   │
│   ├── checkers/                 # Módulos de verificação
│   │   ├── __init__.py
│   │   ├── ping_checker.py       # Verificação ICMP
│   │   ├── port_checker.py       # Verificação TCP
│   │   └── http_checker.py       # Verificação HTTP/HTTPS
│   │
│   ├── storage/                  # Camada de persistência
│   │   ├── __init__.py
│   │   └── database.py           # Interface SQLite
│   │
│   ├── alerts/                   # Sistema de alertas
│   │   ├── __init__.py
│   │   └── alert_manager.py      # Gerenciamento de alertas
│   │
│   └── reports/                  # Geração de relatórios
│       ├── __init__.py
│       └── report_generator.py   # Exportação CSV/JSON
│
├── tests/                        # Testes unitários
│   ├── __init__.py
│   ├── test_ping_checker.py
│   ├── test_port_checker.py
│   ├── test_http_checker.py
│   └── test_database.py
│
├── main.py                       # Ponto de entrada CLI
├── targets.yaml                  # Configuração de alvos
├── .env.example                  # Template de variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
├── requirements.txt              # Dependências Python
└── README.md                     # Esta documentação
```

## 🧪 Testes

O projeto inclui testes unitários para todos os módulos principais.

### Executar todos os testes

```bash
# Com pytest
pytest tests/ -v

# Com unittest
python -m unittest discover tests/ -v
```

### Executar testes específicos

```bash
# Testar apenas checkers
pytest tests/test_ping_checker.py -v

# Testar apenas database
pytest tests/test_database.py -v
```

### Cobertura de testes

```bash
pytest --cov=src tests/
```

## 📊 Exemplos

### Exemplo 1: Monitoramento de Servidor Web

```yaml
# targets.yaml
targets:
  - name: "Website Principal"
    type: "http"
    url: "https://www.meusite.com"
    expected_status: 200
    enabled: true
  
  - name: "API Backend"
    type: "http"
    url: "https://api.meusite.com/health"
    expected_status: 200
    enabled: true
```

```bash
# Monitorar a cada minuto
python main.py monitor --interval 60
```

### Exemplo 2: Verificação de Infraestrutura de Rede

```yaml
# targets.yaml
targets:
  - name: "Gateway Principal"
    type: "ping"
    host: "192.168.1.1"
    enabled: true
  
  - name: "Servidor DNS Interno"
    type: "port"
    host: "192.168.1.53"
    port: 53
    enabled: true
  
  - name: "Firewall"
    type: "ping"
    host: "192.168.1.254"
    enabled: true
```

### Exemplo 3: Monitoramento de Múltiplos Serviços

```yaml
# targets.yaml
targets:
  - name: "PostgreSQL"
    type: "port"
    host: "db.empresa.local"
    port: 5432
    enabled: true
  
  - name: "Redis"
    type: "port"
    host: "cache.empresa.local"
    port: 6379
    enabled: true
  
  - name: "Elasticsearch"
    type: "http"
    url: "http://search.empresa.local:9200"
    expected_status: 200
    enabled: true
```

## 🔮 Melhorias Futuras

### Curto Prazo

- [ ] **Notificações por Email**: Enviar alertas via SMTP
- [ ] **Webhooks**: Integração com Slack, Discord, Microsoft Teams
- [ ] **Dashboard Web**: Interface web simples com Flask/FastAPI
- [ ] **Métricas Prometheus**: Exportar métricas para Prometheus
- [ ] **Configuração de Retry**: Tentativas múltiplas antes de marcar como falha

### Médio Prazo

- [ ] **Suporte a SSL/TLS**: Verificar validade de certificados
- [ ] **Verificação de DNS**: Resolver e validar registros DNS
- [ ] **Monitoramento de Latência**: Alertas baseados em degradação de performance
- [ ] **Agendamento Cron**: Integração nativa para execução agendada
- [ ] **Suporte a SNMP**: Monitorar dispositivos de rede via SNMP

### Longo Prazo

- [ ] **Machine Learning**: Detecção de anomalias usando ML
- [ ] **Grafana Integration**: Dashboards customizáveis
- [ ] **Multi-tenancy**: Suporte para múltiplas organizações
- [ ] **API REST**: Expor funcionalidades via API
- [ ] **Mobile App**: Aplicativo mobile para alertas e visualização

### Extensões de Checkers

- [ ] **Database Checker**: MySQL, PostgreSQL, MongoDB, Redis
- [ ] **FTP/SFTP Checker**: Verificar conectividade de servidores de arquivos
- [ ] **LDAP Checker**: Verificar disponibilidade de Active Directory
- [ ] **Custom Scripts**: Executar scripts customizados como checkers

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga estas etapas:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Diretrizes

- Mantenha o código limpo e bem documentado
- Adicione testes para novas funcionalidades
- Siga as convenções de código Python (PEP 8)
- Atualize a documentação conforme necessário
- Use type hints para todas as funções públicas

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- **Infrastructure Team** - Desenvolvimento inicial

## 🙏 Agradecimentos

- Comunidade Python por suas excelentes bibliotecas
- Equipes de Suporte de TI que inspiraram este projeto
- Todos os contribuidores que ajudaram a melhorar esta ferramenta

## 📞 Suporte

Para dúvidas, sugestões ou problemas:

- Abra uma [Issue](../../issues)
- Consulte a [Wiki](../../wiki)
- Entre em contato com a equipe de infraestrutura

---

**Desenvolvido com ❤️ para facilitar o trabalho de equipes de TI**
