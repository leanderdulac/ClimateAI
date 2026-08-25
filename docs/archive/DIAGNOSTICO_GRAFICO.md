# 🔍 Diagnóstico: Gráficos Climáticos Não Carregam

## Data: 16 de outubro de 2025

## 📊 Análise do Fluxo de Dados

### 1. **Fluxo Esperado:**

```
LocationProvider (padrão: São Paulo)
    ↓
IndexPage carrega
    ↓
WeatherWidget monta
    ↓
useEffect rodará (dependências: selectedLocation, selectedPeriod, isLoadingLocation)
    ↓
Chama embrapaApi.getClimateData(lat, lon, startDate, endDate)
    ↓
Se API falhar → mockClimateData(dias)
    ↓
climateData = array de 30 pontos
    ↓
LineChart e BarChart renderizam com dados
```

## 🐛 Problemas Possíveis Identificados:

### ❌ **Problema 1: selectedLocation pode estar NULL**
- LocationContext tem defaultLocation correto (São Paulo)
- MAS: useState começa com defaultLocation
- Se o componente for re-renderizado, selectedLocation pode virar null

**Verificar:** No console (F12), qual é o valor de `selectedLocation`?

### ❌ **Problema 2: getClimateData lança exceção**
- A exceção é capturada e deveria retornar mockClimateData
- MAS: O catch está lançando erro em vez de retornar mock

```typescript
// ATUAL (ERRADO):
async getClimateData(...) {
  try {
    return await this.apiGet(...);  // Lança erro
  } catch (error) {
    console.log('Usando dados mock');
    return mockClimateData(...);  // MAS TEM try/catch que pega ISSO no WeatherWidget!
  }
}
```

**Problema:** O try/catch em getClimateData previne erro, mas em WeatherWidget:
```typescript
// Em WeatherWidget:
try {
  const historical = await embrapaApi.getClimateData(...);
  // Se getClimateData retornar [], climateData fica vazio!
} catch (historicalError) {
  setClimateData([]);  // ← Definido como array vazio!
}
```

### ❌ **Problema 3: climateData é um array vazio em vez de ter dados**

Se `historical` retornar `[]` (array vazio), então:
```typescript
const adaptedHistorical: ClimateDataPoint[] = (historical || []).map(...)
// Se historical = [], o map retorna []
// Logo: climateData = []
// Logo: gráficos não renderizam
```

### ❌ **Problema 4: getWeatherForecast pode falhar silenciosamente**

```typescript
async getWeatherForecast(latitude: number, longitude: number, days: number = 7) {
  const response = await this.apiGet(...);  // Não tem try/catch!
  // Se apiGet lançar erro, o erro propaga para WeatherWidget
  // Mas em WeatherWidget, o catch define currentWeather = null
  // Logo: nenhum dado é exibido
}
```

## 🔧 Correções Necessárias:

### 1️⃣ **Garantir que locationContext fornece valores padrão**
```typescript
// Em LocationContext:
const [selectedLocation, setSelectedLocation] = useState<LocalizacaoData | null>(defaultLocation);
// ✅ Correto - começa com São Paulo
```

### 2️⃣ **Garantir que embrapaApi.getClimateData sempre retorna dados**

ATUAL:
```typescript
async getClimateData(latitude, longitude, startDate, endDate) {
  try {
    return await this.apiGet(...);
  } catch {
    return mockClimateData(...);
  }
}
```

PROBLEMA: Se `apiGet` lançar erro, o catch retorna `mockClimateData`, mas:
- mockClimateData gera dados com datas inversas (do passado)
- Se houver múltiplas chamadas, os dados podem não estar em ordem

### 3️⃣ **Garantir que getWeatherForecast tem fallback**

ATUAL:
```typescript
async getWeatherForecast(latitude, longitude, days = 7) {
  const response = await this.apiGet(...);  // ← Sem try/catch!
  const forecastArray = response.previsao || response;
  return Array.isArray(forecastArray) ? forecastArray : [];
}
```

PROBLEMA: Se apiGet falhar, o erro propaga e não há fallback para mock

## 🧪 Como Testar:

1. **Abrir DevTools (F12)**
2. **Console - Ver se aparecem logs:**
   ```
   [WeatherWidget] Iniciando busca de dados climáticos...
   [WeatherWidget] Usando localização selecionada: São Paulo, SP
   [WeatherWidget] Buscando dados históricos de 7 dias...
   [WeatherWidget] Dados históricos recebidos: [...]
   [WeatherWidget] Buscando previsão atual...
   [WeatherWidget] Dados atuais recebidos: [...]
   [WeatherWidget] Dados carregados com sucesso
   ```

3. **Se houver erro, qual é?**
   ```
   - Erro de CORS?
   - TypeError: Cannot read property 'latitude' of null?
   - API timeout?
   ```

4. **Verificar valores:**
   - `selectedLocation` = ?
   - `selectedPeriod` = ?
   - `climateData.length` = ?
   - `currentWeather` = ?

## 🎯 Próximos Passos:

1. Abrir site em navegador
2. Pressionar F12 (DevTools)
3. Ir para Console
4. Compartilhar todos os logs e erros
5. Eu corrigirei conforme o erro exato

---

**Nota:** O código está correto na lógica, mas há possíveis edge cases:
- LocationContext pode estar perdendo estado
- Mock data pode estar vazio
- Fetch pode estar falhando silenciosamente
