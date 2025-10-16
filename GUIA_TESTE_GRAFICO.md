# 🚀 GUIA RÁPIDO: Testar Gráficos Climáticos

## ⚡ 5 Minutos de Ação

### 1️⃣ Aguardar Deploy (3 min)
- Netlify está construindo automaticamente
- Você receberá notificação quando pronto

### 2️⃣ Abrir Site
```
https://seu-site.netlify.app/
```

### 3️⃣ Navegar para Dashboard
- Clique em "**Explorar Dashboard**"
- Ou acesse diretamente: `https://seu-site.netlify.app/dashboard`

### 4️⃣ Abrir Console (F12)
```
F12 → Console
```

### 5️⃣ Ver Logs
Procure por mensagens com emoji:
```
🌤️ [WeatherWidget] Iniciando busca...
✅ [WeatherWidget] Usando localização: São Paulo, SP
✅ [WeatherWidget] Dados carregados com sucesso
```

---

## ✅ Sucesso = Você Deve Ver

**Na Página:**
- ✅ "São Paulo, SP" no selector de localização
- ✅ Gráfico com linha verde (temperatura)
- ✅ Gráfico com barras azuis (precipitação)
- ✅ Cards com: Temperatura | Chuva | Vento

**No Console:**
- ✅ Logs com emojis 🌤️ ✅
- ✅ "Dados climáticos mock" (normal, API não está deployada)
- ✅ Nenhum erro vermelho

---

## ❌ Problema = Procure Por

**Na Página:**
- ❌ Sem gráficos visíveis
- ❌ Cards vazios
- ❌ Spinner girando infinitamente

**No Console:**
- ❌ Mensagens com ❌ (vermelho)
- ❌ Erros como:
  - `Cannot read property 'latitude' of null`
  - `API timeout`
  - `CORS error`

---

## 🔧 Se Houver Problema

### Passo 1: Limpar Cache
```
Chrome: Ctrl+Shift+Del → Limpar Cache
Ou: Abrir em aba Incógnita (Ctrl+Shift+N)
```

### Passo 2: Recarregar
```
F5 ou Ctrl+R
```

### Passo 3: Capturar Informações
1. Abrir Console (F12)
2. Copiar TODOS os logs (especialmente os vermelhos)
3. Fazer screenshot da página

### Passo 4: Compartilhar Comigo
- Screenshot da página (vazia ou com dados?)
- Cópia dos logs do console
- URL que está acessando

---

## 📊 Testar Funcionalidades Extras

### Testar Períodos
```
Na página do dashboard:
1. Clicar botão "7D" (7 dias)
   → Gráfico deve atualizar com 7 pontos
2. Clicar botão "30D" (30 dias)
   → Gráfico deve atualizar com 30 pontos
3. Clicar botão "90D" (90 dias)
   → Gráfico deve atualizar com ~90 pontos
```

### Testar Outras Cidades
```
Na página do dashboard:
1. No LocationSelector (onde diz "São Paulo, SP"):
   - Começar digitar "Rio"
   - Selecionar "Rio de Janeiro"
   → Todos os gráficos devem atualizar com dados do Rio
```

---

## 📱 Verificação Completa (Checklist)

- [ ] Site carrega (`https://seu-site.netlify.app/`)
- [ ] WelcomePage mostra "Explorar Dashboard"
- [ ] Botão clicável e navega para `/dashboard`
- [ ] Dashboard carrega
- [ ] "São Paulo, SP" visível no LocationSelector
- [ ] Gráfico de temperatura visível (linha verde)
- [ ] Gráfico de precipitação visível (barras azuis)
- [ ] Cards mostram: Temp | Chuva | Vento
- [ ] Console mostra logs com 🌤️ e ✅
- [ ] Nenhum erro vermelho no console
- [ ] Clicar "7D" atualiza gráfico
- [ ] Clicar "30D" atualiza gráfico
- [ ] Clicar "90D" atualiza gráfico
- [ ] Buscar "Rio" e selecionar funciona
- [ ] Gráficos atualizam para Rio

---

## 🆘 Comando de Diagnóstico

Se quiser informações detalhadas, abrir Console e colar:

```javascript
console.log('=== DIAGNÓSTICO ===');
console.log('URL:', window.location.href);
console.log('Timestamp:', new Date().toISOString());
console.log('Browser:', navigator.userAgent);
```

---

## 📞 Informação Essencial para Reporte

Se problema persistir, preciso de:

1. **Screenshot** da página (está vazia ou mostra dados?)
2. **URL** que está acessando
3. **Logs completos** do console (F12 → Console → Select All → Copy)
4. **Erro específico** (se houver em vermelho)
5. **Qual dispositivo/navegador** está usando

---

**Tempo Esperado de Teste:** 5 minutos
**Tempo de Ação se Erro:** 2 minutos (capturar infos)
**Tempo de Diagnóstico:** 5-10 minutos (meu lado)

---

🎯 **OBJETIVO:** Gráficos carregando com dados do últimos 7/30/90 dias  
✅ **ESPERADO:** Línea verde (temperatura) + Barras azuis (precipitação)  
⏱️ **TIMING:** Deploy agora, testes em 3-5 min
