"""
Atlas Digital de Desastres Service
Serviço para download, processamento e análise de dados do Atlas Digital de Desastres Naturais

Fontes:
- Atlas Digital de Desastres Naturais do Brasil (1991-2024)
- MDR - Ministério do Desenvolvimento Regional
- IBGE - Geocódigos de municípios

Integração:
- PostgreSQL para persistência de dados
- Georreferenciamento com coordenadas IBGE
"""

import logging
import os
import io
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import asyncio

import requests
import pandas as pd
import numpy as np

from config.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AtlasDisasterRecord:
    """Registro individual de desastre do Atlas"""
    record_id: str
    ano: int
    uf: str
    municipio: str
    codigo_municipio: Optional[str]
    tipo_desastre: str
    subtipo_desastre: Optional[str]
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    intensidade: Optional[str]
    mortes_diretas: int = 0
    mortes_indiretas: int = 0
    feridos: int = 0
    desabrigados: int = 0
    desalojados: int = 0
    afetados: int = 0
    prejuizo_estimado: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class AtlasAggregation:
    """Agregação de dados do Atlas"""
    grupo: Dict[str, Any]
    qtd_ocorrencias: int
    total_mortes: int
    total_afetados: int
    total_prejuizo: float
    municipios_atingidos: List[str] = field(default_factory=list)
    anos_ocorrencia: List[int] = field(default_factory=list)


class AtlasDisasterService:
    """
    Serviço para integração com o Atlas Digital de Desastres Naturais
    """

    # URLs padrão (usar configuração ou URL real do MDR)
    DEFAULT_DATA_URL = settings.ATLAS_DATA_URL
    
    # Coordenadas aproximadas de municípios brasileiros (para georreferenciamento básico)
    MUNICIPIOS_GEOCODE = {
        # Capitais e principais cidades
        ('São Paulo', 'SP'): (-23.5505, -46.6333),
        ('Rio de Janeiro', 'RJ'): (-22.9068, -43.1729),
        ('Brasília', 'DF'): (-15.7801, -47.9292),
        ('Salvador', 'BA'): (-12.9714, -38.5014),
        ('Fortaleza', 'CE'): (-3.7319, -38.5267),
        ('Belo Horizonte', 'MG'): (-19.9167, -43.9345),
        ('Manaus', 'AM'): (-3.1190, -60.0217),
        ('Curitiba', 'PR'): (-25.4284, -49.2733),
        ('Recife', 'PE'): (-8.0476, -34.8770),
        ('Porto Alegre', 'RS'): (-30.0346, -51.2177),
        ('Belém', 'PA'): (-1.4558, -48.5039),
        ('Goiânia', 'GO'): (-16.6869, -49.2648),
        ('Guarulhos', 'SP'): (-23.4538, -46.5333),
        ('Campinas', 'SP'): (-22.9099, -47.0626),
        ('São Luís', 'MA'): (-2.5387, -44.2825),
        ('São Gonçalo', 'RJ'): (-22.8268, -43.0539),
        ('Maceió', 'AL'): (-9.6658, -35.7353),
        ('Duque de Caxias', 'RJ'): (-22.7858, -43.3054),
        ('Natal', 'RN'): (-5.7945, -35.2110),
        ('Teresina', 'PI'): (-5.0892, -42.8019),
        ('Campo Grande', 'MS'): (-20.4697, -54.6201),
        ('Nova Iguaçu', 'RJ'): (-22.7592, -43.4511),
        ('São Bernardo do Campo', 'SP'): (-23.6914, -46.5647),
        ('João Pessoa', 'PB'): (-7.1195, -34.8450),
        ('Santo André', 'SP'): (-23.6636, -46.5341),
        ('Osasco', 'SP'): (-23.5329, -46.7919),
        ('Jaboatão dos Guararapes', 'PE'): (-8.1130, -35.0148),
        ('São José dos Campos', 'SP'): (-23.1791, -45.8872),
        ('Ribeirão Preto', 'SP'): (-21.1704, -47.8103),
        ('Uberlândia', 'MG'): (-18.9189, -48.2772),
        ('Contagem', 'MG'): (-19.9320, -44.0538),
        ('Sorocaba', 'SP'): (-23.5015, -47.4526),
        ('Aracaju', 'SE'): (-10.9472, -37.0731),
        ('Feira de Santana', 'BA'): (-12.2664, -38.9663),
        ('Cuiabá', 'MT'): (-15.6014, -56.0979),
        ('Joinville', 'SC'): (-26.3045, -48.8487),
        ('Juiz de Fora', 'MG'): (-21.7642, -43.3502),
        ('Londrina', 'PR'): (-23.3045, -51.1696),
        ('Aparecida de Goiânia', 'GO'): (-16.8239, -49.2439),
        ('Niterói', 'RJ'): (-22.8833, -43.1036),
        ('Ananindeua', 'PA'): (-1.3656, -48.3722),
        ('Porto Velho', 'RO'): (-8.7619, -63.9039),
        ('Florianópolis', 'SC'): (-27.5954, -48.5480),
        ('Serra', 'ES'): (-20.1289, -40.3078),
        ('Caxias do Sul', 'RS'): (-29.1678, -51.1794),
        ('Vila Velha', 'ES'): (-20.3297, -40.2925),
        ('Macapá', 'AP'): (0.0389, -51.0664),
        ('Mauá', 'SP'): (-23.6678, -46.4612),
        ('São João de Meriti', 'RJ'): (-22.8042, -43.3722),
        ('Santos', 'SP'): (-23.9608, -46.3336),
        ('Mogi das Cruzes', 'SP'): (-23.5228, -46.1867),
        ('Betim', 'MG'): (-19.9681, -44.1983),
        ('Campina Grande', 'PB'): (-7.2306, -35.8811),
        ('Olinda', 'PE'): (-8.0089, -34.8553),
        ('Carapicuíba', 'SP'): (-23.5225, -46.8356),
        ('Piracicaba', 'SP'): (-22.7253, -47.6492),
        ('Cariacica', 'ES'): (-20.2619, -40.4175),
        ('Bauru', 'SP'): (-22.3147, -49.0608),
        ('Montes Claros', 'MG'): (-16.7350, -43.8619),
        ('Vitória', 'ES'): (-20.3155, -40.3128),
        ('Pelotas', 'RS'): (-31.7654, -52.3376),
        ('Canoas', 'RS'): (-29.9178, -51.1836),
        ('Cascavel', 'PR'): (-24.9558, -53.4552),
        ('Ponta Grossa', 'PR'): (-25.0916, -50.1668),
        ('Blumenau', 'SC'): (-26.9194, -49.0661),
        ('Caruaru', 'PE'): (-8.2839, -35.9761),
        ('Rio Branco', 'AC'): (-9.9747, -67.8243),
        ('Boa Vista', 'RR'): (2.8235, -60.6758),
        ('Palmas', 'TO'): (-10.1689, -48.3317),
    }
    
    # Mapeamento de tipos de desastres
    DISASTER_TYPE_MAPPING = {
        'inundacao': ['inundação', 'inundacao', 'enchente', 'alagamento'],
        'seca': ['seca', 'estiagem', 'secas'],
        'deslizamento': ['deslizamento', 'movimento de massa', 'rolagem de barro'],
        'granizo': ['granizo', 'queda de granizo'],
        'vendaval': ['vendaval', 'vento forte', 'ciclone', 'tornado'],
        'incendio': ['incêndio', 'incendio', 'queimada'],
        'geada': ['geada', 'granizo'],
        'aluviao': ['aluviao', 'aluviação', 'enxurrada'],
    }

    def __init__(self, data_dir: Optional[str] = None, use_database: bool = True):
        """
        Inicializar serviço do Atlas
        
        Args:
            data_dir: Diretório para armazenar dados baixados
            use_database: Usar banco de dados se disponível
        """
        if data_dir is None:
            data_dir = settings.ATLAS_DATA_DIR
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_database = use_database and settings.ATLAS_DB_ENABLED
        self._db_service = None
        
        # Import lazy do database service
        if self.use_database:
            try:
                from services.atlas_database_service import atlas_db_service
                self._db_service = atlas_db_service
                logger.info("AtlasDatabaseService disponível")
            except Exception as e:
                logger.warning(f"AtlasDatabaseService não disponível: {e}")
                self.use_database = False
        
        self._cache: Optional[pd.DataFrame] = None
        self._cache_timestamp: Optional[datetime] = None
        self._loaded_file: Optional[str] = None
        
        logger.info(f"AtlasDisasterService initialized with data_dir: {self.data_dir}")

    def download_data(
        self,
        url: str,
        filename: Optional[str] = None,
        force: bool = False
    ) -> str:
        """
        Fazer download do arquivo de dados do Atlas
        
        Args:
            url: URL do arquivo (CSV ou Excel)
            filename: Nome do arquivo para salvar
            force: Forçar download mesmo se arquivo existir
            
        Returns:
            Caminho do arquivo salvo
            
        Raises:
            requests.RequestException: Erro no download
            ValueError: URL inválida
        """
        if not url or url == self.DEFAULT_DATA_URL:
            msg = "URL de dados não configurada. Atualize DATA_URL nas configurações."
            logger.error(msg)
            raise ValueError(msg)
        
        if filename is None:
            filename = f"atlas_desastres_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.data_dir / filename
        
        # Verificar se já existe
        if filepath.exists() and not force:
            logger.info(f"Arquivo já existe: {filepath}")
            return str(filepath)
        
        logger.info(f"Baixando dados do Atlas a partir de: {url}")
        
        try:
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(resp.content)
            
            logger.info(f"Arquivo salvo em: {filepath} ({len(resp.content)} bytes)")
            return str(filepath)
            
        except requests.RequestException as e:
            logger.error(f"Erro no download: {e}")
            raise

    def load_data(
        self,
        filepath: Optional[str] = None,
        url: Optional[str] = None,
        use_cache: bool = True,
        cache_timeout_minutes: int = 60
    ) -> pd.DataFrame:
        """
        Carregar dados do Atlas em DataFrame
        
        Args:
            filepath: Caminho do arquivo local
            url: URL para download se arquivo não existir
            use_cache: Usar cache se disponível
            cache_timeout_minutes: Tempo de validade do cache
            
        Returns:
            DataFrame com dados normalizados
            
        Raises:
            FileNotFoundError: Arquivo não encontrado
            pd.errors.EmptyDataError: Arquivo vazio
        """
        # Verificar cache
        if use_cache and self._cache is not None and self._cache_timestamp:
            cache_age = datetime.now() - self._cache_timestamp
            if cache_age.total_seconds() < cache_timeout_minutes * 60:
                logger.info(f"Usando cache ({len(self._cache)} registros)")
                return self._cache.copy()
        
        # Determinar origem dos dados
        if filepath is None and url is not None:
            filepath = self.download_data(url)
        
        if filepath is None:
            # Tentar encontrar arquivo mais recente
            files = list(self.data_dir.glob("atlas_desastres_*.csv")) + \
                    list(self.data_dir.glob("atlas_desastres_*.xlsx"))
            if files:
                filepath = str(max(files, key=lambda p: p.stat().st_mtime))
                logger.info(f"Usando arquivo mais recente: {filepath}")
            else:
                msg = "Nenhum arquivo do Atlas encontrado. Forneça filepath ou url."
                logger.error(msg)
                raise FileNotFoundError(msg)
        
        # Carregar arquivo
        logger.info(f"Carregando arquivo: {filepath}")
        df = self._load_file(filepath)
        
        # Normalizar colunas
        df = self._normalize_columns(df)
        
        # Criar aliases
        df = self._create_column_aliases(df)
        
        # Atualizar cache
        self._cache = df.copy()
        self._cache_timestamp = datetime.now()
        self._loaded_file = filepath
        
        logger.info(f"Dados carregados: {len(df)} registros, {len(df.columns)} colunas")
        return df

    def _load_file(self, filepath: str) -> pd.DataFrame:
        """Carregar arquivo CSV ou Excel"""
        ext = Path(filepath).suffix.lower()
        
        try:
            if ext in ['.xls', '.xlsx']:
                df = pd.read_excel(filepath)
            elif ext == '.csv':
                # Tentar diferentes separadores e encodings
                for sep in [';', ',', '\t']:
                    for encoding in ['utf-8', 'latin1', 'cp1252']:
                        try:
                            df = pd.read_csv(filepath, sep=sep, encoding=encoding)
                            return df
                        except (pd.errors.ParserError, UnicodeDecodeError):
                            continue
                raise ValueError(f"Não foi possível ler CSV com separadores/encodings padrão")
            else:
                raise ValueError(f"Formato não suportado: {ext}")
            
            return df
            
        except pd.errors.EmptyDataError:
            logger.error(f"Arquivo vazio: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {filepath}: {str(e)}", exc_info=True)
            raise

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar nomes de colunas"""
        # Criar mapeamento de colunas originais para normalizadas
        column_mapping = {}
        
        for col in df.columns:
            normalized = (
                str(col)
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("ç", "c")
                .replace("ã", "a")
                .replace("á", "a")
                .replace("é", "e")
                .replace("í", "i")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("ê", "e")
                .replace("ô", "o")
            )
            column_mapping[col] = normalized
        
        df = df.rename(columns=column_mapping)
        
        # Remover duplicatas mantendo a primeira ocorrência
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        
        return df

    def _create_column_aliases(self, df: pd.DataFrame) -> pd.DataFrame:
        """Criar aliases para colunas comuns"""
        # Mapeamento de possíveis nomes de colunas
        year_cols = ['ano', 'year', 'data_ano', 'ano_ocorrencia']
        uf_cols = ['uf', 'estado', 'sigla_uf', 'uf_codigo']
        mun_cols = ['municipio', 'municip', 'nome_municipio', 'cidade']
        tipo_cols = ['tipo_desastre', 'tipo', 'desastre_tipo', 'categoria']
        
        for col in year_cols:
            if col in df.columns and 'ano' not in df.columns:
                df['ano'] = df[col]
                break
        
        for col in uf_cols:
            if col in df.columns and 'uf' not in df.columns:
                df['uf'] = df[col].str.upper().str.strip()
                break
        
        for col in mun_cols:
            if col in df.columns and 'municipio' not in df.columns:
                df['municipio'] = df[col]
                break
        
        for col in tipo_cols:
            if col in df.columns and 'tipo_desastre' not in df.columns:
                df['tipo_desastre'] = df[col]
                break

        return df

    def geocode_municipio(
        self,
        municipio: str,
        uf: str,
    ) -> Optional[Tuple[float, float]]:
        """
        Obter coordenadas de município
        
        Args:
            municipio: Nome do município
            uf: Sigla da UF
            
        Returns:
            Tupla (latitude, longitude) ou None
        """
        # Normalizar nome
        municipio_norm = municipio.strip().title()
        uf_norm = uf.upper().strip()
        
        # Tentar cache local primeiro
        key = (municipio_norm, uf_norm)
        if key in self.MUNICIPIOS_GEOCODE:
            return self.MUNICIPIOS_GEOCODE[key]
        
        # Tentar busca parcial
        for (mun, u), coords in self.MUNICIPIOS_GEOCODE.items():
            if u == uf_norm and municipio_norm.lower() in mun.lower():
                return coords
        
        # Se banco de dados estiver disponível, tentar buscar lá
        if self.use_database and self._db_service:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            
            if loop:
                # Em ambiente async
                pass
            else:
                # Ambiente síncrono - criar novo loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            try:
                geocode_data = loop.run_until_complete(
                    self._db_service.get_municipio_geocode(municipio_norm, uf_norm)
                )
                if geocode_data:
                    coords = (geocode_data['latitude'], geocode_data['longitude'])
                    # Adicionar ao cache local
                    self.MUNICIPIOS_GEOCODE[key] = coords
                    return coords
            except Exception as e:
                logger.debug(f"Erro ao buscar geocódigo no DB: {e}")
        
        return None

    def add_geocode_to_dataframe(
        self,
        df: pd.DataFrame,
        batch_size: int = 1000
    ) -> pd.DataFrame:
        """
        Adicionar coordenadas a DataFrame
        
        Args:
            df: DataFrame com colunas 'municipio' e 'uf'
            batch_size: Tamanho do lote para processamento
            
        Returns:
            DataFrame com colunas 'latitude' e 'longitude' adicionadas
        """
        if 'municipio' not in df.columns or 'uf' not in df.columns:
            logger.warning("Colunas 'municipio' ou 'uf' não encontradas")
            return df
        
        # Inicializar colunas
        df = df.copy()
        df['latitude'] = np.nan
        df['longitude'] = np.nan
        
        # Processar em lotes
        for idx, row in df.iterrows():
            coords = self.geocode_municipio(row['municipio'], row['uf'])
            if coords:
                df.at[idx, 'latitude'] = coords[0]
                df.at[idx, 'longitude'] = coords[1]
        
        geocoded_count = df['latitude'].notna().sum()
        logger.info(f"Geocodificados {geocoded_count}/{len(df)} municípios")
        
        return df

    async def persist_to_database(
        self,
        df: pd.DataFrame,
        batch_size: int = 1000
    ) -> int:
        """
        Persistir dados no banco de dados
        
        Args:
            df: DataFrame com dados do Atlas
            batch_size: Tamanho do lote para inserção
            
        Returns:
            Número de registros inseridos
        """
        if not self.use_database or not self._db_service:
            logger.info("Banco de dados não disponível. Persistência ignorada.")
            return 0
        
        # Converter DataFrame para lista de dicionários
        records = df.to_dict(orient='records')
        
        try:
            inserted = await self._db_service.insert_disasters(
                disasters=records,
                batch_size=batch_size
            )
            logger.info(f"Persistidos {inserted} registros no banco de dados")
            return inserted
        except Exception as e:
            logger.error(f"Erro ao persistir no banco de dados: {e}")
            return 0

    def save_geocode_to_database(
        self,
        municipio: str,
        uf: str,
        latitude: float,
        longitude: float,
        codigo_ibge: Optional[str] = None,
    ):
        """
        Salvar geocódigo no banco de dados
        
        Args:
            municipio: Nome do município
            uf: Sigla da UF
            latitude: Latitude
            longitude: Longitude
            codigo_ibge: Código IBGE do município
        """
        if not self.use_database or not self._db_service:
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(
                self._db_service.upsert_municipio_geocode(
                    codigo_ibge=codigo_ibge or f"{uf}_{municipio}",
                    municipio=municipio,
                    uf=uf,
                    latitude=latitude,
                    longitude=longitude,
                )
            )
        except Exception as e:
            logger.debug(f"Erro ao salvar geocódigo: {e}")

    def filter_disasters(
        self,
        df: pd.DataFrame,
        anos: Optional[Tuple[int, int]] = None,
        uf: Optional[str] = None,
        municipio: Optional[str] = None,
        tipo_desastre: Optional[str] = None,
        intensidade: Optional[str] = None,
        min_afetados: Optional[int] = None,
        min_mortes: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Filtrar dados de desastres
        
        Args:
            df: DataFrame completo
            anos: Tupla (ano_inicial, ano_final)
            uf: Sigla da UF (ex: 'RS')
            municipio: Nome do município
            tipo_desastre: Tipo de desastre (suporta busca parcial)
            intensidade: Nível de intensidade
            min_afetados: Mínimo de pessoas afetadas
            min_mortes: Mínimo de mortes
            
        Returns:
            DataFrame filtrado
        """
        mask = pd.Series(True, index=df.index)
        
        # Filtro por ano
        if anos is not None and 'ano' in df.columns:
            a0, a1 = anos
            mask &= (df['ano'] >= a0) & (df['ano'] <= a1)
        
        # Filtro por UF
        if uf is not None and 'uf' in df.columns:
            mask &= df['uf'].str.upper() == uf.upper().strip()
        
        # Filtro por município
        if municipio is not None and 'municipio' in df.columns:
            mask &= df['municipio'].str.upper().str.contains(municipio.upper().strip())
        
        # Filtro por tipo de desastre
        if tipo_desastre is not None and 'tipo_desastre' in df.columns:
            # Verificar se é um tipo mapeado
            tipo_lower = tipo_desastre.lower()
            if tipo_lower in self.DISASTER_TYPE_MAPPING:
                termos = self.DISASTER_TYPE_MAPPING[tipo_lower]
                tipo_mask = pd.Series(False, index=df.index)
                for termo in termos:
                    tipo_mask |= df['tipo_desastre'].str.upper().str.contains(termo.upper())
                mask &= tipo_mask
            else:
                mask &= df['tipo_desastre'].str.upper().str.contains(tipo_desastre.upper().strip())
        
        # Filtro por intensidade
        if intensidade is not None and 'intensidade' in df.columns:
            mask &= df['intensidade'].str.upper() == intensidade.upper().strip()
        
        # Filtro por mínimo de afetados
        if min_afetados is not None and 'afetados' in df.columns:
            mask &= df['afetados'] >= min_afetados
        
        # Filtro por mínimo de mortes
        if min_mortes is not None:
            col_mortes = 'mortes_diretas' if 'mortes_diretas' in df.columns else 'mortes'
            if col_mortes in df.columns:
                mask &= df[col_mortes] >= min_mortes
        
        return df[mask].copy()

    def aggregate_by_municipality(
        self,
        df: pd.DataFrame,
        group_cols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Agregar dados por município e outros grupos
        
        Args:
            df: DataFrame com dados
            group_cols: Colunas para agrupamento
            
        Returns:
            DataFrame agregado
        """
        if group_cols is None:
            group_cols = ['uf', 'municipio', 'tipo_desastre']
        
        # Filtrar colunas existentes
        valid_cols = [c for c in group_cols if c in df.columns]
        
        if not valid_cols:
            raise ValueError("Nenhuma coluna válida para agregação")
        
        # Colunas numéricas para agregação
        agg_dict = {'size': 'qtd_ocorrencias'}
        
        numeric_cols = []
        for col in ['mortes_diretas', 'mortes_indiretas', 'afetados', 'desabrigados', 'desalojados', 'prejuizo_estimado']:
            if col in df.columns:
                numeric_cols.append(col)
                agg_dict[col] = 'sum'
        
        agg_result = df.groupby(valid_cols).agg(
            qtd_ocorrencias=('ano', 'size'),
            **{col: (col, 'sum') for col in numeric_cols}
        ).reset_index()
        
        # Ordenar por ocorrências
        agg_result = agg_result.sort_values('qtd_ocorrencias', ascending=False)
        
        return agg_result

    def aggregate_by_year(
        self,
        df: pd.DataFrame,
        group_by_uf: bool = False
    ) -> pd.DataFrame:
        """
        Agregar dados por ano
        
        Args:
            df: DataFrame com dados
            group_by_uf: Incluir agrupamento por UF
            
        Returns:
            DataFrame agregado por ano
        """
        if 'ano' not in df.columns:
            raise ValueError("Coluna 'ano' não encontrada")
        
        group_cols = ['ano']
        if group_by_uf and 'uf' in df.columns:
            group_cols.append('uf')
        
        agg_dict = {
            'qtd_ocorrencias': ('ano', 'size'),
        }
        
        # Adicionar colunas numéricas
        for col in ['mortes_diretas', 'afetados', 'desabrigados', 'prejuizo_estimado']:
            if col in df.columns:
                agg_dict[col.replace('_diretas', '')] = (col, 'sum')
        
        agg_result = df.groupby(group_cols).agg(**agg_dict).reset_index()
        agg_result = agg_result.sort_values('ano')
        
        return agg_result

    def get_statistics(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calcular estatísticas descritivas
        
        Args:
            df: DataFrame com dados
            
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_registros': len(df),
            'periodo': {},
            'uf': {},
            'tipos_desastre': {},
            'impacto': {},
        }
        
        # Período
        if 'ano' in df.columns:
            stats['periodo'] = {
                'inicio': int(df['ano'].min()),
                'fim': int(df['ano'].max()),
                'anos_unicos': int(df['ano'].nunique()),
            }
        
        # Por UF
        if 'uf' in df.columns:
            stats['uf'] = {
                'total_estados': int(df['uf'].nunique()),
                'mais_afetado': df.groupby('uf').size().idxmax() if len(df) > 0 else None,
            }
        
        # Por tipo de desastre
        if 'tipo_desastre' in df.columns:
            tipo_counts = df['tipo_desastre'].value_counts()
            stats['tipos_desastre'] = {
                'total_tipos': int(tipo_counts.shape[0]),
                'mais_comum': tipo_counts.index[0] if len(tipo_counts) > 0 else None,
                'top_5': tipo_counts.head(5).to_dict(),
            }
        
        # Impacto
        impacto_cols = ['mortes_diretas', 'afetados', 'desabrigados', 'prejuizo_estimado']
        for col in impacto_cols:
            if col in df.columns:
                stats['impacto'][col] = {
                    'total': df[col].sum(),
                    'media': float(df[col].mean()) if len(df) > 0 else 0,
                    'max': df[col].max(),
                }
        
        return stats

    def export_to_csv(
        self,
        df: pd.DataFrame,
        filename: str,
        include_timestamp: bool = True
    ) -> str:
        """
        Exportar DataFrame para CSV
        
        Args:
            df: DataFrame para exportar
            filename: Nome do arquivo
            include_timestamp: Adicionar timestamp ao nome
            
        Returns:
            Caminho do arquivo salvo
        """
        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
        
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Arquivo exportado: {filepath}")
        return str(filepath)

    def clear_cache(self):
        """Limpar cache de dados"""
        self._cache = None
        self._cache_timestamp = None
        logger.info("Cache limpo")
