#!/bin/bash

echo "=========================================="
echo "  Enviando para GitHub"
echo "=========================================="
echo ""
echo "📦 Projeto: infra-health-monitor"
echo "👤 Autor: christian lindoso Froz"
echo "🔗 Destino: github.com/christianlf/infra-health-monitor"
echo ""

# Verifica se está no diretório correto
if [ ! -f "main.py" ]; then
    echo "❌ Erro: Execute este script de dentro do diretório /tmp/infra-health-monitor"
    exit 1
fi

echo "✅ Diretório correto verificado"
echo ""

# Mostra os commits
echo "📝 Commits que serão enviados:"
echo "-------------------------------------------"
git log --oneline --color
echo "-------------------------------------------"
echo ""

# Mostra o autor dos commits
echo "👤 Autor dos commits:"
git log --format="%an <%ae>" | head -1
echo ""

# Pergunta confirmação
read -p "Deseja fazer o push agora? (s/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[SsYy]$ ]]; then
    echo ""
    echo "🚀 Fazendo push para o GitHub..."
    echo ""
    
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "=========================================="
        echo "  ✅ SUCESSO!"
        echo "=========================================="
        echo ""
        echo "🎉 Repositório criado com sucesso!"
        echo ""
        echo "🔗 Acesse em:"
        echo "   https://github.com/christianlf/infra-health-monitor"
        echo ""
        echo "📊 Próximos passos:"
        echo "   1. Acesse o repositório no GitHub"
        echo "   2. Adicione topics: python, monitoring, infrastructure"
        echo "   3. Configure GitHub Actions (opcional)"
        echo ""
    else
        echo ""
        echo "❌ Erro ao fazer push"
        echo ""
        echo "💡 Possíveis soluções:"
        echo "   1. Certifique-se de ter criado o repositório no GitHub"
        echo "   2. Verifique suas credenciais"
        echo "   3. Use um Personal Access Token como senha"
        echo ""
    fi
else
    echo ""
    echo "⏸️  Push cancelado"
    echo ""
    echo "Para fazer push depois, execute:"
    echo "   cd /tmp/infra-health-monitor"
    echo "   git push -u origin main"
    echo ""
fi
