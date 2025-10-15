# Correções de Funcionalidade - Deploy Netlify

**Data:** 15 de outubro de 2025  
**Commit:** `592cb59`

## 🎯 Problemas Resolvidos

### 1. Landing Page Não Acessível ✅

**Problema:**
- A landing page (`landing-page.html`) estava apenas na raiz do projeto
- O Netlify só publica o conteúdo de `client/dist/`
- Landing page não foi incluída no build

**Solução:**
- Copiado `landing-page.html` para `client/public/landing.html`
- Vite automaticamente copia arquivos de `public/` para `dist/` no build
- Atualizado todas as URLs de `http://localhost:3000/welcome` para `/welcome`
- Landing page agora acessível em: **`https://seu-site.netlify.app/landing.html`**

### 2. Dados Climáticos Não Carregando ✅

**Problema:**
- Frontend tentava acessar `http://localhost:8000/api/v1`
- Backend não está deployado/acessível
- Chamadas API retornavam erro CORS ou timeout
- Aplicação ficava sem dados

**Solução:**
- Implementado sistema de **fallback com dados mock**
- Quando API não responde (timeout 5s), usa dados sintéticos
- Dados climáticos gerados aleatoriamente mas realistas:
  - Temperatura: 20-30°C
  - Precipitação: 0-20mm
  - Umidade: 60-90%
  - Vento: 5-20 km/h
  - Pressão: 1010-1030 hPa

**Exemplo de código:**
```typescript
async getClimateData(...): Promise<ClimateData[]> {
  try {
    return await this.apiGet('/clima/historico', {...});
  } catch (error) {
    // Fallback para dados mock
    console.log('Usando dados climáticos mock');
    return mockClimateData(days);
  }
}
```

### 3. Busca por Cidades Não Funcionando ✅

**Problema:**
- `searchCities()` dependia 100% do backend
- Sem backend = busca não funcionava
- Usuários não conseguiam selecionar localização

**Solução:**
- Implementado busca mock com 5 cidades principais:
  - São Paulo (SP) - `-23.5505, -46.6333`
  - Rio de Janeiro (RJ) - `-22.9068, -43.1729`
  - Belo Horizonte (MG) - `-19.9167, -43.9345`
  - Brasília (DF) - `-15.7942, -47.8822`
  - Curitiba (PR) - `-25.4284, -49.2733`
- Busca filtra por nome de cidade ou estado
- Funciona mesmo sem backend

## 📋 Mudanças Técnicas

### Arquivos Modificados

1. **`client/public/landing.html`** (NOVO)
   - Landing page copiada da raiz
   - URLs atualizadas para caminhos relativos
   - 61KB, 1709 linhas

2. **`client/src/lib/embrapaApi.ts`** (MODIFICADO)
   - +70 linhas de código mock
   - Timeout de 5s para chamadas API
   - Try/catch com fallback em todas as funções
   - Funções mock: `mockClimateData()`, `mockLocationData()`

3. **`client/.env.production`** (NOVO)
   - Variável `VITE_API_BASE_URL` (vazia por padrão)
   - Preparado para conectar backend futuro

### Build Verificado

```bash
$ npm run build
✓ 3249 modules transformed
✓ built in 1m 59s

Arquivos gerados:
- dist/index.html (0.62 kB)
- dist/landing.html (61 kB) ← NOVO!
- dist/assets/index-DWngfcyB.js (697 kB)
- dist/assets/*.css, *.js
```

## 🚀 Como Acessar

### Landing Page
```
https://seu-site.netlify.app/landing.html
```

### Dashboard
```
https://seu-site.netlify.app/
https://seu-site.netlify.app/welcome
```

### Navegação
- Landing page tem botões "Acessar Dashboard" que levam para `/welcome`
- Dashboard funciona com dados mock (sem backend)
- Todos os componentes carregam normalmente

## 🔄 Próximos Passos (Quando Backend Estiver Pronto)

### 1. Deploy do Backend

Use um dos métodos:
- **DigitalOcean**: Script `deploy/deploy_digitalocean.sh`
- **Render**: Deploy gratuito para FastAPI
- **Fly.io**: Deploy com Docker

### 2. Configurar Variável de Ambiente no Netlify

1. Acesse **Site Settings** → **Build & deploy** → **Environment**
2. Adicione variável:
   ```
   Key: VITE_API_BASE_URL
   Value: https://seu-backend.com/api/v1
   ```
3. Redeploy o site

### 3. Testar Integração

```bash
# No console do navegador, verificar:
# - Se ainda aparece "Usando dados mock" = backend não conectado
# - Se não aparece = backend funcionando!
```

### 4. Atualizar netlify.toml (Opcional)

Se quiser proxy de API no Netlify:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://seu-backend.com/api/:splat"
  status = 200
  force = true
```

## ⚠️ Limitações Atuais (Modo Mock)

- ✅ **Funciona:** Visualização de dados climáticos
- ✅ **Funciona:** Busca por cidades principais
- ✅ **Funciona:** Navegação entre páginas
- ✅ **Funciona:** Interface completa
- ❌ **Não funciona:** Dados climáticos reais
- ❌ **Não funciona:** Todas as cidades do Brasil
- ❌ **Não funciona:** Previsões precisas
- ❌ **Não funciona:** Alertas customizados
- ❌ **Não funciona:** Modelagem atuarial com dados reais

## 📊 Logs de Monitoramento

Quando usar dados mock, o console exibe:

```javascript
// Console do navegador
⚠️ API não disponível, usando dados mock: Network Error
📝 Usando dados climáticos mock
📝 Usando localização mock
📝 Usando busca de cidades mock
```

Quando backend conectar:

```javascript
// Console do navegador
✅ (sem mensagens de mock)
// Requisições HTTP aparecerão na aba Network
```

## ✅ Checklist de Verificação

Após deploy no Netlify:

- [x] Build completou sem erros
- [ ] Landing page acessível em `/landing.html`
- [ ] Dashboard carrega em `/` e `/welcome`
- [ ] Busca de cidades retorna 5 cidades
- [ ] Gráficos de clima exibem dados (mock)
- [ ] Console mostra "Usando dados mock"
- [ ] Sem erros JavaScript no console
- [ ] Navegação entre rotas funciona
- [ ] Botões "Acessar Dashboard" funcionam

---

**Status:** ✅ Pronto para deploy  
**Compatibilidade:** Frontend standalone (sem backend)  
**Preparado para:** Integração futura com backend
