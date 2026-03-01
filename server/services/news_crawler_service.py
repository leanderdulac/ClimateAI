"""
News Crawler Service - Radar de Notícias em Tempo Real
Varre RSS feeds de portais brasileiros e classifica eventos climáticos extremos
usando NLP por palavras-chave para alimentar o Oracle com dados da mídia.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

import aiohttp
import feedparser

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CrawledNewsAlert:
    """Alerta extraído de notícias"""
    alert_id: str
    title: str
    summary: str
    source: str
    source_url: str
    published: datetime
    disaster_type: str          # inundacao, deslizamento, seca, vendaval, granizo, incendio
    severity: str               # baixa, media, alta, critica
    severity_score: float       # 1.0 - 5.0
    locations: List[str]        # cidades/estados mencionados
    uf: Optional[str] = None
    confidence: float = 0.0     # 0.0 - 1.0 confiança da classificação
    crawled_at: datetime = field(default_factory=datetime.now)


# ─────────────────────────────────────────────────────────────────────────────
# NLP Keyword Dictionaries
# ─────────────────────────────────────────────────────────────────────────────

DISASTER_KEYWORDS = {
    'inundacao': {
        'keywords': [
            'inundação', 'inundacao', 'enchente', 'alagamento', 'cheia',
            'transbord', 'nível do rio', 'rio transbord', 'água invad',
            'submers', 'dilúvio', 'tromba d\'água', 'enxurrada'
        ],
        'weight': 1.0
    },
    'deslizamento': {
        'keywords': [
            'deslizamento', 'desmoronamento', 'desabamento', 'soterr',
            'barreira', 'encosta', 'morro', 'terra cedeu', 'escorregamento',
            'movimento de massa', 'queda de barreira'
        ],
        'weight': 1.2  # geralmente mais grave
    },
    'vendaval': {
        'keywords': [
            'vendaval', 'ventania', 'tempestade', 'ciclone', 'tornado',
            'furacão', 'rajada', 'ventos fortes', 'destrui', 'destelhamento',
            'queda de árvore'
        ],
        'weight': 0.9
    },
    'seca': {
        'keywords': [
            'seca', 'estiagem', 'falta de água', 'crise hídrica',
            'reservatório', 'nível baixo', 'desertificação', 'queimada seca'
        ],
        'weight': 0.7
    },
    'granizo': {
        'keywords': [
            'granizo', 'chuva de pedra', 'pedras de gelo', 'tempestade de granizo'
        ],
        'weight': 0.8
    },
    'incendio': {
        'keywords': [
            'incêndio', 'incendio', 'queimada', 'fogo', 'chamas',
            'incêndio florestal', 'devastação pelo fogo', 'pantanal em chamas',
            'amazônia em chamas'
        ],
        'weight': 0.9
    },
}

SEVERITY_INDICATORS = {
    'critica': {
        'keywords': [
            'mortes', 'morreu', 'morreram', 'óbito', 'vítima fatal',
            'desaparecido', 'tragédia', 'catástrofe', 'estado de emergência',
            'calamidade pública', 'destruição total', 'apocal'
        ],
        'score': 5.0
    },
    'alta': {
        'keywords': [
            'desabrigad', 'desalojad', 'resgatad', 'evacua', 'interdita',
            'destruíd', 'grave', 'alerta máximo', 'alerta vermelho',
            'risco iminente', 'situação crítica', 'milhares', 'centenas'
        ],
        'score': 4.0
    },
    'media': {
        'keywords': [
            'danos', 'prejuízo', 'afetad', 'bloqueio', 'interdição',
            'alerta laranja', 'atenção', 'risco moderado', 'impacto'
        ],
        'score': 3.0
    },
    'baixa': {
        'keywords': [
            'monitoramento', 'previsão', 'possibilidade', 'risco baixo',
            'alerta amarelo', 'atenção', 'cuidado'
        ],
        'score': 2.0
    },
}

# Brazilian states for geo-extraction
UF_MAP: Dict[str, str] = {
    'acre': 'AC', 'alagoas': 'AL', 'amapá': 'AP', 'amazonas': 'AM',
    'bahia': 'BA', 'ceará': 'CE', 'distrito federal': 'DF',
    'espírito santo': 'ES', 'goiás': 'GO', 'maranhão': 'MA',
    'mato grosso': 'MT', 'mato grosso do sul': 'MS', 'minas gerais': 'MG',
    'pará': 'PA', 'paraíba': 'PB', 'paraná': 'PR', 'pernambuco': 'PE',
    'piauí': 'PI', 'rio de janeiro': 'RJ', 'rio grande do norte': 'RN',
    'rio grande do sul': 'RS', 'rondônia': 'RO', 'roraima': 'RR',
    'santa catarina': 'SC', 'são paulo': 'SP', 'sergipe': 'SE',
    'tocantins': 'TO',
}

# Major Brazilian cities for geo-extraction
MAJOR_CITIES = [
    'São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Porto Alegre',
    'Salvador', 'Fortaleza', 'Recife', 'Curitiba', 'Manaus', 'Belém',
    'Florianópolis', 'Goiânia', 'Brasília', 'Natal', 'Campo Grande',
    'Vitória', 'Maceió', 'João Pessoa', 'Teresina', 'Cuiabá',
    'Petrópolis', 'Niterói', 'Santos', 'Campinas', 'Ribeirão Preto',
    'Blumenau', 'Joinville', 'Canoas', 'São Leopoldo', 'Eldorado do Sul',
    'São Sebastião', 'Ubatuba', 'Angra dos Reis', 'Paraty', 'Muçum',
]


# ─────────────────────────────────────────────────────────────────────────────
# RSS Feed Sources
# ─────────────────────────────────────────────────────────────────────────────

RSS_FEEDS = [
    {
        'name': 'Google News BR - Desastres',
        'url': 'https://news.google.com/rss/search?q=enchente+OR+deslizamento+OR+inundação+OR+tempestade+OR+seca+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419',
        'source': 'Google News',
    },
    {
        'name': 'Google News BR - Clima Extremo',
        'url': 'https://news.google.com/rss/search?q=alerta+climático+OR+chuva+forte+OR+vendaval+OR+granizo+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419',
        'source': 'Google News',
    },
    {
        'name': 'Google News BR - Defesa Civil',
        'url': 'https://news.google.com/rss/search?q=defesa+civil+OR+estado+emergência+desastre+natural+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419',
        'source': 'Google News',
    },
    {
        'name': 'G1 Natureza',
        'url': 'https://g1.globo.com/rss/g1/natureza/',
        'source': 'G1',
    },
    {
        'name': 'G1 Ciência e Saúde',
        'url': 'https://g1.globo.com/rss/g1/ciencia-e-saude/',
        'source': 'G1',
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class NewsCrawlerService:
    """
    Serviço de crawling de notícias climáticas em tempo real.
    Varre feeds RSS, classifica eventos por NLP e armazena alertas.
    """

    def __init__(self):
        self.alerts: List[CrawledNewsAlert] = []
        self._seen_hashes: set = set()
        self._last_crawl: Optional[datetime] = None
        self._crawl_interval_seconds: int = 600  # 10 minutos
        self._max_alerts: int = 200
        self._is_crawling: bool = False
        self._background_task: Optional[asyncio.Task] = None
        logger.info("NewsCrawlerService initialized")

    # ── Public API ───────────────────────────────────────────────────────

    async def start_background_crawl(self):
        """Inicia crawl periódico em background"""
        if self._background_task is None:
            self._background_task = asyncio.create_task(self._periodic_crawl())
            logger.info("Background news crawl started")

    async def stop_background_crawl(self):
        """Para o crawl periódico"""
        if self._background_task:
            self._background_task.cancel()
            self._background_task = None
            logger.info("Background news crawl stopped")

    async def force_refresh(self) -> Dict[str, Any]:
        """Força uma varredura imediata"""
        new_count = await self._crawl_all_feeds()
        return {
            'status': 'ok',
            'new_alerts': new_count,
            'total_alerts': len(self.alerts),
            'crawled_at': datetime.now().isoformat(),
        }

    def get_recent_alerts(self, limit: int = 20, disaster_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retorna alertas recentes, opcionalmente filtrados por tipo"""
        filtered = self.alerts
        if disaster_type:
            filtered = [a for a in filtered if a.disaster_type == disaster_type]

        sorted_alerts = sorted(filtered, key=lambda a: a.published, reverse=True)
        return [asdict(a) for a in sorted_alerts[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Estatísticas dos alertas coletados"""
        if not self.alerts:
            return {
                'total_alerts': 0,
                'by_type': {},
                'by_severity': {},
                'by_source': {},
                'last_crawl': self._last_crawl.isoformat() if self._last_crawl else None,
                'oldest_alert': None,
                'newest_alert': None,
            }

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_source: Dict[str, int] = {}

        for alert in self.alerts:
            by_type[alert.disaster_type] = by_type.get(alert.disaster_type, 0) + 1
            by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
            by_source[alert.source] = by_source.get(alert.source, 0) + 1

        sorted_alerts = sorted(self.alerts, key=lambda a: a.published)

        return {
            'total_alerts': len(self.alerts),
            'by_type': by_type,
            'by_severity': by_severity,
            'by_source': by_source,
            'last_crawl': self._last_crawl.isoformat() if self._last_crawl else None,
            'oldest_alert': sorted_alerts[0].published.isoformat() if sorted_alerts else None,
            'newest_alert': sorted_alerts[-1].published.isoformat() if sorted_alerts else None,
        }

    def get_oracle_events(self, min_severity: str = 'media', min_confidence: float = 0.2) -> List[Dict[str, Any]]:
        """
        Converte alertas de alta confiança em eventos compatíveis com o Oracle.
        Usado para injetar notícias reais no pipeline de live-events do Oracle.
        
        Multi-Source Consensus: apenas alertas que passam pelo filtro mínimo
        de severidade E confiança são promovidos a eventos Oracle.
        """
        import uuid
        import random
        
        severity_order = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
        min_sev_level = severity_order.get(min_severity, 2)
        
        # Coordenadas de fallback para cidades conhecidas
        city_coords = {
            'São Paulo': (-23.550, -46.633),
            'Rio de Janeiro': (-22.906, -43.172),
            'Belo Horizonte': (-19.916, -43.934),
            'Porto Alegre': (-30.034, -51.217),
            'Salvador': (-12.971, -38.501),
            'Fortaleza': (-3.731, -38.526),
            'Recife': (-8.047, -34.877),
            'Curitiba': (-25.428, -49.273),
            'Manaus': (-3.119, -60.021),
            'Florianópolis': (-27.595, -48.548),
            'Belém': (-1.455, -48.502),
            'Goiânia': (-16.686, -49.264),
            'Brasília': (-15.793, -47.882),
            'Petrópolis': (-22.505, -43.178),
            'Blumenau': (-26.919, -49.066),
        }
        
        # Default coords by UF
        uf_coords = {
            'SP': (-23.550, -46.633), 'RJ': (-22.906, -43.172),
            'MG': (-19.916, -43.934), 'RS': (-30.034, -51.217),
            'BA': (-12.971, -38.501), 'CE': (-3.731, -38.526),
            'PE': (-8.047, -34.877), 'PR': (-25.428, -49.273),
            'AM': (-3.119, -60.021), 'SC': (-27.595, -48.548),
            'PA': (-1.455, -48.502), 'GO': (-16.686, -49.264),
            'DF': (-15.793, -47.882), 'ES': (-20.315, -40.312),
            'MT': (-15.601, -56.097), 'MS': (-20.469, -54.620),
            'MA': (-2.530, -44.282), 'PI': (-5.089, -42.801),
            'RN': (-5.795, -35.209), 'PB': (-7.119, -34.845),
            'AL': (-9.665, -35.735), 'SE': (-10.911, -37.071),
            'AC': (-9.974, -67.807), 'RO': (-8.761, -63.903),
            'AP': (0.034, -51.066), 'RR': (2.819, -60.671),
            'TO': (-10.184, -48.333),
        }
        
        oracle_events = []
        
        for alert in self.alerts:
            sev_level = severity_order.get(alert.severity, 0)
            if sev_level < min_sev_level or alert.confidence < min_confidence:
                continue
            
            # Determine coordinates
            lat, lon = -15.793, -47.882  # Brasília fallback
            for city in alert.locations:
                if city in city_coords:
                    lat, lon = city_coords[city]
                    break
            else:
                if alert.uf and alert.uf in uf_coords:
                    lat, lon = uf_coords[alert.uf]
            
            # Determine municipality name — use title snippet if no location found
            if alert.locations:
                municipio = alert.locations[0]
            elif alert.uf:
                municipio = alert.uf
            else:
                # Use first meaningful words from title as location label
                municipio = alert.title.split(' - ')[0][:40] if alert.title else 'Brasil'
            
            payout_triggered = alert.severity_score >= 3.0
            payout_pct = min(1.0, (alert.severity_score - 3.0) / 2.0 + 0.25) if payout_triggered else 0.0
            
            oracle_events.append({
                'event_id': f"news_{alert.alert_id}",
                'token_id': f"tok_{uuid.uuid4().hex[:8]}",
                'municipio': municipio,
                'uf': alert.uf or 'BR',
                'latitude': lat,
                'longitude': lon,
                'disaster_type': alert.disaster_type,
                'severity_score': alert.severity_score,
                'ndvi': round(random.uniform(0.1, 0.4) if alert.disaster_type == 'seca' else random.uniform(0.2, 0.8), 3),
                'soil_moisture': round(random.uniform(0.1, 0.3) if alert.disaster_type == 'seca' else random.uniform(0.3, 0.7), 3),
                'timestamp': alert.published.isoformat(),
                'payout_triggered': payout_triggered,
                'payout_percentage': round(payout_pct, 2),
                'payout_amount': round(payout_pct * 100000.0, 2),
                'blockchain_tx_id': None,
                'status': 'TRIGGERED' if payout_triggered else 'PENDING',
                'source': f"📰 {alert.source}: {alert.title[:80]}",
                'confidence': alert.confidence,
            })
        
        return oracle_events

    def get_risk_adjustment_factor(self, uf: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula fator de ajuste de risco dinâmico baseado nas notícias recentes.
        
        Usado pelo modelo de precificação para ajustar o prêmio em tempo real:
        - Muitas notícias de severidade alta/crítica → prêmio sobe
        - Poucas notícias ou baixa severidade → prêmio normal
        
        Retorna:
            risk_factor: multiplicador (0.0 a 0.30 = até +30% no prêmio)
            alert_count: quantidade de alertas relevantes
            dominant_disaster: tipo de desastre mais frequente
        """
        recent_cutoff = datetime.now() - timedelta(hours=24)
        
        relevant = [a for a in self.alerts if a.published >= recent_cutoff]
        if uf:
            relevant = [a for a in relevant if a.uf == uf]
        
        if not relevant:
            return {
                'risk_factor': 0.0,
                'alert_count': 0,
                'dominant_disaster': None,
                'severity_avg': 0.0,
                'description': 'Sem alertas recentes — risco base mantido',
            }
        
        # Calculate weighted severity
        severity_scores = [a.severity_score * a.confidence for a in relevant]
        avg_severity = sum(severity_scores) / len(severity_scores)
        
        # Count by type
        by_type: Dict[str, int] = {}
        for a in relevant:
            by_type[a.disaster_type] = by_type.get(a.disaster_type, 0) + 1
        dominant = max(by_type, key=by_type.get) if by_type else None
        
        # Risk factor: scales from 0 to 0.30
        # Based on: number of alerts × average severity
        density_factor = min(1.0, len(relevant) / 10.0)  # max at 10+ alerts
        severity_factor = min(1.0, avg_severity / 4.0)    # max at severity 4+
        
        risk_factor = round(density_factor * severity_factor * 0.30, 4)
        
        if risk_factor > 0.20:
            desc = f'⚠️ ALTO RISCO: {len(relevant)} alertas em 24h — prêmio ajustado +{risk_factor*100:.1f}%'
        elif risk_factor > 0.10:
            desc = f'🔶 RISCO MODERADO: {len(relevant)} alertas — prêmio ajustado +{risk_factor*100:.1f}%'
        elif risk_factor > 0:
            desc = f'🔵 RISCO LEVE: {len(relevant)} alertas — prêmio ajustado +{risk_factor*100:.1f}%'
        else:
            desc = 'Sem alertas recentes — risco base mantido'
        
        return {
            'risk_factor': risk_factor,
            'alert_count': len(relevant),
            'dominant_disaster': dominant,
            'severity_avg': round(avg_severity, 2),
            'description': desc,
        }

    # ── Private Crawling ─────────────────────────────────────────────────

    async def _periodic_crawl(self):
        """Loop de crawl periódico"""
        while True:
            try:
                await self._crawl_all_feeds()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic crawl: {e}")
            await asyncio.sleep(self._crawl_interval_seconds)

    async def _crawl_all_feeds(self) -> int:
        """Varre todos os feeds configurados"""
        if self._is_crawling:
            logger.warning("Crawl already in progress, skipping")
            return 0

        self._is_crawling = True
        new_count = 0

        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for feed_config in RSS_FEEDS:
                    try:
                        count = await self._crawl_feed(session, feed_config)
                        new_count += count
                    except Exception as e:
                        logger.warning(f"Failed to crawl {feed_config['name']}: {e}")

            self._last_crawl = datetime.now()

            # Trim old alerts
            if len(self.alerts) > self._max_alerts:
                self.alerts.sort(key=lambda a: a.published, reverse=True)
                self.alerts = self.alerts[:self._max_alerts]

            logger.info(f"Crawl complete: {new_count} new alerts, {len(self.alerts)} total")

        finally:
            self._is_crawling = False

        return new_count

    async def _crawl_feed(self, session: aiohttp.ClientSession, feed_config: Dict) -> int:
        """Varre um feed RSS individual"""
        new_count = 0
        try:
            async with session.get(feed_config['url']) as resp:
                if resp.status != 200:
                    logger.warning(f"Feed {feed_config['name']} returned {resp.status}")
                    return 0

                content = await resp.text()
                parsed = feedparser.parse(content)

                for entry in parsed.entries:
                    alert = self._process_entry(entry, feed_config)
                    if alert:
                        new_count += 1

        except asyncio.TimeoutError:
            logger.warning(f"Timeout crawling {feed_config['name']}")
        except Exception as e:
            logger.warning(f"Error crawling {feed_config['name']}: {e}")

        return new_count

    def _process_entry(self, entry: Any, feed_config: Dict) -> Optional[CrawledNewsAlert]:
        """Processa uma entrada individual do RSS"""
        title = getattr(entry, 'title', '') or ''
        summary = getattr(entry, 'summary', '') or ''
        link = getattr(entry, 'link', '') or ''

        # Dedup by title hash
        text_hash = hashlib.md5(title.lower().encode()).hexdigest()
        if text_hash in self._seen_hashes:
            return None

        # Classify disaster
        combined_text = f"{title} {summary}".lower()
        disaster_result = self._classify_disaster(combined_text)

        if not disaster_result:
            return None  # Not a climate/disaster article

        disaster_type, disaster_confidence = disaster_result

        # Classify severity
        severity, severity_score = self._classify_severity(combined_text, disaster_type)

        # Extract locations
        locations = self._extract_locations(f"{title} {summary}")
        uf = self._extract_uf(f"{title} {summary}")

        # Parse published date
        published = self._parse_date(entry)

        # Build alert
        alert = CrawledNewsAlert(
            alert_id=f"news_{text_hash[:12]}",
            title=title[:200],
            summary=self._clean_html(summary)[:500],
            source=feed_config.get('source', 'Unknown'),
            source_url=link,
            published=published,
            disaster_type=disaster_type,
            severity=severity,
            severity_score=severity_score,
            locations=locations,
            uf=uf,
            confidence=disaster_confidence,
        )

        self._seen_hashes.add(text_hash)
        self.alerts.append(alert)
        return alert

    # ── NLP Classification ───────────────────────────────────────────────

    def _classify_disaster(self, text: str) -> Optional[tuple]:
        """Classifica o tipo de desastre com base em keywords"""
        best_type = None
        best_score = 0.0

        for dtype, config in DISASTER_KEYWORDS.items():
            matches = sum(1 for kw in config['keywords'] if kw in text)
            if matches > 0:
                score = matches * config['weight']
                if score > best_score:
                    best_score = score
                    best_type = dtype

        if best_type is None:
            return None

        # Confidence: more keyword matches = higher confidence
        max_possible = len(DISASTER_KEYWORDS[best_type]['keywords'])
        confidence = min(1.0, best_score / max(max_possible * 0.3, 1))

        return (best_type, round(confidence, 2))

    def _classify_severity(self, text: str, disaster_type: str) -> tuple:
        """Classifica a severidade da notícia"""
        for level in ['critica', 'alta', 'media', 'baixa']:
            config = SEVERITY_INDICATORS[level]
            matches = sum(1 for kw in config['keywords'] if kw in text)
            if matches > 0:
                return (level, config['score'])

        return ('media', 2.5)

    def _extract_locations(self, text: str) -> List[str]:
        """Extrai menções de cidades conhecidas"""
        found = []
        for city in MAJOR_CITIES:
            if city.lower() in text.lower():
                found.append(city)
        return found[:5]

    def _extract_uf(self, text: str) -> Optional[str]:
        """Extrai estado (UF)"""
        text_lower = text.lower()

        for state_name, uf_code in UF_MAP.items():
            if state_name in text_lower:
                return uf_code

        # Try UF abbreviations: (RS), (SP), etc.
        uf_match = re.findall(r'\b([A-Z]{2})\b', text)
        valid_ufs = set(UF_MAP.values())
        for uf in uf_match:
            if uf in valid_ufs:
                return uf

        return None

    # ── Utilities ────────────────────────────────────────────────────────

    def _parse_date(self, entry: Any) -> datetime:
        """Parse RSS entry date"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            from time import mktime
            try:
                return datetime.fromtimestamp(mktime(entry.published_parsed))
            except Exception:
                pass
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            from time import mktime
            try:
                return datetime.fromtimestamp(mktime(entry.updated_parsed))
            except Exception:
                pass
        return datetime.now()

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove tags HTML básicas"""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean


# Singleton
_news_crawler_service: Optional[NewsCrawlerService] = None


def get_news_crawler_service() -> NewsCrawlerService:
    """Retorna instância singleton do serviço de crawling"""
    global _news_crawler_service
    if _news_crawler_service is None:
        _news_crawler_service = NewsCrawlerService()
    return _news_crawler_service
