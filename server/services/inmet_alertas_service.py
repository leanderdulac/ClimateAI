"""
INMET Alertas RSS Service
Integração com feed RSS de alertas meteorológicos do INMET

URL do Feed RSS:
https://alertas2.inmet.gov.br/rss

Tipos de Alertas:
- Chuvas Intensas
- Baixa Umidade
- Ventos Costeiros
- Tempestade
- Declínio de Temperatura
- Acumulado de Chuva

Severidade:
- Perigo Potencial (Amarelo)
- Perigo (Laranja)
- Grande Perigo (Vermelho)
"""

import logging
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


@dataclass
class INMETAlert:
    """Alerta do INMET"""
    alert_id: str
    title: str
    event_type: str  # Chuvas Intensas, Baixa Umidade, etc
    severity: str  # Perigo Potencial, Perigo, Grande Perigo
    severity_level: int  # 1=Perigo Potencial, 2=Perigo, 3=Grande Perigo
    start_time: datetime
    end_time: datetime
    description: str
    affected_areas: List[str]
    link: str
    published: datetime
    source: str = "INMET"


class INMETAlertService:
    """
    Serviço de integração com alertas RSS do INMET
    """
    
    # RSS Feed URLs
    RSS_FEED_URL = "https://alertas2.inmet.gov.br/rss"
    RSS_FEED_URL_ALT = "https://apiprevmet3.inmet.gov.br/avisos/rss"
    
    def __init__(self):
        """Inicializar serviço de alertas"""
        self.cache: List[INMETAlert] = []
        self.last_update: Optional[datetime] = None
        logger.info("INMETAlertService initialized")
    
    def fetch_alerts(self, use_cache: bool = True, cache_timeout_minutes: int = 15) -> List[INMETAlert]:
        """
        Buscar alertas do feed RSS
        
        Args:
            use_cache: Usar cache se disponível
            cache_timeout_minutes: Tempo de cache em minutos
        
        Returns:
            Lista de alertas
        """
        # Verificar cache
        if use_cache and self.cache and self.last_update:
            cache_age = datetime.now() - self.last_update
            if cache_age < timedelta(minutes=cache_timeout_minutes):
                logger.info(f"Using cached alerts ({len(self.cache)} alerts)")
                return self.cache
        
        try:
            # Parse RSS feed
            logger.info(f"Fetching INMET alerts from {self.RSS_FEED_URL}")
            feed = feedparser.parse(self.RSS_FEED_URL)
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing error: {feed.bozo_exception}")
                # Tentar URL alternativa
                feed = feedparser.parse(self.RSS_FEED_URL_ALT)
            
            alerts = []
            
            for entry in feed.entries:
                alert = self._parse_entry(entry)
                if alert:
                    alerts.append(alert)
            
            # Atualizar cache
            self.cache = alerts
            self.last_update = datetime.now()
            
            logger.info(f"Fetched {len(alerts)} alerts from INMET RSS")
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching INMET alerts: {e}")
            # Retornar cache mesmo se expirado em caso de erro
            return self.cache if self.cache else []
    
    def _parse_entry(self, entry) -> Optional[INMETAlert]:
        """
        Parse uma entrada do RSS
        
        Args:
            entry: Entrada do feed RSS
        
        Returns:
            INMETAlert ou None
        """
        try:
            # Extrair ID do link
            alert_id = entry.link.split('/')[-1] if entry.link else str(hash(entry.title))
            
            # Extrair tipo de evento e severidade do título
            title = entry.title
            event_type, severity = self._parse_title(title)
            
            # Mapear severidade para nível numérico
            severity_level = self._severity_to_level(severity)
            
            # Extrair tempos do description (HTML)
            start_time, end_time = self._parse_times(entry.description)
            
            # Extrair áreas afetadas
            affected_areas = self._parse_areas(entry.description)
            
            # Extrair descrição limpa
            description = self._clean_description(entry.description)
            
            # Parse published time
            published = self._parse_published(entry.published)
            
            alert = INMETAlert(
                alert_id=alert_id,
                title=title,
                event_type=event_type,
                severity=severity,
                severity_level=severity_level,
                start_time=start_time,
                end_time=end_time,
                description=description,
                affected_areas=affected_areas,
                link=entry.link,
                published=published
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    def _parse_title(self, title: str) -> tuple:
        """
        Extrair tipo de evento e severidade do título
        
        Exemplos:
        - "Aviso de Chuvas Intensas. Severidade Grau: Perigo Potencial"
        - "Aviso de Baixa Umidade. Severidade Grau: Perigo"
        - "Aviso de Tempestade. Severidade Grau: Grande Perigo"
        """
        event_type = "Desconhecido"
        severity = "Perigo Potencial"
        
        # Extrair tipo de evento
        event_patterns = [
            (r'Chuvas Intensas', 'Chuvas Intensas'),
            (r'Baixa Umidade', 'Baixa Umidade'),
            (r'Ventos Costeiros', 'Ventos Costeiros'),
            (r'Tempestade', 'Tempestade'),
            (r'Declínio de Temperatura', 'Declínio de Temperatura'),
            (r'Acumulado de Chuva', 'Acumulado de Chuva'),
            (r'Onda de Calor', 'Onda de Calor'),
            (r'Granizo', 'Granizo'),
        ]
        
        for pattern, event in event_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                event_type = event
                break
        
        # Extrair severidade
        severity_patterns = [
            (r'Grande Perigo', 'Grande Perigo'),
            (r'\bPerigo\b', 'Perigo'),
            (r'Perigo Potencial', 'Perigo Potencial'),
        ]
        
        for pattern, sev in severity_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                severity = sev
                break
        
        return event_type, severity
    
    def _severity_to_level(self, severity: str) -> int:
        """
        Mapear severidade para nível numérico
        
        1 = Perigo Potencial (Amarelo)
        2 = Perigo (Laranja)
        3 = Grande Perigo (Vermelho)
        """
        mapping = {
            'Perigo Potencial': 1,
            'Perigo': 2,
            'Grande Perigo': 3
        }
        return mapping.get(severity, 1)
    
    def _parse_times(self, description_html: str) -> tuple:
        """
        Extrair tempos de início e fim do description HTML
        
        Returns:
            (start_time, end_time)
        """
        start_time = datetime.now()
        end_time = datetime.now() + timedelta(hours=24)
        
        try:
            soup = BeautifulSoup(description_html, 'html.parser')
            
            # Procurar por "Início" e "Fim" nas tabelas
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    if 'início' in header or 'inicio' in header:
                        start_time = self._parse_datetime_string(value)
                    elif 'fim' in header:
                        end_time = self._parse_datetime_string(value)
            
        except Exception as e:
            logger.error(f"Error parsing times: {e}")
        
        return start_time, end_time
    
    def _parse_datetime_string(self, dt_string: str) -> datetime:
        """
        Parse string de datetime do INMET
        
        Formato: "2026-02-16 09:00:00.0"
        """
        try:
            # Remover milissegundos se presente
            dt_string = dt_string.split('.')[0]
            return datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now()
    
    def _parse_areas(self, description_html: str) -> List[str]:
        """
        Extrair áreas afetadas do description HTML
        """
        areas = []
        
        try:
            soup = BeautifulSoup(description_html, 'html.parser')
            
            # Procurar por "Área" nas tabelas
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()
                    
                    if 'área' in header or 'area' in header:
                        # Extrair nomes de áreas (separados por vírgula)
                        area_text = value.replace('Aviso para as Áreas:', '').strip()
                        areas = [a.strip() for a in area_text.split(',')]
                        break
            
        except Exception as e:
            logger.error(f"Error parsing areas: {e}")
        
        return areas
    
    def _clean_description(self, description_html: str) -> str:
        """
        Limpar description HTML para texto puro
        """
        try:
            soup = BeautifulSoup(description_html, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except:
            return description_html
    
    def _parse_published(self, published_string: str) -> datetime:
        """
        Parse published time string
        """
        try:
            return datetime.strptime(published_string, '%a, %d %b %Y %H:%M:%S %z')
        except:
            return datetime.now()
    
    def get_active_alerts(
        self,
        event_type: str = None,
        severity_level: int = None,
        location: str = None
    ) -> List[INMETAlert]:
        """
        Obter alertas ativos com filtros opcionais
        
        Args:
            event_type: Filtrar por tipo de evento
            severity_level: Filtrar por nível de severidade (1, 2, 3)
            location: Filtrar por localização (busca parcial)
        
        Returns:
            Lista de alertas filtrados
        """
        alerts = self.fetch_alerts()
        now = datetime.now()
        
        # Filtrar alertas ativos (dentro do período)
        active_alerts = [
            a for a in alerts
            if a.start_time <= now <= a.end_time
        ]
        
        # Aplicar filtros adicionais
        if event_type:
            active_alerts = [
                a for a in active_alerts
                if a.event_type.lower() == event_type.lower()
            ]
        
        if severity_level:
            active_alerts = [
                a for a in active_alerts
                if a.severity_level >= severity_level
            ]
        
        if location:
            active_alerts = [
                a for a in active_alerts
                if any(location.lower() in area.lower() for area in a.affected_areas)
            ]
        
        return active_alerts
    
    def get_alerts_by_severity(self) -> Dict[str, List[INMETAlert]]:
        """
        Obter alertas agrupados por severidade
        
        Returns:
            Dict com chaves 'Perigo Potencial', 'Perigo', 'Grande Perigo'
        """
        alerts = self.fetch_alerts()
        
        return {
            'Perigo Potencial': [a for a in alerts if a.severity == 'Perigo Potencial'],
            'Perigo': [a for a in alerts if a.severity == 'Perigo'],
            'Grande Perigo': [a for a in alerts if a.severity == 'Grande Perigo']
        }
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """
        Obter resumo dos alertas
        
        Returns:
            Dict com estatísticas
        """
        alerts = self.fetch_alerts()
        now = datetime.now()
        
        active_alerts = [a for a in alerts if a.start_time <= now <= a.end_time]
        
        return {
            'total_alerts': len(alerts),
            'active_alerts': len(active_alerts),
            'by_severity': {
                'Perigo Potencial': len([a for a in active_alerts if a.severity == 'Perigo Potencial']),
                'Perigo': len([a for a in active_alerts if a.severity == 'Perigo']),
                'Grande Perigo': len([a for a in active_alerts if a.severity == 'Grande Perigo'])
            },
            'by_event_type': self._count_by_event_type(active_alerts),
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
    
    def _count_by_event_type(self, alerts: List[INMETAlert]) -> Dict[str, int]:
        """Contar alertas por tipo de evento"""
        counts = {}
        for alert in alerts:
            event_type = alert.event_type
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status do serviço
        
        Returns:
            Dict com status
        """
        return {
            'service': 'INMET Alertas RSS',
            'status': 'active' if self.cache else 'inactive',
            'feed_url': self.RSS_FEED_URL,
            'total_alerts_cached': len(self.cache),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'cache_timeout_minutes': 15
        }
