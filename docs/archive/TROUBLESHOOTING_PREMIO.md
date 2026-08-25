# 🔧 Troubleshooting - Cálculo de Prêmio

## Problema Relatado
Botão "Calculate Premium" não está funcionando e nenhum cálculo está sendo gerado.

## Soluções Implementadas

### 1. ✅ Logs de Debug Adicionados
Adicionados logs detalhados no console do navegador para facilitar o diagnóstico:
- `[PricingSimulator]` - Prefixo para todos os logs
- Log de parâmetros de entrada
- Log de requisições API
- Log de respostas da API
- Log de erros detalhados

### 2. ✅ Validação Melhorada
- Removida validação bloqueante de evento climático
- Valores padrão usados se nenhum evento for selecionado
- Mensagens de erro mais claras e informativas

### 3. ✅ Tratamento de Erros Aprimorado
- Mensagens de erro detalhadas
- Dicas de troubleshooting incluídas
- Melhor identificação de problemas de rede

## Como Diagnosticar

### No Navegador (F12 → Console)

1. **Abra o console do navegador** (F12)
2. **Clique em "Calculate Premium"**
3. **Verifique os logs**:

```
[PricingSimulator] Iniciando cálculo...
[PricingSimulator] assetValue: 100000
[PricingSimulator] selectedEvent: {...}
[PricingSimulator] frequency: 10
[PricingSimulator] severity: 10000
[PricingSimulator] selectedLocation: {...}
[PricingSimulator] Enviando requisição para API...
[PricingSimulator] Request: {...}
[PricingSimulator] Resultado da API: {...}
[PricingSimulator] Cálculo concluído com sucesso!
```

### Verificações Manuais

#### 1. Backend está rodando?
```bash
curl http://localhost:8000/health
```

**Resposta esperada**:
```json
{"status": "healthy", ...}
```

#### 2. Endpoint de pricing está acessível?
```bash
curl -X POST http://localhost:8000/api/v1/policy-pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "asset_value": 100000,
    "severity_amount": 10000,
    "frequency_pct": 10,
    "coverage_period_years": 1,
    "scr_score": 450,
    "is_manual_underwriting": false
  }'
```

**Resposta esperada**:
```json
{
  "is_approved": true,
  "status": "APPROVED",
  "financials": {
    "total_premium": 39333.7,
    ...
  }
}
```

#### 3. Frontend está configurado corretamente?

Verifique o arquivo `client/.env`:
```bash
cat client/.env
```

**Deve conter**:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_DATA=false
```

#### 4. Frontend foi rebuild após mudanças?

Se modificou arquivos do frontend, precisa rebuild:
```bash
cd client
npm run build
```

Ou em desenvolvimento:
```bash
cd client
npm run dev
```

## Erros Comuns e Soluções

### Erro: "Failed to fetch"
**Causa**: Backend não está rodando ou URL incorreta

**Solução**:
```bash
# Inicie o backend
cd server
python -m uvicorn main:app --reload
```

### Erro: "404 Not Found"
**Causa**: Endpoint não existe ou URL errada

**Solução**:
1. Verifique se `VITE_API_BASE_URL` está correto
2. Verifique se endpoint está registrado em `server/main.py`

### Erro: "CORS error"
**Causa**: CORS não configurado corretamente

**Solução**:
```bash
# Edite server/.env
ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Erro: "assetValue <= 0"
**Causa**: Valor do bem não preenchido

**Solução**: Preencha o valor do bem (padrão: R$ 100.000)

### Erro: "Nenhum evento selecionado"
**Causa**: Nenhum evento climático selecionado

**Solução**: 
- Selecione um evento climático (Seca, Inundação, etc.)
- **OU** use valores padrão (agora automático)

## Teste Rápido

### Script de Teste

```bash
# Teste o backend diretamente
cd /home/exp/Downloads/ClimateAI

# Teste health check
curl http://localhost:8000/health

# Teste endpoint de pricing
curl -X POST http://localhost:8000/api/v1/policy-pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "asset_value": 100000,
    "severity_amount": 10000,
    "frequency_pct": 10,
    "coverage_period_years": 1,
    "scr_score": 450,
    "is_manual_underwriting": false,
    "latitude": -23.55,
    "longitude": -46.63
  }' | jq
```

## Fluxo de Funcionamento

1. **Usuário clica em "Calculate Premium"**
2. **Frontend valida dados**:
   - `assetValue > 0` ✓
   - Usa valores padrão se necessário ✓
3. **Frontend envia requisição**:
   - `POST /api/v1/policy-pricing/calculate`
   - Body: `{asset_value, severity_amount, frequency_pct, ...}`
4. **Backend processa**:
   - Busca dados climáticos (OpenMeteo)
   - Calcula com Extreme Value Theory
   - Retorna resultado
5. **Frontend exibe resultado**:
   - Prêmio total
   - Decomposição de custos
   - Análise financeira

## Arquivos Modificados

- `client/src/components/PricingSimulator.tsx` - Logs e tratamento de erros
- `client/.env` - Configuração de ambiente
- `client/.env.example` - Template atualizado

## Próximos Passos

Se após todas as verificações o problema persistir:

1. **Reinicie o frontend**:
   ```bash
   cd client
   rm -rf node_modules/.vite
   npm run dev
   ```

2. **Limpe cache do navegador**:
   - Ctrl+Shift+Delete
   - Limpar cache e cookies

3. **Verifique versão do Node**:
   ```bash
   node --version  # Deve ser 18+
   ```

4. **Reinstale dependências**:
   ```bash
   cd client
   rm -rf node_modules package-lock.json
   npm install
   ```

## Contate Suporte

Se nada funcionar, abra uma issue no GitHub com:
- Logs do console (F12)
- Resposta do `curl` para o endpoint
- Versões: Node, npm, Python
- Sistema operacional

---

**Última atualização**: Fevereiro 2026  
**Status**: ✅ Corrigido
