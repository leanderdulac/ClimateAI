"""
Brazil Disaster Alerts Service
Integração com múltiplas fontes de alertas de desastres no Brasil

Fontes:
1. CEMADEN - Centro Nacional de Monitoramento e Alertas de Desastres Naturais
2. INMET Alertas (quando disponível)
3. CPTec/INPE - Previsão de tempo severo
4. GeoCAT - Catálogo de dados abertos

CEMADEN API:
- Endpoint: http://geoservicos.cemaden.gov.br/
- Dados abertos: http://www.cemaden.gov.br/dados-abertos/
"""

import logging
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from typing import Dict, List, Optional, Any

from services.cemaden_service import CemadenService

logger = logging.getLogger(__name__)


@dataclass
class BrazilDisasterAlert:
    """Alerta de desastre para Brasil"""
    alert_id: str
    title: str
    disaster_type: str  # Chuva, Seca, Deslizamento, etc
    severity: str  # Baixo, Médio, Alto, Muito Alto
    severity_level: int  # 1-4
    start_time: datetime
    end_time: Optional[datetime]
    state: str  # Estado (UF)
    cities: List[str]  # Cidades afetadas
    description: str
    source: str  # CEMADEN, INMET, etc
    link: Optional[str] = None


class BrazilDisasterAlertService:
    """
    Serviço unificado de alertas de desastres para Brasil
    """
    
    # CEMADEN Endpoints
    CEMADEN_BASE_URL = "http://geoservicos.cemaden.gov.br"
    CEMADEN_ALERTAS_URL = f"{CEMADEN_BASE_URL}/geoserver/cemaden/ows"
    
    # Alternative sources
    INMET_ALERTAS_URL = "https://alertas2.inmet.gov.br/rss"
    CPTEC_URL = "http://servicos.cptec.inpe.br/XML"
    
    def __init__(self):
        """Inicializar serviço"""
        self.cache: List[BrazilDisasterAlert] = []
        self.last_update: Optional[datetime] = None
        self.cemaden_client = CemadenService()
        logger.info("BrazilDisasterAlertService initialized")
    
    def fetch_alerts(
        self,
        use_cache: bool = True,
        cache_timeout_minutes: int = 30,
        sources: List[str] = None
    ) -> List[BrazilDisasterAlert]:
        """
        Buscar alertas de múltiplas fontes
        
        Args:
            use_cache: Usar cache se disponível
            cache_timeout_minutes: Tempo de cache
            sources: Fontes para buscar ['cemaden', 'inmet', 'cptec']
        
        Returns:
            Lista de alertas
        """
        # Verificar cache
        if use_cache and self.cache and self.last_update:
            cache_age = datetime.now() - self.last_update
            if cache_age < timedelta(minutes=cache_timeout_minutes):
                logger.info(f"Using cached alerts ({len(self.cache)} alerts)")
                return self.cache
        
        if sources is None:
            sources = ['cemaden']  # CEMADEN como primária
        
        all_alerts = []
        
        # Buscar de cada fonte
        if 'cemaden' in sources:
            try:
                cemaden_alerts = self._fetch_cemaden_alerts()
                all_alerts.extend(cemaden_alerts)
                logger.info(f"Fetched {len(cemaden_alerts)} alerts from CEMADEN")
            except Exception as e:
                logger.error(f"Error fetching CEMADEN alerts: {e}")
        
        if 'inmet' in sources:
            try:
                inmet_alerts = self._fetch_inmet_alerts_mock()
                all_alerts.extend(inmet_alerts)
                logger.info(f"Fetched {len(inmet_alerts)} alerts from INMET (mock)")
            except Exception as e:
                logger.error(f"Error fetching INMET alerts: {e}")
        
        # Atualizar cache
        self.cache = all_alerts
        self.last_update = datetime.now()
        
        return all_alerts
    
    def _fetch_cemaden_alerts(self) -> List[BrazilDisasterAlert]:
        """
        Buscar alertas do CEMADEN
        
        Primeiro tenta buscar dados processados da REST API (volumes altos de precipitação real).
        Caso a rota REST falhe, realiza o fallback para o serviço de dados abertos WFS.
        """
        alerts = []
        
        # 1. Tentativa via API REST (cemaden_service.py)
        try:
            recent_data = self.cemaden_client.get_dados_recentes()
            if recent_data and isinstance(recent_data, list):
                for data in recent_data:
                    # Acumulados grandes = alerta
                    # Dependendo da resposta do cemaden, a chave pode variar
                    acumulado = data.get("acumulado", data.get("acumulado_24h", 0))
                    try:
                        acumulado = float(acumulado) if acumulado is not None else 0.0
                    except ValueError:
                        acumulado = 0.0
                        
                    if acumulado > 50.0:
                        city = data.get("nome", data.get("municipio", "Local Indefinido"))
                        state = data.get("uf", "BR")
                        
                        intensity = 'Muito Alto' if acumulado > 100 else 'Alto' if acumulado > 70 else 'Médio'
                        severity_level = 4 if intensity == 'Muito Alto' else 3 if intensity == 'Alto' else 2
                        
                        alerts.append(BrazilDisasterAlert(
                            alert_id=f"CEMADEN-REST-{data.get('codestacao', str(hash(city)))}",
                            title=f"Alerta de Chuva - {intensity}",
                            disaster_type='Chuva',
                            severity=intensity,
                            severity_level=severity_level,
                            start_time=datetime.now(),
                            end_time=datetime.now() + timedelta(hours=24),
                            state=state,
                            cities=[city],
                            description=f"Alerta medido de Chuva com intensidade {intensity} para {city} - {state} (Acumulado nas últimas 24h: {acumulado}mm)",
                            source='CEMADEN REST API',
                            link=None
                        ))
                        
                if alerts:
                    logger.info(f"Generated {len(alerts)} alerts mapped from CEMADEN REST precipitation data")
                    return alerts
        except Exception as e:
            logger.error(f"Error generating REST alerts from CEMADEN: {e}")
        
        # 2. Fallback WFS GoServer
        try:
            # CEMADEN dados de alertas de chuva via GeoServer
            url = f"{self.CEMADEN_ALERTAS_URL}?service=WFS&version=1.0.0&request=GetFeature&typeName=cemaden:alerta_municipio&outputFormat=application/json&maxFeatures=100"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse GeoJSON features
                if 'features' in data:
                    for feature in data['features']:
                        alert = self._parse_cemaden_feature(feature)
                        if alert:
                            alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error fetching CEMADEN WFS alerts: {e}")
            # Fallback para dados mock
            alerts = self._get_cemaden_mock_alerts()
        
        return alerts
    
    def _parse_cemaden_feature(self, feature: Dict) -> Optional[BrazilDisasterAlert]:
        """
        Parse feature GeoJSON do CEMADEN
        """
        try:
            props = feature.get('properties', {})
            
            alert_id = props.get('id', str(hash(json.dumps(props))))
            state = props.get('uf', 'Unknown')
            city = props.get('municipio', 'Unknown')
            intensity = props.get('intensidade', 'Médio')
            
            # Mapear intensidade para severidade
            severity_map = {
                'Baixo': ('Baixo', 1),
                'Médio': ('Médio', 2),
                'Alto': ('Alto', 3),
                'Muito Alto': ('Muito Alto', 4)
            }
            severity, severity_level = severity_map.get(intensity, ('Médio', 2))
            
            # Determinar tipo de desastre
            disaster_type = 'Chuva'  # CEMADEN foca em alertas de chuva
            
            return BrazilDisasterAlert(
                alert_id=str(alert_id),
                title=f"Alerta de {disaster_type} - {severity}",
                disaster_type=disaster_type,
                severity=severity,
                severity_level=severity_level,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=24),
                state=state,
                cities=[city],
                description=f"Alerta de {disaster_type} com intensidade {intensity} para {city}/{state}",
                source='CEMADEN',
                link=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing CEMADEN feature: {e}")
            return None
    
    def _get_cemaden_mock_alerts(self) -> List[BrazilDisasterAlert]:
        """
        Dados mock para CEMADEN (fallback)
        """
        return [
            BrazilDisasterAlert(
                alert_id='CEMADEN-001',
                title='Alerta de Chuva - Alto',
                disaster_type='Chuva',
                severity='Alto',
                severity_level=3,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=12),
                state='SP',
                cities=['São Paulo', 'Guarulhos', 'Osasco'],
                description='Alerta de chuva intensa para região metropolitana de São Paulo',
                source='CEMADEN (Mock)'
            ),
            BrazilDisasterAlert(
                alert_id='CEMADEN-002',
                title='Alerta de Chuva - Médio',
                disaster_type='Chuva',
                severity='Médio',
                severity_level=2,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=24),
                state='RJ',
                cities=['Rio de Janeiro', 'Niterói'],
                description='Alerta de chuva para região metropolitana do Rio de Janeiro',
                source='CEMADEN (Mock)'
            ),
            BrazilDisasterAlert(
                alert_id='CEMADEN-003',
                title='Alerta de Deslizamento - Alto',
                disaster_type='Deslizamento',
                severity='Alto',
                severity_level=3,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=6),
                state='RJ',
                cities=['Petrópolis', 'Teresópolis'],
                description='Risco de deslizamentos em áreas de encosta',
                source='CEMADEN (Mock)'
            )
        ]
    
    def _fetch_inmet_alerts_mock(self) -> List[BrazilDisasterAlert]:
        """
        INMET alerts (mock - API indisponível)
        """
        return [
            BrazilDisasterAlert(
                alert_id='INMET-001',
                title='Aviso de Chuvas Intensas. Severidade Grau: Perigo',
                disaster_type='Chuvas Intensas',
                severity='Perigo',
                severity_level=2,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=24),
                state='RS',
                cities=['Porto Alegre', 'Canoas', 'Novo Hamburgo'],
                description='Chuva entre 30 e 60 mm/h ou 50 e 100 mm/dia, ventos intensos (60-100 km/h)',
                source='INMET (Mock)',
                link='https://alertas2.inmet.gov.br/'
            )
        ]
    
    def get_active_alerts(
        self,
        state: str = None,
        city: str = None,
        disaster_type: str = None,
        severity_level: int = None
    ) -> List[BrazilDisasterAlert]:
        """
        Obter alertas ativos com filtros
        
        Args:
            state: Filtrar por estado (UF)
            city: Filtrar por cidade
            disaster_type: Filtrar por tipo de desastre
            severity_level: Filtrar por nível mínimo de severidade
        
        Returns:
            Lista de alertas filtrados
        """
        alerts = self.fetch_alerts()
        
        # Aplicar filtros
        if state:
            alerts = [a for a in alerts if a.state.upper() == state.upper()]
        
        if city:
            alerts = [
                a for a in alerts
                if any(city.lower() in c.lower() for c in a.cities)
            ]
        
        if disaster_type:
            alerts = [
                a for a in alerts
                if a.disaster_type.lower() == disaster_type.lower()
            ]
        
        if severity_level:
            alerts = [a for a in alerts if a.severity_level >= severity_level]
        
        return alerts
    
    def get_alerts_by_state(self) -> Dict[str, List[BrazilDisasterAlert]]:
        """
        Obter alertas agrupados por estado
        
        Returns:
            Dict com estados como chaves
        """
        alerts = self.fetch_alerts()
        
        grouped = {}
        for alert in alerts:
            state = alert.state
            if state not in grouped:
                grouped[state] = []
            grouped[state].append(alert)
        
        return grouped
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """
        Obter resumo dos alertas
        
        Returns:
            Dict com estatísticas
        """
        alerts = self.fetch_alerts()
        
        return {
            'total_alerts': len(alerts),
            'by_state': self._count_by_field(alerts, 'state'),
            'by_disaster_type': self._count_by_field(alerts, 'disaster_type'),
            'by_severity': self._count_by_field(alerts, 'severity'),
            'sources': list(set(a.source for a in alerts)),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
    
    def _count_by_field(self, alerts: List[BrazilDisasterAlert], field: str) -> Dict[str, int]:
        """Contar alertas por campo"""
        counts = {}
        for alert in alerts:
            value = getattr(alert, field, 'Unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status do serviço
        
        Returns:
            Dict com status
        """
        return {
            'service': 'Brazil Disaster Alerts',
            'status': 'active' if self.cache else 'degraded',
            'sources': {
                'cemaden': {
                    'status': 'active',
                    'url': self.CEMADEN_ALERTAS_URL,
                    'data_type': 'Chuva/Deslizamento'
                },
                'inmet': {
                    'status': 'mock',
                    'url': self.INMET_ALERTAS_URL,
                    'data_type': 'Alertas Meteorológicos'
                },
                'cptec': {
                    'status': 'available',
                    'url': self.CPTEC_URL,
                    'data_type': 'Previsão'
                }
            },
            'total_alerts_cached': len(self.cache),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
