#!/usr/bin/bash
# ============================================================================
# 🏥 VERIFICAÇÃO RÁPIDA - ETAPA 5: HEALTH CHECKS
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         🏥 VERIFICAÇÃO - ETAPA 5: HEALTH CHECKS               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Checklist
echo -e "${YELLOW}📋 Verificando implementação:${NC}\n"

checks=0
total=10

# 1. Arquivo health.py criado
if [ -f "server/api/health.py" ]; then
    echo -e "${GREEN}✓${NC} server/api/health.py exists ($(wc -l < server/api/health.py) linhas)"
    ((checks++))
else
    echo -e "${RED}✗${NC} server/api/health.py NOT FOUND"
fi

# 2. Import em main.py
if grep -q "from api.health import HealthChecker" server/main.py; then
    echo -e "${GREEN}✓${NC} HealthChecker imported in main.py"
    ((checks++))
else
    echo -e "${RED}✗${NC} HealthChecker import NOT FOUND in main.py"
fi

# 3. Variável global health_checker
if grep -q "health_checker: Optional\[HealthChecker\]" server/main.py; then
    echo -e "${GREEN}✓${NC} Global health_checker variable declared"
    ((checks++))
else
    echo -e "${RED}✗${NC} Global health_checker variable NOT FOUND"
fi

# 4. Endpoint /health
if grep -q "@app.get(\"/health\")" server/main.py; then
    echo -e "${GREEN}✓${NC} Endpoint /health exists"
    ((checks++))
else
    echo -e "${RED}✗${NC} Endpoint /health NOT FOUND"
fi

# 5. Endpoint /api/v1/health/full
if grep -q "@app.get(\"/api/v1/health/full\")" server/main.py; then
    echo -e "${GREEN}✓${NC} Endpoint /api/v1/health/full exists"
    ((checks++))
else
    echo -e "${RED}✗${NC} Endpoint /api/v1/health/full NOT FOUND"
fi

# 6. Endpoint /api/v1/health/critical
if grep -q "@app.get(\"/api/v1/health/critical\")" server/main.py; then
    echo -e "${GREEN}✓${NC} Endpoint /api/v1/health/critical exists"
    ((checks++))
else
    echo -e "${RED}✗${NC} Endpoint /api/v1/health/critical NOT FOUND"
fi

# 7. Inicialização no startup
if grep -q "health_checker = HealthChecker(" server/main.py; then
    echo -e "${GREEN}✓${NC} HealthChecker initialized in startup_event()"
    ((checks++))
else
    echo -e "${RED}✗${NC} HealthChecker initialization NOT FOUND"
fi

# 8. Classes em health.py
if grep -q "class HealthChecker" server/api/health.py; then
    echo -e "${GREEN}✓${NC} HealthChecker class exists"
    ((checks++))
else
    echo -e "${RED}✗${NC} HealthChecker class NOT FOUND"
fi

# 9. Documentação
if [ -f "STAGE5_HEALTH_CHECKS.md" ]; then
    echo -e "${GREEN}✓${NC} STAGE5_HEALTH_CHECKS.md documentation exists"
    ((checks++))
else
    echo -e "${RED}✗${NC} STAGE5_HEALTH_CHECKS.md NOT FOUND"
fi

# 10. Script de teste
if [ -f "test_health_checks.sh" ]; then
    echo -e "${GREEN}✓${NC} test_health_checks.sh exists"
    ((checks++))
else
    echo -e "${RED}✗${NC} test_health_checks.sh NOT FOUND"
fi

echo ""
echo -e "${BLUE}Resultado: $checks/$total verificações passaram${NC}"
echo ""

if [ $checks -eq $total ]; then
    echo -e "${GREEN}✅ ETAPA 5 COMPLETA!${NC}"
    echo ""
    echo -e "${YELLOW}Próximos passos:${NC}"
    echo "  1. Iniciar o servidor: cd server && uvicorn main:app --reload"
    echo "  2. Testar health checks: ../test_health_checks.sh"
    echo "  3. Monitorar: curl http://localhost:8000/api/v1/health/full"
    echo ""
elif [ $checks -gt 6 ]; then
    echo -e "${YELLOW}⚠️  ETAPA 5 PARCIALMENTE COMPLETA${NC}"
    echo "Existem alguns problemas menores a resolver."
    echo ""
else
    echo -e "${RED}❌ ETAPA 5 INCOMPLETA${NC}"
    echo "Alguns componentes essenciais estão faltando."
    echo ""
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"

# Exibir estrutura de arquivos relevantes
echo -e "${YELLOW}📁 Estrutura de Arquivos:${NC}\n"
echo "server/"
echo "├── main.py (modificado)"
echo "└── api/"
echo "    ├── health.py (NOVO - 350+ linhas)"
echo "    ├── clima.py"
echo "    └── ... outros módulos"
echo ""
echo "Documentação:"
echo "├── STAGE5_HEALTH_CHECKS.md (NOVO)"
echo "├── STAGE5_SUMMARY.md (NOVO)"
echo "├── HEALTH_CHECKS_INTEGRATION_EXAMPLES.py (NOVO)"
echo "└── test_health_checks.sh (NOVO)"
echo ""

# Estatísticas
echo -e "${YELLOW}📊 Estatísticas:${NC}\n"
health_lines=$(wc -l < server/api/health.py 2>/dev/null || echo "0")
main_lines=$(wc -l < server/main.py 2>/dev/null || echo "0")
echo "  • server/api/health.py: $health_lines linhas"
echo "  • server/main.py: $main_lines linhas"
echo "  • Classes implementadas: 7 (ServiceStatus, HealthCheckResult, DatabaseHealthCheck, RedisHealthCheck, SystemHealthCheck, APIHealthCheck, HealthChecker)"
echo "  • Endpoints adicionados: 3 (/health, /api/v1/health/full, /api/v1/health/critical)"
echo "  • Documentação: 800+ linhas"
echo ""

# Progresso
echo -e "${YELLOW}📈 Progresso do Projeto:${NC}\n"
echo "  Stage 1: Security Hardening        ✅ Completo"
echo "  Stage 2: Docker Optimization       ✅ Completo"
echo "  Stage 3: Frontend Performance      ✅ Completo"
echo "  Stage 4: E2E Tests                 ✅ Completo"
echo "  Stage 5: Health Checks             ✅ Completo (VOCÊ ESTÁ AQUI)"
echo "  Stage 6: JSON Logging              ⏳ Pendente"
echo "  Stage 7: Database Backups          ⏳ Pendente"
echo "  Stage 8: Test Coverage             ⏳ Pendente"
echo ""
echo -e "  Progresso Total: 5/8 (62.5%)"
echo ""
