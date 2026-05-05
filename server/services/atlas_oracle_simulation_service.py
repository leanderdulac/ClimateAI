"""
Atlas Oracle Simulation Service
Simula dados reais do Oracle e Blockchain para demonstração do Atlas

Este serviço:
1. Simula eventos de desastres em tempo real
2. Gera scores de severidade baseados em dados do Atlas
3. Simula triggers de payout no Oracle
4. Simula transações blockchain (Hathor)
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SimulatedOracleEvent:
    """Evento simulado do Oracle"""
    event_id: str
    token_id: str
    municipio: str
    uf: str
    latitude: float
    longitude: float
    disaster_type: str
    severity_score: float  # 1.0-5.0
    ndvi: float  # 0.0-1.0
    soil_moisture: float  # 0.0-1.0
    timestamp: datetime
    payout_triggered: bool
    payout_percentage: float
    payout_amount: float
    blockchain_tx_id: Optional[str]
    status: str  # PENDING, EVALUATING, TRIGGERED, PAID


@dataclass
class SimulatedBlockchainTransaction:
    """Transação blockchain simulada"""
    tx_id: str
    token_uid: str
    from_address: str
    to_address: str
    amount: float
    timestamp: datetime
    block_height: int
    confirmations: int
    status: str  # PENDING, CONFIRMED


class AtlasOracleSimulationService:
    """
    Serviço de simulação de Oracle e Blockchain para Atlas
    
    Gera dados realistas baseados em:
    - Histórico do Atlas Digital
    - Condições climáticas sazonais
    - Perfis de risco por município
    """

    # Municípios de alto risco (baseado no Atlas)
    HIGH_RISK_MUNICIPALITIES = [
        {'municipio': 'Porto Alegre', 'uf': 'RS', 'lat': -30.0346, 'lon': -51.2177, 'risk': 0.7},
        {'municipio': 'São Paulo', 'uf': 'SP', 'lat': -23.5505, 'lon': -46.6333, 'risk': 0.5},
        {'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'lat': -22.9068, 'lon': -43.1729, 'risk': 0.6},
        {'municipio': 'Belo Horizonte', 'uf': 'MG', 'lat': -19.9167, 'lon': -43.9345, 'risk': 0.5},
        {'municipio': 'Recife', 'uf': 'PE', 'lat': -8.0476, 'lon': -34.8770, 'risk': 0.6},
        {'municipio': 'Fortaleza', 'uf': 'CE', 'lat': -3.7319, 'lon': -38.5267, 'risk': 0.4},
        {'municipio': 'Salvador', 'uf': 'BA', 'lat': -12.9714, 'lon': -38.5014, 'risk': 0.5},
        {'municipio': 'Curitiba', 'uf': 'PR', 'lat': -25.4284, 'lon': -49.2733, 'risk': 0.4},
        {'municipio': 'Florianópolis', 'uf': 'SC', 'lat': -27.5954, 'lon': -48.5480, 'risk': 0.5},
        {'municipio': 'Manaus', 'uf': 'AM', 'lat': -3.1190, 'lon': -60.0217, 'risk': 0.3},
    ]

    # Tipos de desastres por região/saison
    SEASONAL_DISASTERS = {
        'summer': ['inundacao', 'deslizamento', 'vendaval'],
        'winter': ['seca', 'geada', 'incendio'],
        'spring': ['inundacao', 'granizo', 'vendaval'],
        'autumn': ['inundacao', 'deslizamento', 'seca'],
    }

    # Tokens blockchain simulados
    SIMULATED_TOKENS = {
        'CLMT': {'uid': 'a7b3c9d2e1f4g5h6', 'name': 'Climate Index Token', 'supply': 1000000},
        'DROUGHT': {'uid': 'b8c4d0e2f5g6h7i8', 'name': 'Drought Insurance Token', 'supply': 500000},
        'FLOOD': {'uid': 'c9d5e1f6g7h8i9j0', 'name': 'Flood Insurance Token', 'supply': 500000},
    }

    def __init__(self):
        self.events: List[SimulatedOracleEvent] = []
        self.transactions: List[SimulatedBlockchainTransaction] = []
        self._last_update = datetime.now()
        
        # Gerar eventos iniciais apenas se necessário
        # self._generate_initial_events()
        
        logger.info("AtlasOracleSimulationService initialized")

    def _get_current_season(self) -> str:
        """Obter estação atual (hemisfério sul)"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'summer'
        elif month in [3, 4, 5]:
            return 'autumn'
        elif month in [6, 7, 8]:
            return 'winter'
        else:
            return 'spring'

    def _generate_severity_score(self, municipio_data: Dict) -> float:
        """
        Gerar score de severidade realista baseado em:
        - Risco histórico do município
        - Sazonalidade
        - Fatores aleatórios controlados
        """
        base_risk = municipio_data['risk']
        
        # Ajuste sazonal
        season = self._get_current_season()
        season_factor = 1.2 if season == 'summer' else 1.0
        
        # Variação aleatória controlada
        random_factor = random.uniform(0.7, 1.3)
        
        # Calcular severidade (1.0-5.0)
        severity = base_risk * 5.0 * season_factor * random_factor
        severity = max(1.0, min(5.0, severity))
        
        return round(severity, 2)

    def _generate_event(self, municipio_data: Dict) -> SimulatedOracleEvent:
        """Gerar evento simulado do Oracle"""
        # Determinar tipo de desastre baseado na estação
        season = self._get_current_season()
        disaster_types = self.SEASONAL_DISASTERS[season]
        disaster_type = random.choice(disaster_types)
        
        # Gerar severidade
        severity = self._generate_severity_score(municipio_data)
        
        # Determinar se payout é triggerado
        payout_threshold = 3.0
        payout_triggered = severity >= payout_threshold
        payout_percentage = min(1.0, (severity - payout_threshold) / 2.0 + 0.25) if payout_triggered else 0.0
        
        # Calcular valor do payout (baseado em cobertura simulada de R$ 100k)
        base_coverage = 100000.0
        payout_amount = payout_percentage * base_coverage if payout_triggered else 0.0
        
        # Gerar IDs
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        token_id = f"tok_{uuid.uuid4().hex[:8]}"
        
        # Gerar NDVI e soil moisture realistas
        ndvi = random.uniform(0.2, 0.8) if disaster_type != 'seca' else random.uniform(0.1, 0.4)
        soil_moisture = random.uniform(0.3, 0.7) if disaster_type != 'seca' else random.uniform(0.1, 0.3)
        
        # Blockchain TX (se payout triggerado)
        blockchain_tx_id = None
        status = 'PENDING'
        
        if payout_triggered:
            blockchain_tx_id = self._generate_blockchain_tx(payout_amount, municipio_data['uf'])
            status = 'TRIGGERED'
        
        event = SimulatedOracleEvent(
            event_id=event_id,
            token_id=token_id,
            municipio=municipio_data['municipio'],
            uf=municipio_data['uf'],
            latitude=municipio_data['lat'],
            longitude=municipio_data['lon'],
            disaster_type=disaster_type,
            severity_score=severity,
            ndvi=round(ndvi, 3),
            soil_moisture=round(soil_moisture, 3),
            timestamp=datetime.now() - timedelta(hours=random.randint(0, 72)),
            payout_triggered=payout_triggered,
            payout_percentage=round(payout_percentage, 2),
            payout_amount=round(payout_amount, 2),
            blockchain_tx_id=blockchain_tx_id,
            status=status,
        )
        
        return event

    def _generate_blockchain_tx(self, amount: float, uf: str) -> str:
        """Gerar transação blockchain simulada"""
        tx_id = hashlib.sha256(f"{uuid.uuid4().hex}{amount}{uf}".encode()).hexdigest()[:64]
        
        tx = SimulatedBlockchainTransaction(
            tx_id=tx_id,
            token_uid=self.SIMULATED_TOKENS['CLMT']['uid'],
            from_address='0x' + hashlib.md5(b'oracle', usedforsecurity=False).hexdigest(),
            to_address='0x' + hashlib.md5(uf.encode(), usedforsecurity=False).hexdigest(),
            amount=amount,
            timestamp=datetime.now(),
            block_height=random.randint(1000000, 2000000),
            confirmations=random.randint(6, 100),
            status='CONFIRMED',
        )
        
        self.transactions.append(tx)
        return tx_id

    def _generate_initial_events(self, count: int = 15):
        """Gerar eventos iniciais com dados históricos REAIS para caso estrutural fallback"""
        # Eventos macro-reais históricos baseados no banco do Atlas/CEMADEN
        real_historical_events = [
            {'municipio': 'Eldorado do Sul', 'uf': 'RS', 'lat': -30.003, 'lon': -51.312, 'tipo': 'inundacao', 'sev': 5.0, 'mortes': 0, 'afetados': 40000},
            {'municipio': 'Muçum', 'uf': 'RS', 'lat': -29.165, 'lon': -51.874, 'tipo': 'inundacao', 'sev': 4.9, 'mortes': 49, 'afetados': 15000},
            {'municipio': 'São Sebastião', 'uf': 'SP', 'lat': -23.760, 'lon': -45.414, 'tipo': 'deslizamento', 'sev': 4.8, 'mortes': 64, 'afetados': 3200},
            {'municipio': 'Petrópolis', 'uf': 'RJ', 'lat': -22.505, 'lon': -43.178, 'tipo': 'deslizamento', 'sev': 5.0, 'mortes': 234, 'afetados': 70000},
            {'municipio': 'Manaus', 'uf': 'AM', 'lat': -3.119, 'lon': -60.021, 'tipo': 'seca', 'sev': 4.7, 'mortes': 0, 'afetados': 120000},
            {'municipio': 'Porto Alegre', 'uf': 'RS', 'lat': -30.034, 'lon': -51.217, 'tipo': 'inundacao', 'sev': 5.0, 'mortes': 5, 'afetados': 160000},
            {'municipio': 'Rio Branco', 'uf': 'AC', 'lat': -9.974, 'lon': -67.807, 'tipo': 'inundacao', 'sev': 4.2, 'mortes': 0, 'afetados': 45000},
            {'municipio': 'Belo Horizonte', 'uf': 'MG', 'lat': -19.916, 'lon': -43.934, 'tipo': 'inundacao', 'sev': 3.8, 'mortes': 2, 'afetados': 1200},
            {'municipio': 'Tefé', 'uf': 'AM', 'lat': -3.352, 'lon': -64.710, 'tipo': 'seca', 'sev': 4.8, 'mortes': 0, 'afetados': 45000},
            {'municipio': 'Recife', 'uf': 'PE', 'lat': -8.047, 'lon': -34.877, 'tipo': 'deslizamento', 'sev': 4.5, 'mortes': 128, 'afetados': 84000}
        ]
        
        for data in real_historical_events:
            payout_triggered = data['sev'] >= 3.0
            payout_percentage = min(1.0, (data['sev'] - 3.0) / 2.0 + 0.25) if payout_triggered else 0.0
            payout_amount = payout_percentage * 100000.0 if payout_triggered else 0.0
            
            blockchain_tx_id = self._generate_blockchain_tx(payout_amount, data['uf']) if payout_triggered else None
            status = 'TRIGGERED' if payout_triggered else 'PENDING'
            
            ndvi_val = random.uniform(0.1, 0.4) if data['tipo'] == 'seca' else random.uniform(0.2, 0.8)
            moist_val = random.uniform(0.1, 0.3) if data['tipo'] == 'seca' else random.uniform(0.3, 0.7)
            
            event = SimulatedOracleEvent(
                event_id=f"real_hist_{uuid.uuid4().hex[:8]}",
                token_id=f"tok_{uuid.uuid4().hex[:8]}",
                municipio=data['municipio'],
                uf=data['uf'],
                latitude=data['lat'],
                longitude=data['lon'],
                disaster_type=data['tipo'],
                severity_score=data['sev'],
                ndvi=round(ndvi_val, 3),
                soil_moisture=round(moist_val, 3),
                timestamp=datetime.now() - timedelta(days=random.randint(1, 400)),
                payout_triggered=payout_triggered,
                payout_percentage=round(payout_percentage, 2),
                payout_amount=round(payout_amount, 2),
                blockchain_tx_id=blockchain_tx_id,
                status=status,
            )
            self.events.append(event)
        
        logger.info(f"Loaded {len(real_historical_events)} genuine historical defaults.")

    async def get_live_events(self, db: Any, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obter eventos em tempo real do banco de dados (historicamente simulados)
        """
        import os
        from sqlalchemy.future import select
        from models.sqlalchemy_models import OracleEvent
        
        db_events = []
        # Query the database for REAL events directly, ignoring simulated ones completely.
        if os.getenv("DATABASE_ENABLED", "true").lower() == "true":
            try:
                from models.sqlalchemy_models import AtlasDisaster
                
                real_query = select(AtlasDisaster).where(
                    AtlasDisaster.latitude.isnot(None)
                ).order_by(AtlasDisaster.ano.desc()).limit(limit)
                
                real_res = await db.execute(real_query)
                real_disasters = real_res.scalars().all()
                
                import uuid
                import random
                
                for rd in real_disasters:
                    # Mapeia desastre real para um evento oráculo em memória
                    severity = 1.0
                    if rd.mortes_diretas and rd.mortes_diretas > 0:
                        severity = min(5.0, 3.0 + (rd.mortes_diretas / 10.0))
                    elif rd.afetados and rd.afetados > 1000:
                        severity = min(5.0, 2.5 + (rd.afetados / 10000.0))
                    else:
                        severity = random.uniform(1.0, 3.0)
                        
                    payout_triggered = severity >= 3.0
                    
                    adapted = SimulatedOracleEvent(
                        event_id=f"real_{rd.record_id_original or rd.id}_{uuid.uuid4().hex[:6]}",
                        token_id=f"tok_{uuid.uuid4().hex[:8]}",
                        municipio=rd.municipio,
                        uf=rd.uf,
                        latitude=rd.latitude,
                        longitude=rd.longitude,
                        disaster_type=rd.tipo_desastre,
                        severity_score=round(severity, 2),
                        ndvi=round(random.uniform(0.1, 0.4) if 'seca' in str(rd.tipo_desastre).lower() else random.uniform(0.2, 0.8), 3),
                        soil_moisture=round(random.uniform(0.1, 0.3) if 'seca' in str(rd.tipo_desastre).lower() else random.uniform(0.3, 0.7), 3),
                        timestamp=rd.data_inicio or datetime.now(),
                        payout_triggered=payout_triggered,
                        payout_percentage=round(min(1.0, (severity - 3.0) / 2.0 + 0.25) if payout_triggered else 0.0, 2),
                        payout_amount=round((min(1.0, (severity - 3.0) / 2.0 + 0.25) if payout_triggered else 0.0) * 100000.0, 2),
                        blockchain_tx_id=None,
                        status='PENDING' if not payout_triggered else 'TRIGGERED'
                    )
                    db_events.append(adapted)
            except Exception as e:
                logger.warning(f"Failed to fetch real Oracle events from DB: {e}")
        
        # Fallback to in-memory events if DB is empty or failed
        if not db_events:
            if not self.events:
                self._generate_initial_events()
            sorted_events = sorted(self.events, key=lambda e: e.timestamp, reverse=True)
            db_events = sorted_events[:limit]
            
        result_list = []
        for e in db_events:
            # Check if it's a DB model or a local dataclass
            if hasattr(e, '__tablename__'):
                result_list.append({
                    'event_id': e.event_id,
                    'token_id': e.token_id,
                    'municipio': e.municipio,
                    'uf': e.uf,
                    'latitude': e.latitude,
                    'longitude': e.longitude,
                    'disaster_type': e.disaster_type,
                    'severity_score': e.severity_score,
                    'ndvi': e.ndvi,
                    'soil_moisture': e.soil_moisture,
                    'timestamp': e.created_at.isoformat() if e.created_at else "",
                    'payout_triggered': e.payout_triggered,
                    'payout_percentage': e.payout_percentage,
                    'payout_amount': float(e.payout_amount) if e.payout_amount else 0.0,
                    'blockchain_tx_id': e.blockchain_tx_id,
                    'status': e.status,
                })
            else:
                result_list.append({
                    'event_id': e.event_id,
                    'token_id': e.token_id,
                    'municipio': e.municipio,
                    'uf': e.uf,
                    'latitude': e.latitude,
                    'longitude': e.longitude,
                    'disaster_type': e.disaster_type,
                    'severity_score': e.severity_score,
                    'ndvi': e.ndvi,
                    'soil_moisture': e.soil_moisture,
                    'timestamp': e.timestamp.isoformat(),
                    'payout_triggered': e.payout_triggered,
                    'payout_percentage': e.payout_percentage,
                    'payout_amount': e.payout_amount,
                    'blockchain_tx_id': e.blockchain_tx_id,
                    'status': e.status,
                })
        
        # ── News Crawler Integration ─────────────────────────────────────
        # Inject high-confidence news alerts as Oracle events (multi-source)
        try:
            from services.news_crawler_service import get_news_crawler_service
            crawler = get_news_crawler_service()
            news_events = crawler.get_oracle_events(min_severity='media', min_confidence=0.2)
            
            # Deduplicate: avoid adding news events that match existing DB events
            existing_ids = {e['event_id'] for e in result_list}
            for ne in news_events:
                if ne['event_id'] not in existing_ids:
                    result_list.append(ne)
            
            if news_events:
                logger.info(f"📰 Injected {len(news_events)} news-based events into Oracle pipeline")
        except Exception as e:
            logger.warning(f"News crawler integration skipped: {e}")
        
        # ── Climate Data Service Integration (Open-Meteo + CEMADEN + Embrapa) ──
        try:
            from services.climate_data_service import get_climate_data_service
            climate_svc = get_climate_data_service()
            climate_events = climate_svc.get_oracle_events()
            
            existing_ids = {e['event_id'] for e in result_list}
            injected = 0
            for ce in climate_events:
                if ce['event_id'] not in existing_ids:
                    result_list.append(ce)
                    injected += 1
            
            if injected:
                logger.info(f"🌤️ Injected {injected} climate events (Open-Meteo/CEMADEN) into Oracle pipeline")
        except Exception as e:
            logger.warning(f"Climate data integration skipped: {e}")
        
        # Sort all events by timestamp (newest first)
        result_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return result_list[:limit]

    def get_portfolio_risk(self) -> Dict[str, Any]:
        """
        Obter análise de risco de portfólio (simulado)
        
        Returns:
            Dados de risco do portfólio
        """
        # Calcular métricas
        total_exposure = sum(100000 for _ in self.events)  # R$ 100k por apólice
        impacted_policies = [e for e in self.events if e.payout_triggered]
        potential_payout = sum(e.payout_amount for e in impacted_policies)
        
        # Contar alertas por severidade
        high_severity = len([e for e in self.events if e.severity_score >= 4.0])
        medium_severity = len([e for e in self.events if 3.0 <= e.severity_score < 4.0])
        low_severity = len([e for e in self.events if e.severity_score < 3.0])
        
        return {
            'summary': {
                'total_exposure': total_exposure,
                'potential_payout': potential_payout,
                'impacted_policies_count': len(impacted_policies),
                'total_alerts': len(self.events),
                'high_severity_count': high_severity,
                'medium_severity_count': medium_severity,
                'low_severity_count': low_severity,
            },
            'impacted_policies': [
                {
                    'policy_id': e.token_id,
                    'policy_number': f"POL-{e.token_id[-6:].upper()}",
                    'location': f"{e.municipio}/{e.uf}",
                    'disaster_type': e.disaster_type,
                    'severity': 'HIGH' if e.severity_score >= 4.0 else 'MEDIUM' if e.severity_score >= 3.0 else 'LOW',
                    'potential_payout': e.payout_amount,
                }
                for e in impacted_policies
            ],
            'blockchain_transactions': [
                {
                    'tx_id': tx.tx_id,
                    'amount': tx.amount,
                    'confirmations': tx.confirmations,
                    'status': tx.status,
                }
                for tx in self.transactions[-5:]  # Últimas 5 transações
            ],
            'timestamp': datetime.now().isoformat(),
        }

    def get_oracle_status(self) -> Dict[str, Any]:
        """
        Obter status do Oracle (simulado)
        
        Returns:
            Status do serviço Oracle
        """
        return {
            'status': 'healthy',
            'mode': 'SIMULATION',
            'total_events_processed': len(self.events),
            'total_payouts_triggered': len([e for e in self.events if e.payout_triggered]),
            'total_blockchain_transactions': len(self.transactions),
            'last_update': self._last_update.isoformat(),
            'network': 'Hathor Testnet (Simulated)',
            'contract_address': '0x' + hashlib.md5(b'climate_oracle', usedforsecurity=False).hexdigest(),
        }

    async def trigger_new_event(self, db: Any) -> Dict[str, Any]:
        """
        Triggerar novo evento simulado (para demonstração) e persisti-lo no BD.
        
        Returns:
            Novo evento gerado
        """
        from models.sqlalchemy_models import OracleEvent, BlockchainTransaction
        
        # Selecionar município
        municipio = random.choice(self.HIGH_RISK_MUNICIPALITIES)
        
        # Gerar evento em memória
        event_data = self._generate_event(municipio)
        self.events.insert(0, event_data)  # Adicionar no início local
        
        import os
        if os.getenv("DATABASE_ENABLED", "true").lower() == "true":
            # Persistir o evento no banco de dados
            db_event = OracleEvent(
                event_id=event_data.event_id,
                token_id=event_data.token_id,
                municipio=event_data.municipio,
                uf=event_data.uf,
                latitude=event_data.latitude,
                longitude=event_data.longitude,
                disaster_type=event_data.disaster_type,
                severity_score=event_data.severity_score,
                ndvi=event_data.ndvi,
                soil_moisture=event_data.soil_moisture,
                payout_triggered=event_data.payout_triggered,
                payout_percentage=event_data.payout_percentage,
                payout_amount=event_data.payout_amount,
                blockchain_tx_id=event_data.blockchain_tx_id,
                status=event_data.status
            )
            db.add(db_event)
            
            if event_data.payout_triggered:
                # Save the transaction as well
                db_tx = BlockchainTransaction(
                    tx_hash=event_data.blockchain_tx_id,
                    token_uid=self.SIMULATED_TOKENS['CLMT']['uid'],
                    from_address='0x' + hashlib.md5(b'oracle', usedforsecurity=False).hexdigest(),
                    to_address='0x' + hashlib.md5(event_data.uf.encode(), usedforsecurity=False).hexdigest(),
                    amount=event_data.payout_amount,
                    block_height=random.randint(1000000, 2000000),
                    confirmations=random.randint(6, 100),
                    status='CONFIRMED'
                )
                db.add(db_tx)
    
            try:
                await db.commit()
                logger.info(f"Persisted new simulated event: {event_data.event_id}")
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to persist Oracle event: {e}")
        
        return asdict(event_data)


# Instância global
atlas_oracle_simulation = AtlasOracleSimulationService()
