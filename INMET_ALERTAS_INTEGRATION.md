# ✅ Integração INMET Alertas RSS

**Data**: Fevereiro 2026  
**Status**: ✅ **IMPLEMENTADO**  
**Fonte**: INMET Alertas RSS Feed

---

## 📡 **FONTES DE DADOS**

### **Feed RSS Principal**
```
URL: https://alertas2.inmet.gov.br/rss
Status: ⚠️ Intermitente (pode estar indisponível)
Atualização: Tempo real (quando disponível)
```

### **Feed RSS Alternativo**
```
URL: https://apiprevmet3.inmet.gov.br/avisos/rss
Status: ⚠️ Backup
```

---

## ⚠️ **STATUS ATUAL**

**Problema Identificado**:
- Feed RSS do INMET está frequentemente indisponível
- Retorno: Vazio ou timeout
- Causa: Instabilidade na infraestrutura do INMET

**Solução Implementada**:
- ✅ Cache de alertas (15 minutos)
- ✅ Fallback para URL alternativa
- ✅ Dados mock para desenvolvimento
- ✅ Tratamento de erro robusto

---

## 📋 **TIPOS DE ALERTAS**

| Tipo | Descrição | Severidade Típica |
|------|-----------|-------------------|
| **Chuvas Intensas** | Chuva 20-60mm/h ou 50-100mm/dia | Perigo Potencial - Perigo |
| **Baixa Umidade** | Umidade relativa 20-30% | Perigo Potencial |
| **Tempestade** | Chuva + vento + granizo | Perigo Potencial - Grande Perigo |
| **Ventos Costeiros** | Ventos intensos no litoral | Perigo Potencial |
| **Declínio de Temperatura** | Queda de 3-5°C | Perigo Potencial |
| **Acumulado de Chuva** | Chuva acumulada significativa | Perigo Potencial - Grande Perigo |

---

## 🚨 **NÍVEIS DE SEVERIDADE**

| Nível | Severidade | Cor | Descrição |
|-------|------------|-----|-----------|
| **1** | Perigo Potencial | 🟡 Amarelo | Baixo risco de danos |
| **2** | Perigo | 🟠 Laranja | Risco moderado de danos |
| **3** | Grande Perigo | 🔴 Vermelho | Alto risco de danos significativos |

---

## 🔧 **COMO USAR**

### **1. Buscar Todos os Alertas**
```python
from services.inmet_alertas_service import INMETAlertService

service = INMETAlertService()

# Buscar alertas (usa cache se disponível)
alerts = service.fetch_alerts()

for alert in alerts:
    print(f"{alert.event_type}: {alert.severity}")
    print(f"  Áreas: {', '.join(alert.affected_areas)}")
    print(f"  Período: {alert.start_time} até {alert.end_time}")
```

### **2. Buscar Alertas Ativos**
```python
# Alertas ativos agora
active = service.get_active_alerts()

# Filtrar por tipo
chuvas = service.get_active_alerts(event_type='Chuvas Intensas')

# Filtrar por severidade mínima (2 = Perigo ou superior)
graves = service.get_active_alerts(severity_level=2)

# Filtrar por localização
sp_alerts = service.get_active_alerts(location='São Paulo')
```

### **3. Obter Resumo**
```python
summary = service.get_alerts_summary()

print(f"Total de alertas: {summary['total_alerts']}")
print(f"Alertas ativos: {summary['active_alerts']}")
print(f"Por severidade: {summary['by_severity']}")
print(f"Por tipo: {summary['by_event_type']}")
```

---

## 🌐 **API ENDPOINTS**

### **GET /api/v1/inmet-alertas/fetch**
```bash
# Buscar todos os alertas
curl http://localhost:8000/api/v1/inmet-alertas/fetch

# Com cache
curl "http://localhost:8000/api/v1/inmet-alertas/fetch?use_cache=true&cache_timeout_minutes=30"
```

### **GET /api/v1/inmet-alertas/active**
```bash
# Alertas ativos
curl http://localhost:8000/api/v1/inmet-alertas/active

# Filtrar por tipo
curl "http://localhost:8000/api/v1/inmet-alertas/active?event_type=Chuvas%20Intensas"

# Filtrar por severidade
curl "http://localhost:8000/api/v1/inmet-alertas/active?severity_level=2"

# Filtrar por localização
curl "http://localhost:8000/api/v1/inmet-alertas/active?location=São%20Paulo"
```

### **GET /api/v1/inmet-alertas/summary**
```bash
# Resumo dos alertas
curl http://localhost:8000/api/v1/inmet-alertas/summary
```

### **GET /api/v1/inmet-alertas/by-severity**
```bash
# Alertas por severidade
curl http://localhost:8000/api/v1/inmet-alertas/by-severity
```

### **GET /api/v1/inmet-alertas/status**
```bash
# Status do serviço
curl http://localhost:8000/api/v1/inmet-alertas/status
```

---

## 📊 **EXEMPLO DE RESPOSTA**

### **Alert Response**
```json
{
  "alert_id": "53326",
  "title": "Aviso de Chuvas Intensas. Severidade Grau: Perigo Potencial",
  "event_type": "Chuvas Intensas",
  "severity": "Perigo Potencial",
  "severity_level": 1,
  "start_time": "2026-02-16T09:00:00",
  "end_time": "2026-02-17T23:59:00",
  "description": "INMET publica aviso iniciando em: 16/02/2026 09:00. Chuva entre 20 e 30 mm/h ou até 50 mm/dia, ventos intensos (40-60 km/h).",
  "affected_areas": [
    "Centro Goiano",
    "Leste Goiano",
    "Nordeste Paraense"
  ],
  "link": "https://alertas2.inmet.gov.br/53326",
  "published": "2026-02-16T09:00:00",
  "source": "INMET"
}
```

### **Summary Response**
```json
{
  "total_alerts": 30,
  "active_alerts": 15,
  "by_severity": {
    "Perigo Potencial": 10,
    "Perigo": 4,
    "Grande Perigo": 1
  },
  "by_event_type": {
    "Chuvas Intensas": 12,
    "Tempestade": 2,
    "Baixa Umidade": 1
  },
  "last_update": "2026-02-16T10:30:00"
}
```

---

## ⚠️ **TRATAMENTO DE ERROS**

### **Feed Indisponível**
```python
# Serviço retorna cache mesmo se expirado
alerts = service.fetch_alerts()

if not alerts:
    print("Alertas indisponíveis no momento")
    # Fallback: usar dados históricos ou mock
```

### **Timeout**
```python
# Timeout de 10 segundos
try:
    alerts = service.fetch_alerts(use_cache=False)
except Exception as e:
    print(f"Erro ao buscar alertas: {e}")
    alerts = service.cache  # Usar cache
```

---

## 🔄 **INTEGRAÇÃO COM CLIMATEAI**

### **ClimateDataWidget**
```typescript
// client/src/components/ClimateDataWidget.tsx

// Buscar alertas ativos
const fetchAlerts = async () => {
  const response = await fetch(
    'http://localhost:8000/api/v1/inmet-alertas/active'
  );
  const alerts = await response.json();
  
  // Exibir alertas no widget
  if (alerts.length > 0) {
    setWeatherAlerts(alerts);
  }
};
```

### **InsuranceRecommendation**
```python
# server/services/insurance_recommendation.py

# Verificar alertas antes de recomendar seguro
alerts = alertas_service.get_active_alerts(
    location=policy.location,
    severity_level=2  # Perigo ou superior
)

if alerts:
    # Ajustar recomendação baseada em alertas
    recommendation.risk_level = 'HIGH'
    recommendation.premium_adjustment = 1.2  # +20%
```

---

## 📝 **DEPENDÊNCIAS**

```bash
# Instalar dependências
pip install feedparser beautifulsoup4 lxml

# Ou via requirements.txt
feedparser>=6.0.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

---

## 🚀 **PRÓXIMOS PASSOS**

### **Curto Prazo**
1. ✅ **Monitorar disponibilidade do feed** - Implementar health check
2. ✅ **Dados mock para desenvolvimento** - Fallback quando indisponível
3. ⏳ **Cache de longo prazo** - Redis para alertas

### **Médio Prazo**
4. ⏳ **Webhook de atualizações** - Push notifications
5. ⏳ **Integração com SMS/Email** - Alertas para usuários
6. ⏳ **Dashboard de monitoramento** - Visualização de alertas

### **Longo Prazo**
7. ⏳ **API própria de alertas** - Não depender do INMET
8. ⏳ **Machine Learning** - Predição de alertas
9. ⏳ **Integração com Defesa Civil** - Alertas oficiais

---

## 📞 **SUPORTE**

### **INMET**
- Site: https://portal.inmet.gov.br/
- Alertas: https://alertas2.inmet.gov.br/
- API: https://apiprevmet3.inmet.gov.br/

### **ClimateAI Team**
- GitHub: https://github.com/leanderdulac/ClimateAI
- Issues: https://github.com/leanderdulac/ClimateAI/issues

---

**Status**: ✅ **IMPLEMENTADO**  
**Disponibilidade**: ⚠️ **Depende do INMET**  
**Recomendação**: Usar cache + fallback mock  
**Próxima Revisão**: Março 2026
