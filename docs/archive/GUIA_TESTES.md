# 🧪 Guia de Testes - Verificar Correção dos Gráficos

## ✅ Checklist de Verificação Pós-Deploy

### Fase 1: Verificação Inicial (Imediata)

- [ ] **URL acessível**
  - Abra: `https://seu-site.netlify.app/dashboard`
  - Aguarde 3-5 segundos para carregar
  - ✅ Página deve carregar sem erros

- [ ] **Localização padrão aparece**
  - Deve ver: "São Paulo, SP" no LocationSelector
  - ✅ Se vê, LocalizationContext está funcionando

- [ ] **WeatherWidget renderiza**
  - Deve ter: Card com "Previsão do Tempo"
  - Deve ter: Temperatura, Umidade, Chuva visíveis
  - Deve ter: DOIS gráficos (temperatura + precipitação)
  - ✅ Se todos aparecem, componente está montado

---

### Fase 2: Verificação de Dados (Console)

Abra o console do navegador: **F12** → **Console**

Procure por logs como estes:

```javascript
[WeatherWidget] Iniciando busca de dados climáticos...
[WeatherWidget] Usando localização selecionada: São Paulo, SP
[WeatherWidget] Buscando dados históricos de 7 dias...
[WeatherWidget] Dados históricos recebidos: Array(7)
[WeatherWidget] Buscando previsão atual...
[WeatherWidget] Dados atuais recebidos: Array(1)
[WeatherWidget] Dados carregados com sucesso
```

**Checklist:**
- [ ] Logs `[WeatherWidget]` aparecem?
- [ ] Diz "7 dias" no primeiro carregamento?
- [ ] Mostra "Dados históricos recebidos"?
- [ ] Diz "Dados carregados com sucesso"?
- ❌ Sem erros vermelhos?

**Se vê tudo isso:** ✅ Dados estão carregando corretamente

---

### Fase 3: Testes de Interação

#### Teste 3.1: Verificar Dados no Gráfico de Temperatura

1. Abra o gráfico de temperatura
2. Passe mouse sobre os pontos
3. Deve ver tooltip com:
   - Data (exemplo: "16/10/2025")
   - Temperatura (exemplo: "25.3°C")

**Checklist:**
- [ ] Tooltip aparece ao passar mouse?
- [ ] Mostra data corretamente?
- [ ] Mostra temperatura em °C?

---

#### Teste 3.2: Verificar Dados no Gráfico de Precipitação

1. Abra o gráfico de precipitação
2. Passe mouse sobre as barras
3. Deve ver tooltip com:
   - Data (exemplo: "16/10/2025")
   - Precipitação (exemplo: "5.2mm")

**Checklist:**
- [ ] Tooltip aparece ao passar mouse?
- [ ] Mostra data corretamente?
- [ ] Mostra precipitação em mm?

---

#### Teste 3.3: Mudar Período - 7D → 30D

1. Localize os botões de período (7D, 30D, 90D) acima dos gráficos
2. Clique em "30D"
3. Observe:
   - Botão 30D fica em destaque (azul)
   - Gráficos atualizam
   - Mais pontos aparecem nos gráficos
   - Console mostra: `[WeatherWidget] Buscando dados históricos de 30 dias...`

**Checklist:**
- [ ] Botão 30D ficou destacado?
- [ ] Gráfico de temperatura tem mais pontos?
- [ ] Gráfico de precipitação tem mais barras?
- [ ] Log console diz "30 dias"?
- [ ] Sem erros vermelhos?

**Se tudo passou:** ✅ Período 7D → 30D funciona!

---

#### Teste 3.4: Mudar Período - 30D → 90D

1. Clique em "90D"
2. Observe:
   - Botão 90D fica em destaque
   - Gráficos atualizam NOVAMENTE
   - Ainda mais pontos aparecem
   - Console mostra: `[WeatherWidget] Buscando dados históricos de 90 dias...`

**Checklist:**
- [ ] Botão 90D ficou destacado?
- [ ] Gráfico tem ainda mais pontos?
- [ ] Log console diz "90 dias"?
- [ ] Pontos estão mais próximos (comprimidos)?
- [ ] Sem erros vermelhos?

**Se tudo passou:** ✅ Período 30D → 90D funciona!

---

#### Teste 3.5: Voltar para 7D

1. Clique em "7D"
2. Observe:
   - Gráficos voltam ao estado original
   - Menos pontos novamente
   - Escala muda

**Checklist:**
- [ ] Voltou para 7 pontos?
- [ ] Gráficos se comportam como antes?

**Se passou:** ✅ Ciclo completo funciona!

---

### Fase 4: Testes de Responsividade

#### Teste 4.1: Desktop (Sua resolução atual)
- [ ] Gráficos aparecem lado a lado?
- [ ] Legendas visíveis?
- [ ] Botões de período acessíveis?

#### Teste 4.2: Tablet (1024px)
```bash
F12 → Ctrl+Shift+M → Selecionar "iPad"
```
- [ ] Gráficos responsivos?
- [ ] Botões ainda acessíveis?

#### Teste 4.3: Mobile (375px)
```bash
F12 → Ctrl+Shift+M → Selecionar "iPhone 12"
```
- [ ] Gráficos empilhados verticalmente?
- [ ] Botões acessíveis?
- [ ] Sem overflow horizontal?

---

### Fase 5: Testes de Performance

1. Abra DevTools: **F12** → **Performance**
2. Clique em record (círculo vermelho)
3. Mude entre períodos: 7D → 30D → 90D → 7D
4. Clique stop
5. Analise:

**Checklist:**
- [ ] Transições suaves (sem travadas)?
- [ ] Menos de 100ms por mudança de período?
- [ ] Sem memory leaks (memória não crescendo)?

---

### Fase 6: Testes de Erro (Esperados Falhem)

Estes testes devem **falhar** corretamente:

#### Teste 6.1: Abrir DevTools → Network
1. F12 → **Network**
2. Recarregue a página (F5)
3. Mude entre períodos
4. Observe as requisições:

```
GET /api/v1/clima/historico?latitude=...&longitude=...&data_inicio=...&data_fim=...
```

**Se API está DOWN:**
- [ ] Ainda funciona (com dados mock)?
- [ ] Console diz "Usando dados climáticos mock"?
- [ ] Gráficos aparecem com dados simulados?

**Se API está UP:**
- [ ] Requisição retorna status 200?
- [ ] Dados aparecem nos gráficos?

---

### Fase 7: Teste de Cache

1. Carregue a página normalmente
2. F12 → **Application** → **Cache Storage**
3. Recarregue sem conexão (DevTools → Network → "Offline")
4. Observe:
   - [ ] Página ainda funciona?
   - [ ] Dados estão no cache?

---

## 📋 Matriz de Testes Esperados

| Teste | Esperado | Status |
|-------|----------|--------|
| Página carrega | ✅ Sem erros | ☐ |
| Localização mostra | ✅ São Paulo, SP | ☐ |
| Gráfico temperatura | ✅ Com dados | ☐ |
| Gráfico precipitação | ✅ Com dados | ☐ |
| 7D carrega | ✅ 7 pontos | ☐ |
| 30D carrega | ✅ 30 pontos | ☐ |
| 90D carrega | ✅ 90 pontos | ☐ |
| Transição suave | ✅ Sem lag | ☐ |
| Console sem erros | ✅ Só logs | ☐ |
| Mobile responsivo | ✅ Funciona | ☐ |
| Modo offline | ✅ Dados mock | ☐ |

---

## 🔍 Troubleshooting

### Problema: Gráficos ainda vazios

**Solução 1: Limpar cache**
```
Ctrl+Shift+Del → Selecionar "Cached images and files"
```

**Solução 2: Aba anônima**
```
Ctrl+Shift+N e acessar site de novo
```

**Solução 3: Hard refresh**
```
Ctrl+F5 (Windows) ou Cmd+Shift+R (Mac)
```

### Problema: Erros no console

**Se vê:** `TypeError: Cannot read property 'map' of undefined`
- Dados históricos estão nulos
- Backend pode estar offline
- Verificar se `climateData` está sendo setado

**Se vê:** `TypeError: selectedPeriod is undefined`
- `usePeriod()` não está retornando valor
- Verifique se PeriodProvider envolve o componente

**Se vê:** `CORS error`
- Backend não está respondendo
- Usar dados mock (automático)
- Verificar VITE_API_BASE_URL

### Problema: Período não muda

**Causa provável:** Botões não estão sendo clicados
- F12 → **Elements**
- Procure por: `<button>30D</button>`
- Verifique se tem classe `.button`
- Teste clicar com console:
  ```javascript
  document.querySelector('button').click();
  ```

### Problema: Performance ruim

**Se gráfico trava ao mudar período:**
- Dados muito grandes (90 dias com muitos pontos)
- Renderização Recharts muito pesada
- Solução: Limitar pontos a cada 3 dias

---

## ✅ Resultado Final Esperado

Quando TUDO funcionar:

```
Dashboard
├─ Localização: São Paulo, SP ✓
├─ Temperatura (7D)
│  └─ 7 pontos, gráfico linha suave ✓
├─ Precipitação (7D)
│  └─ 7 barras, valores visíveis ✓
├─ Período buttons
│  ├─ 7D: Destacado (azul) ✓
│  ├─ 30D: Cinza (clicável) ✓
│  └─ 90D: Cinza (clicável) ✓
│
└─ Ao clicar 30D:
   ├─ Temperatura: 30 pontos ✓
   ├─ Precipitação: 30 barras ✓
   ├─ 30D: Destacado (azul) ✓
   └─ Log: "Buscando dados de 30 dias..." ✓
```

---

## 📞 Reportar Problemas

Se algo não funcionar:

1. **Screenshot do problema**
2. **Console output (F12)**
3. **URL que estava acessando**
4. **Dispositivo/Browser**
5. **Passos para reproduzir**

Exemplo:
```
Problema: Gráfico fica em branco ao clicar 30D
Screenshot: [anexo]
Console: TypeError: Cannot read property 'map' of undefined
URL: https://site.netlify.app/dashboard
Browser: Chrome 120 no Windows 11
Passos: 1. Carrega página 2. Clica 30D 3. Gráfico fica branco
```

---

**Teste Data:** 16 de Outubro de 2025
**Versão:** 1.0
**Commit:** 62b0914
