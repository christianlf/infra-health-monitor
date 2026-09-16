# 🪟 Guia de Instalação e Teste - Windows

**Guia específico para testar o Infra Health Monitor no Windows 10/11**

---

## 📋 Pré-requisitos

### 1. Python 3.10+
Verifique se já tem instalado:
```powershell
python --version
```

Se não tiver, baixe em: https://www.python.org/downloads/

**IMPORTANTE:** Marque a opção "Add Python to PATH" durante a instalação!

### 2. Git (opcional, mas recomendado)
Baixe em: https://git-scm.com/download/win

### 3. Docker Desktop (para testes avançados)
Baixe em: https://www.docker.com/products/docker-desktop

---

## 🚀 Instalação Rápida (PowerShell)

### Passo 1: Clonar o projeto
```powershell
# Se tiver Git instalado:
git clone https://github.com/christianlf/infra-health-monitor.git
cd infra-health-monitor

# OU baixe o ZIP manualmente:
# https://github.com/christianlf/infra-health-monitor/archive/refs/heads/main.zip
# Extraia e abra o PowerShell na pasta
```

### Passo 2: Criar ambiente virtual
```powershell
python -m venv venv
```

### Passo 3: Ativar ambiente virtual

**PowerShell (recomendado):**
```powershell
venv\Scripts\Activate.ps1
```

**Se der erro de política de execução:**
```powershell
# Execute como administrador:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Depois tente novamente:
venv\Scripts\Activate.ps1
```

**Prompt de Comando (CMD):**
```cmd
venv\Scripts\activate.bat
```

### Passo 4: Instalar dependências
```powershell
pip install -r requirements.txt
```

### Passo 5: Configurar
```powershell
# Copiar arquivos de exemplo
copy .env.example .env
copy targets-public.yaml targets.yaml
```

### Passo 6: Testar!
```powershell
python main.py check
```

---

## ✅ Teste Básico (Alvos Públicos)

### Configuração:
O arquivo `targets-public.yaml` já está pronto! Ele testa:
- ✅ Google DNS (8.8.8.8)
- ✅ Cloudflare DNS (1.1.1.1)
- ✅ GitHub (https://github.com)
- ✅ Google (https://www.google.com)

### Comandos:
```powershell
# Check único
python main.py check

# Monitoramento contínuo (Ctrl+C para parar)
python main.py monitor --interval 30

# Gerar relatórios
python main.py report summary
python main.py report csv --output relatorio.csv
python main.py report json --output relatorio.json
```

### Ver resultados:
```powershell
# Ver alertas
type alerts.log

# Abrir CSV no Excel
start relatorio.csv

# Ver banco de dados (instale: https://sqlitebrowser.org/)
# sqlitebrowser infra_health.db
```

---

## 🐳 Teste Avançado (Docker)

### Pré-requisito: Docker Desktop instalado e rodando

### Passo 1: Subir containers
```powershell
docker-compose -f docker-compose-test.yml up -d
```

### Passo 2: Verificar containers
```powershell
docker ps
```

Você deve ver 4 containers rodando:
- test-webserver (Nginx)
- test-apache
- test-database (PostgreSQL)
- test-redis

### Passo 3: Configurar targets
```powershell
copy targets-docker.yaml targets.yaml
```

### Passo 4: Monitorar
```powershell
python main.py monitor --interval 10
```

### Passo 5: Simular falhas (em outro PowerShell)
```powershell
# Derrubar Nginx
docker stop test-webserver

# Aguardar 30 segundos (ver alertas no outro terminal)

# Recuperar Nginx
docker start test-webserver

# Ver alertas
type alerts.log
```

### Passo 6: Parar containers
```powershell
docker-compose -f docker-compose-test.yml down
```

---

## 🧪 Rodar Testes Unitários

### Instalar pytest:
```powershell
pip install pytest pytest-cov
```

### Executar todos os testes:
```powershell
pytest tests/ -v
```

### Ver cobertura de código:
```powershell
pytest tests/ --cov=src --cov-report=html
start htmlcov\index.html
```

---

## 🛠️ Troubleshooting Windows

### Problema 1: "python não é reconhecido"
**Solução:** Adicione Python ao PATH:
1. Painel de Controle → Sistema → Configurações avançadas
2. Variáveis de ambiente
3. Editar PATH do usuário
4. Adicionar: `C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python310`

**OU** reinstale Python marcando "Add to PATH"

### Problema 2: "pip não encontrado"
**Solução:**
```powershell
python -m pip install --upgrade pip
```

### Problema 3: Erro ao instalar pacotes
**Solução:**
```powershell
# Atualizar pip
python -m pip install --upgrade pip

# Instalar Visual C++ Build Tools (se necessário)
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Problema 4: PowerShell não executa scripts
**Solução:**
```powershell
# Como administrador:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problema 5: Porta já em uso (Docker)
**Solução:**
```powershell
# Ver processos usando a porta
netstat -ano | findstr :8080

# Matar processo (substitua PID)
taskkill /PID 1234 /F

# OU mudar porta no docker-compose-test.yml
```

### Problema 6: Docker não inicia
**Solução:**
1. Verificar se Hyper-V está ativado (Windows 10 Pro+)
2. Verificar se WSL 2 está instalado:
   ```powershell
   wsl --list --verbose
   ```
3. Atualizar WSL:
   ```powershell
   wsl --update
   ```

---

## 📸 Ferramentas Úteis para Windows

### 1. Windows Terminal (recomendado)
Baixe na Microsoft Store - melhor que PowerShell padrão!

### 2. DB Browser for SQLite
https://sqlitebrowser.org/
- Visualizar banco `infra_health.db`
- Ver histórico de checks
- Exportar dados

### 3. Visual Studio Code
https://code.visualstudio.com/
- Editor de código
- Terminal integrado
- Extensões Python

### 4. Docker Desktop
https://www.docker.com/products/docker-desktop
- Gerenciar containers
- Ver logs
- Dashboard visual

---

## 🎬 Demo Completa no Windows (15 minutos)

### Terminal 1 (Windows Terminal/PowerShell):
```powershell
# 1. Preparar ambiente
cd infra-health-monitor
venv\Scripts\Activate.ps1

# 2. Subir Docker
docker-compose -f docker-compose-test.yml up -d

# 3. Configurar
copy targets-docker.yaml targets.yaml

# 4. Iniciar monitor
python main.py monitor --interval 5
```

### Terminal 2 (outro PowerShell):
```powershell
# Navegar para a pasta
cd infra-health-monitor

# Simular falhas
docker stop test-webserver
timeout /t 30 /nobreak  # Aguardar 30s
docker start test-webserver

docker stop test-database
timeout /t 30 /nobreak
docker start test-database
```

### Terminal 3 (análise):
```powershell
cd infra-health-monitor

# Ver alertas
type alerts.log

# Gerar relatórios
python main.py report summary
python main.py report csv --output demo.csv

# Abrir no Excel
start demo.csv

# Ver banco (se tiver DB Browser instalado)
sqlitebrowser infra_health.db
```

---

## 🎯 Comandos Essenciais Windows

### Gerenciamento de venv:
```powershell
# Criar
python -m venv venv

# Ativar (PowerShell)
venv\Scripts\Activate.ps1

# Ativar (CMD)
venv\Scripts\activate.bat

# Desativar
deactivate
```

### Docker:
```powershell
# Subir containers
docker-compose -f docker-compose-test.yml up -d

# Ver containers rodando
docker ps

# Ver logs
docker logs test-webserver

# Parar container
docker stop test-webserver

# Iniciar container
docker start test-webserver

# Remover tudo
docker-compose -f docker-compose-test.yml down
```

### Python:
```powershell
# Executar script
python main.py check

# Instalar pacote
pip install nome-pacote

# Ver pacotes instalados
pip list

# Rodar testes
pytest tests/ -v
```

### Arquivos:
```powershell
# Copiar
copy origem destino

# Ver conteúdo
type arquivo.txt

# Listar arquivos
dir

# Criar pasta
mkdir pasta

# Deletar arquivo
del arquivo.txt
```

---

## 📋 Checklist de Instalação

Antes de começar a testar, verifique:

- [ ] ✅ Python 3.10+ instalado (`python --version`)
- [ ] ✅ Pip funcionando (`pip --version`)
- [ ] ✅ Venv criado (`venv\Scripts\Activate.ps1`)
- [ ] ✅ Dependências instaladas (`pip list`)
- [ ] ✅ Arquivo `.env` configurado
- [ ] ✅ Arquivo `targets.yaml` configurado
- [ ] ✅ Docker Desktop instalado (para testes avançados)
- [ ] ✅ Containers rodando (`docker ps`)

---

## 🎓 Diferenças Linux vs Windows

| Comando | Linux/Mac | Windows PowerShell | Windows CMD |
|---------|-----------|-------------------|-------------|
| **Ativar venv** | `source venv/bin/activate` | `venv\Scripts\Activate.ps1` | `venv\Scripts\activate.bat` |
| **Copiar arquivo** | `cp origem destino` | `copy origem destino` | `copy origem destino` |
| **Ver arquivo** | `cat arquivo` | `type arquivo` | `type arquivo` |
| **Listar arquivos** | `ls` | `dir` ou `ls` (alias) | `dir` |
| **Limpar tela** | `clear` | `cls` ou `clear` | `cls` |
| **Caminho** | `/home/user/` | `C:\Users\user\` | `C:\Users\user\` |
| **Barra** | `/` (forward) | `\` (backward) | `\` (backward) |

---

## 🚀 Quick Commands (Copie e Cole)

### Instalação completa (PowerShell):
```powershell
git clone https://github.com/christianlf/infra-health-monitor.git
cd infra-health-monitor
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
copy targets-public.yaml targets.yaml
python main.py check
```

### Teste com Docker (PowerShell):
```powershell
docker-compose -f docker-compose-test.yml up -d
copy targets-docker.yaml targets.yaml
python main.py monitor --interval 10
```

### Análise de resultados:
```powershell
type alerts.log
python main.py report summary
python main.py report csv --output relatorio.csv
start relatorio.csv
```

---

## 📞 Precisa de Ajuda?

Se continuar com problemas no Windows:

1. **Verifique a versão do Python:**
   ```powershell
   python --version
   ```
   Deve ser 3.10 ou superior

2. **Reinstale dependências:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

3. **Use o CMD se PowerShell der problema:**
   ```cmd
   cd infra-health-monitor
   venv\Scripts\activate.bat
   python main.py check
   ```

4. **Desabilite antivírus temporariamente** (pode bloquear Docker/venv)

---

**Christian Lindoso Froz**  
📧 christianlindoso18@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/christian-lindoso-froz)  
🐙 [GitHub](https://github.com/christianlf)

---

**Última atualização:** 2026-09-16
