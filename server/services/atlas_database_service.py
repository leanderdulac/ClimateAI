"""
Atlas Database Service
Serviço para persistência de dados do Atlas em PostgreSQL
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from contextlib import asynccontextmanager

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from models.sqlalchemy_models import AtlasDisaster, AtlasMunicipioGeocode
from config.config import settings

logger = logging.getLogger(__name__)


class AtlasDatabaseService:
    """
    Serviço para operações de banco de dados do Atlas
    """

    def __init__(self):
        """Inicializar serviço de banco de dados"""
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
        
        if settings.ATLAS_DB_ENABLED and settings.DATABASE_URL:
            self._init_engine()

    def _init_engine(self):
        """Inicializar engine do banco de dados"""
        try:
            db_url = settings.DATABASE_URL
            engine_kwargs = {"pool_pre_ping": True}
            
            if db_url and "asyncpg" in db_url:
                separator = "&" if "?" in db_url else "?"
                if "prepared_statement_cache_size" not in db_url:
                    db_url += f"{separator}prepared_statement_cache_size=0"
                separator = "&"
                if "statement_cache_size" not in db_url:
                    db_url += f"{separator}statement_cache_size=0"

                engine_kwargs["pool_size"] = 10
                engine_kwargs["max_overflow"] = 20

            self.engine = create_async_engine(
                db_url,
                **engine_kwargs,
            )
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            self._initialized = True
            logger.info("AtlasDatabaseService initialized")
        except Exception as e:
            logger.error(f"Erro ao inicializar AtlasDatabaseService: {e}")
            self._initialized = False

    @asynccontextmanager
    async def get_session(self):
        """Obter sessão do banco de dados"""
        if not self._initialized:
            self._init_engine()
        
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized")
        
        session = self.async_session_maker()
        try:
            yield session
        finally:
            await session.close()

    async def insert_disasters(
        self,
        disasters: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        Inserir registros de desastres em lote
        
        Args:
            disasters: Lista de dicionários com dados dos desastres
            batch_size: Tamanho do lote para inserção
            
        Returns:
            Número de registros inseridos
        """
        if not self._initialized:
            logger.warning("Database não inicializado. Inserção ignorada.")
            return 0
        
        inserted = 0
        
        try:
            async with self.get_session() as session:
                for i in range(0, len(disasters), batch_size):
                    batch = disasters[i:i + batch_size]
                    
                    for data in batch:
                        # Converter datas
                        data_inicio = None
                        if data.get('data_inicio'):
                            try:
                                if isinstance(data['data_inicio'], str):
                                    data_inicio = datetime.strptime(
                                        data['data_inicio'], '%Y-%m-%d'
                                    ).date()
                                elif isinstance(data['data_inicio'], date):
                                    data_inicio = data['data_inicio']
                            except (ValueError, TypeError):
                                pass
                        
                        data_fim = None
                        if data.get('data_fim'):
                            try:
                                if isinstance(data['data_fim'], str):
                                    data_fim = datetime.strptime(
                                        data['data_fim'], '%Y-%m-%d'
                                    ).date()
                                elif isinstance(data['data_fim'], date):
                                    data_fim = data['data_fim']
                            except (ValueError, TypeError):
                                pass
                        
                        disaster = AtlasDisaster(
                            record_id_original=data.get('record_id_original'),
                            ano=data.get('ano', 0),
                            uf=data.get('uf', ''),
                            municipio=data.get('municipio', ''),
                            codigo_municipio=data.get('codigo_municipio'),
                            latitude=data.get('latitude'),
                            longitude=data.get('longitude'),
                            tipo_desastre=data.get('tipo_desastre', ''),
                            subtipo_desastre=data.get('subtipo_desastre'),
                            intensidade=data.get('intensidade'),
                            data_inicio=data_inicio,
                            data_fim=data_fim,
                            mortes_diretas=data.get('mortes_diretas', 0),
                            mortes_indiretas=data.get('mortes_indiretas', 0),
                            feridos=data.get('feridos', 0),
                            desabrigados=data.get('desabrigados', 0),
                            desalojados=data.get('desalojados', 0),
                            afetados=data.get('afetados', 0),
                            prejuizo_estimado=data.get('prejuizo_estimado'),
                            fonte=data.get('fonte', 'Atlas Digital MDR'),
                        )
                        session.add(disaster)
                    
                    await session.commit()
                    inserted += len(batch)
                    logger.info(f"Inseridos {inserted}/{len(disasters)} registros")
                    
        except Exception as e:
            logger.error(f"Erro ao inserir desastres: {e}")
            raise
        
        return inserted

    async def query_disasters(
        self,
        anos: Optional[Tuple[int, int]] = None,
        uf: Optional[str] = None,
        municipio: Optional[str] = None,
        tipo_desastre: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Consultar registros de desastres
        
        Args:
            anos: Tupla (ano_inicial, ano_final)
            uf: Sigla da UF
            municipio: Nome do município
            tipo_desastre: Tipo de desastre
            limit: Limite de registros
            offset: Offset para paginação
            
        Returns:
            Lista de dicionários com dados dos desastres
        """
        if not self._initialized:
            return []
        
        async with self.get_session() as session:
            query = select(AtlasDisaster)
            
            # Aplicar filtros
            conditions = []
            
            if anos:
                conditions.append(and_(
                    AtlasDisaster.ano >= anos[0],
                    AtlasDisaster.ano <= anos[1]
                ))
            
            if uf:
                conditions.append(AtlasDisaster.uf == uf.upper())
            
            if municipio:
                conditions.append(
                    AtlasDisaster.municipio.ilike(f"%{municipio}%")
                )
            
            if tipo_desastre:
                conditions.append(
                    AtlasDisaster.tipo_desastre.ilike(f"%{tipo_desastre}%")
                )
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Ordenar e paginar
            query = query.order_by(AtlasDisaster.ano.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            disasters = result.scalars().all()
            
            return [self._disaster_to_dict(d) for d in disasters]

    async def count_disasters(
        self,
        anos: Optional[Tuple[int, int]] = None,
        uf: Optional[str] = None,
        tipo_desastre: Optional[str] = None,
    ) -> int:
        """Contar registros de desastres com filtros"""
        if not self._initialized:
            return 0
        
        async with self.get_session() as session:
            query = select(func.count()).select_from(AtlasDisaster)
            
            conditions = []
            if anos:
                conditions.append(and_(
                    AtlasDisaster.ano >= anos[0],
                    AtlasDisaster.ano <= anos[1]
                ))
            if uf:
                conditions.append(AtlasDisaster.uf == uf.upper())
            if tipo_desastre:
                conditions.append(
                    AtlasDisaster.tipo_desastre.ilike(f"%{tipo_desastre}%")
                )
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar() or 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas gerais do banco de dados"""
        if not self._initialized:
            return {}
        
        async with self.get_session() as session:
            # Total de registros
            total_query = select(func.count()).select_from(AtlasDisaster)
            total = (await session.execute(total_query)).scalar() or 0
            
            # Período
            periodo_query = select(
                func.min(AtlasDisaster.ano),
                func.max(AtlasDisaster.ano)
            )
            periodo_result = await session.execute(periodo_query)
            periodo_row = periodo_result.first()
            
            # Top UF
            uf_query = select(
                AtlasDisaster.uf,
                func.count().label('qtd')
            ).group_by(AtlasDisaster.uf).order_by(
                func.count().desc()
            ).limit(1)
            uf_result = await session.execute(uf_query)
            uf_row = uf_result.first()
            
            # Top tipo
            tipo_query = select(
                AtlasDisaster.tipo_desastre,
                func.count().label('qtd')
            ).group_by(AtlasDisaster.tipo_desastre).order_by(
                func.count().desc()
            ).limit(1)
            tipo_result = await session.execute(tipo_query)
            tipo_row = tipo_result.first()
            
            # Totais de impacto
            impacto_query = select(
                func.sum(AtlasDisaster.mortes_diretas),
                func.sum(AtlasDisaster.afetados),
                func.sum(AtlasDisaster.prejuizo_estimado)
            )
            impacto_result = await session.execute(impacto_query)
            impacto_row = impacto_result.first()
            
            return {
                'total_registros': total,
                'periodo': {
                    'inicio': periodo_row[0] if periodo_row else None,
                    'fim': periodo_row[1] if periodo_row else None,
                },
                'uf': {
                    'mais_afetado': uf_row[0] if uf_row else None,
                    'qtd': uf_row[1] if uf_row else 0,
                },
                'tipos_desastre': {
                    'mais_comum': tipo_row[0] if tipo_row else None,
                    'qtd': tipo_row[1] if tipo_row else 0,
                },
                'impacto': {
                    'total_mortes': impacto_row[0] or 0,
                    'total_afetados': impacto_row[1] or 0,
                    'total_prejuizo': float(impacto_row[2] or 0),
                }
            }

    async def upsert_municipio_geocode(
        self,
        codigo_ibge: str,
        municipio: str,
        uf: str,
        latitude: float,
        longitude: float,
        populacao: Optional[int] = None,
        area_km2: Optional[float] = None,
    ) -> AtlasMunicipioGeocode:
        """
        Inserir ou atualizar geocódigo de município
        
        Args:
            codigo_ibge: Código IBGE do município
            municipio: Nome do município
            uf: Sigla da UF
            latitude: Latitude
            longitude: Longitude
            populacao: População do município
            area_km2: Área em km²
            
        Returns:
            Registro criado ou atualizado
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        async with self.get_session() as session:
            # Tentar buscar existente
            query = select(AtlasMunicipioGeocode).where(
                AtlasMunicipioGeocode.codigo_municipio_ibge == codigo_ibge
            )
            result = await session.execute(query)
            geocode = result.scalar_one_or_none()
            
            if geocode:
                # Atualizar
                geocode.latitude = latitude
                geocode.longitude = longitude
                if populacao:
                    geocode.populacao = populacao
                if area_km2:
                    geocode.area_km2 = area_km2
                geocode.updated_at = datetime.utcnow()
            else:
                # Inserir
                geocode = AtlasMunicipioGeocode(
                    codigo_municipio_ibge=codigo_ibge,
                    municipio=municipio,
                    uf=uf,
                    latitude=latitude,
                    longitude=longitude,
                    populacao=populacao,
                    area_km2=area_km2,
                )
                session.add(geocode)
            
            await session.commit()
            await session.refresh(geocode)
            
            return geocode

    async def get_municipio_geocode(
        self,
        municipio: str,
        uf: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Obter geocódigo de município
        
        Args:
            municipio: Nome do município
            uf: Sigla da UF
            
        Returns:
            Dicionário com coordenadas ou None
        """
        if not self._initialized:
            return None
        
        async with self.get_session() as session:
            query = select(AtlasMunicipioGeocode).where(
                and_(
                    AtlasMunicipioGeocode.municipio.ilike(f"{municipio}%"),
                    AtlasMunicipioGeocode.uf == uf.upper()
                )
            )
            result = await session.execute(query)
            geocode = result.scalar_one_or_none()
            
            if geocode:
                return {
                    'codigo_ibge': geocode.codigo_municipio_ibge,
                    'latitude': geocode.latitude,
                    'longitude': geocode.longitude,
                    'populacao': geocode.populacao,
                    'area_km2': geocode.area_km2,
                }
            return None

    def _disaster_to_dict(self, disaster: AtlasDisaster) -> Dict[str, Any]:
        """Converter modelo SQLAlchemy em dicionário"""
        return {
            'id': disaster.id,
            'record_id_original': disaster.record_id_original,
            'ano': disaster.ano,
            'uf': disaster.uf,
            'municipio': disaster.municipio,
            'codigo_municipio': disaster.codigo_municipio,
            'latitude': disaster.latitude,
            'longitude': disaster.longitude,
            'tipo_desastre': disaster.tipo_desastre,
            'subtipo_desastre': disaster.subtipo_desastre,
            'intensidade': disaster.intensidade,
            'data_inicio': disaster.data_inicio.isoformat() if disaster.data_inicio else None,
            'data_fim': disaster.data_fim.isoformat() if disaster.data_fim else None,
            'mortes_diretas': disaster.mortes_diretas,
            'mortes_indiretas': disaster.mortes_indiretas,
            'feridos': disaster.feridos,
            'desabrigados': disaster.desabrigados,
            'desalojados': disaster.desalojados,
            'afetados': disaster.afetados,
            'prejuizo_estimado': float(disaster.prejuizo_estimado) if disaster.prejuizo_estimado else None,
            'fonte': disaster.fonte,
        }


# Instância global
atlas_db_service = AtlasDatabaseService()
