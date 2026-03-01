#!/bin/bash
# ClimateWise - Script de Verificação do Banco de Dados

echo "======================================"
echo "ClimateWise - Verificação do Banco"
echo "======================================"
echo ""

# Verificar se container está rodando
echo "1. Verificando container PostgreSQL..."
podman ps | grep climatewise-db
if [ $? -ne 0 ]; then
    echo "❌ PostgreSQL não está rodando!"
    exit 1
fi
echo "✅ PostgreSQL está rodando"
echo ""

# Verificar banco de dados
echo "2. Verificando banco de dados..."
podman exec climatewise-db psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='climatewise';" 2>&1 | grep climatewise
if [ $? -ne 0 ]; then
    echo "❌ Banco de dados 'climatewise' não encontrado!"
    exit 1
fi
echo "✅ Banco de dados 'climatewise' encontrado"
echo ""

# Verificar tabelas
echo "3. Verificando tabelas..."
TABLES=$(podman exec climatewise-db psql -U postgres -d climatewise -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
echo "   Tabelas encontradas: $TABLES"
if [ "$TABLES" -lt 5 ]; then
    echo "⚠️  Número de tabelas menor que o esperado (5)"
    echo "   Execute: podman exec -i climatewise-db psql -U postgres -d climatewise < server/init-db.sql"
else
    echo "✅ Tabelas verificadas"
fi
echo ""

# Verificar usuários
echo "4. Verificando usuários..."
podman exec climatewise-db psql -U postgres -d climatewise -c "SELECT id, email, full_name, role FROM users;" 2>&1
echo ""

# Testar conexão
echo "5. Testando conexão..."
podman exec climatewise-db psql -U postgres -d climatewise -c "SELECT NOW() as current_time;" 2>&1 | grep current_time
if [ $? -eq 0 ]; then
    echo "✅ Conexão com banco de dados OK"
else
    echo "❌ Erro na conexão com banco de dados"
fi
echo ""

echo "======================================"
echo "Verificação concluída!"
echo "======================================"
echo ""
echo "📋 Credenciais de Teste:"
echo "   Admin: admin@climatewise.com / admin123"
echo "   User:  user@climatewise.com / user123"
echo ""
echo "🔧 Para resetar o banco:"
echo "   podman exec -i climatewise-db psql -U postgres -d climatewise < server/init-db.sql"
echo ""
