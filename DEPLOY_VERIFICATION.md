# Guia de Verificação - Deploy Netlify

**Data:** 15 de outubro de 2025
**Commit:** `2ca69f5`

## 🔍 Como Verificar se Está Funcionando

### 1. Landing Page (Página Inicial)

**Acesse:** `https://seu-site.netlify.app/`

**Deve mostrar:**
- ✅ Página HTML completa com design azul/roxo
- ✅ Botão "Acessar Dashboard"
- ✅ Seções sobre ClimateAI
- ✅ **SEM erro 404**

### 2. Dashboard

**Acesse:** `https://seu-site.netlify.app/welcome`

**Deve mostrar:**
- ✅ **Banner amarelo** no topo: "⚠️ Modo Demo"
- ✅ Interface completa
- ✅ Campos de busca funcionais
- ✅ **SEM tela branca**

### 3. Busca de Cidades

1. Digite "São" no campo de busca
2. **Deve retornar:** São Paulo, Rio de Janeiro, Belo Horizonte, Brasília, Curitiba
3. Selecione uma cidade

### 4. Dados Climáticos

Após selecionar cidade:
- ✅ Gráficos carregam (2-5 segundos)
- ✅ Mostra temperatura, umidade, precipitação
- ✅ Valores realistas (não zeros)

### 5. Console do Navegador (F12)

**Mensagens esperadas (NORMAIS):**
```
Usando dados climáticos mock
Usando localização mock
Usando busca de cidades mock
```

**NÃO deve ter:**
```
Cannot find module ❌
Uncaught Error ❌
Failed to load ❌
```

## 🐛 Se Não Funcionar

### Landing page 404
- Limpar cache: Ctrl+Shift+R
- Modo anônimo do navegador
- Aguardar 5min após deploy

### Dashboard tela branca
1. F12 → Console → ver erros
2. Recarregar (F5)
3. Tentar `/index.html` diretamente

### Dados não carregam
1. Verificar se selecionou cidade
2. Ver console: deve ter "usando dados mock"
3. Aguardar até 10 segundos

## ✅ Resultado Esperado

Se tudo estiver certo:
- Landing page carrega
- Dashboard mostra banner amarelo
- Busca retorna 5 cidades
- Gráficos mostram dados
- Console tem mensagens "mock"

---

**Me informe:** O que você vê ao acessar o site?
