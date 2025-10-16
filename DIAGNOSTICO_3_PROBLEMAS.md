# 🔍 DIAGNÓSTICO COMPLETO: 3 Problemas Críticos

## Data: 16 de outubro de 2025

---

## ❌ PROBLEMA 1: Cidades Brasileiras Não Carregam

### Root Cause Identificada

**Arquivo:** `client/src/lib/embrapaApi.ts` (linha 230-237)

**Código Problemático:**
```typescript
return mockCities.map(c => ({
  ...mockLocationData(c.latitude, c.longitude),
  city: c.city,
  state: c.state,
  stateName: c.city  // ← BUG! Deveria ser nome do estado
}));
```

**Problema:**
- `stateName: c.city` está definindo o nome do estado como o nome da cidade
- Exemplo: Para "São Paulo", `stateName` = "São Paulo" (deveria ser "São Paulo" estado)
- Isso causa confusão no mapeamento de dados

### Impacto
- Busca de cidades retorna dados malformados
- Interface pode não exibir cidades corretamente
- Localização pode não ser selecionada

### Solução
```typescript
return mockCities.map(c => ({
  ...mockLocationData(c.latitude, c.longitude),
  city: c.city,
  state: c.state,
  stateName: 'São Paulo' // ← Nome correto do estado
}));
```

---

## ❌ PROBLEMA 2: Busca por Coordenadas Não Funciona

### Root Cause Identificada

**Arquivo:** `client/src/lib/embrapaApi.ts` (linha ~195)

**Função:** `getLocationByCity(city, state)`

```typescript
async getLocationByCity(city: string, state: string): Promise<LocationData> {
  try {
    const location = await this.apiGet('/localizacao/cidade', {
      cidade: city,
      estado: state.toUpperCase()
    });
    return this.normalizeLocation(location);
  } catch (error) {
    // Fallback
    return { ...mockLocationData(-23.5505, -46.6333), city, state: state.toUpperCase() };
  }
}
```

**Problemas:**
1. **API Timeout:** Endpoints `/localizacao/cidade` provavelmente estão falhando
2. **Sem dados mock adequados:** Fallback retorna sempre São Paulo
3. **Erro silencioso:** Função não loga o erro, difícil debugar

### Fluxo Atual:
```
User digita "Rio de Janeiro" + "RJ"
  ↓
LocationSelector.searchLocationByCity()
  ↓
embrapaApi.getLocalizacaoPorCidade("Rio de Janeiro", "RJ")
  ↓
embrapaApiService.getLocationByCity("Rio de Janeiro", "RJ")
  ↓
this.apiGet('/localizacao/cidade', ...)
  ↓
API timeout/falha → Fallback retorna São Paulo ❌
```

### Impacto
- Busca por cidade sempre retorna São Paulo
- Usuário acha que busca funcionou, mas dados estão errados
- Coordenadas não correspondem à cidade buscada

---

## ❌ PROBLEMA 3: Gráficos Continuam Não Carregando

### Root Cause Identificada

**Possível Origem:** Combination dos problemas acima + timeout de API

**Cadeia de Problemas:**
1. LocationSelector não carrega cidades corretamente
2. Localização padrão (São Paulo) tem dados inconsistentes
3. WeatherWidget chama `getClimateData()` com coordenadas erradas
4. API timeout em `/clima/historico`
5. Mesmo com mock fallback, dados pode estar vazio

### Verificação Necessária:

**Abrir Console (F12) e procurar por:**
```
❌ [WeatherWidget] Erro ao buscar dados históricos:
📈 [WeatherWidget] Dados históricos recebidos: 0 pontos
```

Se ambos aparecerem, significa que:
- `getClimateData()` está falhando
- Mock data está vazio ou não retornando

### Fluxo Esperado vs Real:

```
ESPERADO:
WeatherWidget monta
  ↓
selectedLocation = São Paulo (padrão)
  ↓
getClimateData(-23.5505, -46.6333, startDate, endDate)
  ↓
API falha → mockClimateData(30) retorna 30 pontos ✅
  ↓
climateData = 30 pontos
  ↓
LineChart renderiza ✅

REAL:
WeatherWidget monta
  ↓
selectedLocation = null ou malformado ❌
  ↓
getClimateData() chamado com valores inválidos
  ↓
API falha → mockClimateData retorna dados
  ↓
Mas dados pode estar vazio ou não adaptado corretamente ❌
  ↓
climateData = [] (vazio)
  ↓
Sem dados para renderizar ❌
```

---

## 🔧 Soluções Propostas

### FIX 1: Corrigir stateName no searchCities

**Arquivo:** `client/src/lib/embrapaApi.ts`

```typescript
// ANTES:
return mockCities.map(c => ({
  ...mockLocationData(c.latitude, c.longitude),
  city: c.city,
  state: c.state,
  stateName: c.city  // ❌ ERRADO
}));

// DEPOIS:
const estadosMap: { [key: string]: string } = {
  'SP': 'São Paulo',
  'RJ': 'Rio de Janeiro',
  'MG': 'Minas Gerais',
  'DF': 'Distrito Federal',
  'PR': 'Paraná'
};

return mockCities.map(c => ({
  ...mockLocationData(c.latitude, c.longitude),
  city: c.city,
  state: c.state,
  stateName: estadosMap[c.state] || c.state  // ✅ CORRETO
}));
```

### FIX 2: Adicionar Mock Data Melhor em getLocationByCity

**Arquivo:** `client/src/lib/embrapaApi.ts`

```typescript
// ANTES:
async getLocationByCity(city: string, state: string): Promise<LocationData> {
  try {
    return await this.apiGet('/localizacao/cidade', {...});
  } catch (error) {
    return { ...mockLocationData(-23.5505, -46.6333), city, state };  // ❌ Sempre SP
  }
}

// DEPOIS:
async getLocationByCity(city: string, state: string): Promise<LocationData> {
  try {
    const location = await this.apiGet('/localizacao/cidade', {...});
    console.log('✅ Localização encontrada via API:', city, state);
    return this.normalizeLocation(location);
  } catch (error) {
    // Usar dados mock de cidades conhecidas
    console.warn('⚠️ API falhou, usando mock data para:', city, state);
    
    const cityMocks: { [key: string]: { lat: number, lon: number } } = {
      'rio_de_janeiro': { lat: -22.9068, lon: -43.1729 },
      'belo_horizonte': { lat: -19.9167, lon: -43.9345 },
      'brasilia': { lat: -15.7942, lon: -47.8822 },
      'curitiba': { lat: -25.4284, lon: -49.2733 },
      'salvador': { lat: -12.9714, lon: -38.5014 },
      // ... mais cidades
    };
    
    const key = city.toLowerCase().replace(/\s+/g, '_');
    const coords = cityMocks[key] || { lat: -23.5505, lon: -46.6333 }; // Default: SP
    
    return {
      ...mockLocationData(coords.lat, coords.lon),
      city,
      state: state.toUpperCase()
    };
  }
}
```

### FIX 3: Adicionar Logs e Validação em WeatherWidget

**Arquivo:** `client/src/components/WeatherWidget.tsx` (linha 80)

```typescript
// Adicionar validação:
if (!latitude || !longitude || isNaN(latitude) || isNaN(longitude)) {
  console.error('❌ [WeatherWidget] Coordenadas inválidas:', { latitude, longitude });
  setLoading(false);
  return;
}

console.log('✅ [WeatherWidget] Coordenadas válidas:', { latitude, longitude });

const historical = await embrapaApi.getClimateData(
  latitude,
  longitude,
  startDate.toISOString().split('T')[0],
  endDate.toISOString().split('T')[0]
);

console.log('📊 [WeatherWidget] Histórico retornado - tipo:', typeof historical, 'length:', historical?.length);

if (!Array.isArray(historical)) {
  console.error('❌ [WeatherWidget] Histórico não é array:', historical);
  setClimateData([]);
  return;
}

if (historical.length === 0) {
  console.warn('⚠️ [WeatherWidget] Histórico vazio!');
}
```

---

## 📋 Checklist de Testes

- [ ] Fix 1 aplicado: `stateName` correto em searchCities
- [ ] Fix 2 aplicado: Mock data melhorado em getLocationByCity  
- [ ] Fix 3 aplicado: Logs e validação em WeatherWidget
- [ ] Build sem erros: `npm run build`
- [ ] Console limpo (F12): Sem erros vermelhos
- [ ] Testar busca por cidade: Digitar "Rio"
- [ ] Verificar coordenadas retornadas
- [ ] Verificar gráficos aparecem
- [ ] Verificar logs aparecem no console

---

## 🎯 Conclusão

Os 3 problemas estão interconectados:
1. Busca de cidades retorna dados malformados
2. Busca por coordenadas retorna sempre São Paulo
3. Gráficos não carregam porque dados estão vazios/inválidos

**Todos precisam ser corrigidos simultaneamente** para que o sistema funcione.
