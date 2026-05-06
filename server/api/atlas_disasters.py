"""
Atlas Digital de Desastres - API Router
Endpoints para acesso e análise de dados do Atlas Digital de Desastres Naturais
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body, status
from fastapi.responses import FileResponse
import pandas as pd

from models.schemas import (
    AtlasDisasterRecord,
    AtlasDisasterAggregation,
    AtlasStatistics,
    AtlasFilterRequest,
    AtlasDownloadRequest,
    AtlasDataStatus,
)
from services.atlas_disaster_service import AtlasDisasterService
from services.atlas_visualization_service import AtlasVisualizationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/atlas", tags=["atlas-disasters"])

# Instâncias globais dos serviços
atlas_service = AtlasDisasterService()
visualization_service = AtlasVisualizationService()


# ============================================================================
# Helper Functions
# ============================================================================

def _get_or_load_data() -> pd.DataFrame:
    """Carregar dados ou retornar erro se não disponíveis"""
    try:
        return atlas_service.load_data(use_cache=True)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Dados não encontrados",
                "message": str(e),
                "suggestion": "Faça upload ou download dos dados primeiro usando o endpoint /download"
            }
        )
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar dados: {str(e)}"
        )


def _record_to_dict(row: pd.Series) -> Dict[str, Any]:
    """Converter linha do DataFrame em dicionário"""
    return {
        'record_id': str(row.name) if hasattr(row, 'name') else '',
        'ano': int(row.get('ano', 0)),
        'uf': str(row.get('uf', '')),
        'municipio': str(row.get('municipio', '')),
        'codigo_municipio': row.get('codigo_municipio'),
        'tipo_desastre': str(row.get('tipo_desastre', '')),
        'subtipo_desastre': row.get('subtipo_desastre'),
        'data_inicio': str(row.get('data_inicio')) if pd.notna(row.get('data_inicio')) else None,
        'data_fim': str(row.get('data_fim')) if pd.notna(row.get('data_fim')) else None,
        'intensidade': row.get('intensidade'),
        'mortes_diretas': int(row.get('mortes_diretas', 0)) if pd.notna(row.get('mortes_diretas')) else 0,
        'mortes_indiretas': int(row.get('mortes_indiretas', 0)) if pd.notna(row.get('mortes_indiretas')) else 0,
        'feridos': int(row.get('feridos', 0)) if pd.notna(row.get('feridos')) else 0,
        'desabrigados': int(row.get('desabrigados', 0)) if pd.notna(row.get('desabrigados')) else 0,
        'desalojados': int(row.get('desalojados', 0)) if pd.notna(row.get('desalojados')) else 0,
        'afetados': int(row.get('afetados', 0)) if pd.notna(row.get('afetados')) else 0,
        'prejuizo_estimado': float(row.get('prejuizo_estimado')) if pd.notna(row.get('prejuizo_estimado')) else None,
        'latitude': float(row.get('latitude')) if pd.notna(row.get('latitude')) else None,
        'longitude': float(row.get('longitude')) if pd.notna(row.get('longitude')) else None,
    }


# ============================================================================
# API Endpoints - Gestão de Dados
# ============================================================================

@router.post("/download", response_model=Dict[str, str])
async def download_data(request: AtlasDownloadRequest):
    """
    Fazer download de dados do Atlas Digital
    
    **URLs suportadas:**
    - CSV direto do Atlas Digital MDR
    - Excel com dados de desastres
    
    **Exemplo:**
    ```json
    {
        "url": "https://atlasdigital.mdr.gov.br/downloads/dados.csv",
        "filename": "atlas_2024.csv",
        "force": false
    }
    ```
    """
    try:
        filepath = atlas_service.download_data(
            url=request.url,
            filename=request.filename,
            force=request.force
        )
        
        return {
            "status": "success",
            "filepath": filepath,
            "message": "Download realizado com sucesso"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no download: {str(e)}"
        )


@router.get("/status", response_model=AtlasDataStatus)
async def get_status():
    """
    Verificar status dos dados do Atlas
    
    Retorna informações sobre o arquivo carregado, cache e diretório de dados
    """
    status_data = AtlasDataStatus(
        arquivo_carregado=atlas_service._loaded_file,
        total_registros=len(atlas_service._cache) if atlas_service._cache is not None else 0,
        cache_timestamp=atlas_service._cache_timestamp.isoformat() if atlas_service._cache_timestamp else None,
        data_dir=str(atlas_service.data_dir)
    )
    return status_data


@router.get("/reload")
async def reload_data():
    """
    Recarregar dados do arquivo
    
    Limpa o cache e recarrega os dados do último arquivo usado
    """
    try:
        atlas_service.clear_cache()
        df = atlas_service.load_data(use_cache=False)
        
        return {
            "status": "success",
            "message": "Dados recarregados com sucesso",
            "total_registros": len(df)
        }
    except Exception as e:
        logger.error(f"Erro ao recarregar dados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao recarregar dados: {str(e)}"
        )


# ============================================================================
# API Endpoints - Consulta de Dados
# ============================================================================

@router.get("/records", response_model=List[AtlasDisasterRecord])
async def get_records(
    limit: int = Query(default=100, ge=1, le=10000, description="Número máximo de registros"),
    offset: int = Query(default=0, ge=0, description="Offset para paginação"),
):
    """
    Listar registros de desastres com paginação
    
    - **limit**: Número máximo de registros (1-10000)
    - **offset**: Offset para paginação
    """
    df = _get_or_load_data()
    
    # Aplicar paginação
    df_paginated = df.iloc[offset:offset + limit]
    
    records = [_record_to_dict(row) for _, row in df_paginated.iterrows()]
    
    return records


@router.post("/filter", response_model=Dict[str, Any])
async def filter_disasters(filters: AtlasFilterRequest):
    """
    Filtrar dados de desastres
    
    **Filtros disponíveis:**
    - **anos**: Tupla (ano_inicial, ano_final)
    - **uf**: Sigla da UF (ex: 'RS')
    - **municipio**: Nome do município (busca parcial)
    - **tipo_desastre**: Tipo de desastre (ex: 'inundacao', 'seca')
    - **intensidade**: Nível de intensidade
    - **min_afetados**: Mínimo de pessoas afetadas
    - **min_mortes**: Mínimo de mortes
    
    **Tipos de desastres suportados:**
    - inundacao, seca, deslizamento, granizo, vendaval, incendio, geada, aluviao
    """
    df = _get_or_load_data()
    
    # Aplicar filtros
    df_filtered = atlas_service.filter_disasters(
        df=df,
        anos=filters.anos,
        uf=filters.uf,
        municipio=filters.municipio,
        tipo_desastre=filters.tipo_desastre,
        intensidade=filters.intensidade,
        min_afetados=filters.min_afetados,
        min_mortes=filters.min_mortes,
    )
    
    # Converter para lista de dicionários
    records = [_record_to_dict(row) for _, row in df_filtered.iterrows()]
    
    return {
        "total": len(records),
        "filters_applied": filters.model_dump(),
        "data": records
    }


@router.get("/filter/simple")
async def filter_disasters_simple(
    ano_inicio: Optional[int] = Query(None, ge=1900, le=2100),
    ano_fim: Optional[int] = Query(None, ge=1900, le=2100),
    uf: Optional[str] = Query(None, max_length=2),
    tipo_desastre: Optional[str] = Query(None),
    min_afetados: Optional[int] = Query(None, ge=0),
):
    """
    Filtrar dados com parâmetros simples (GET)
    
    Versão simplificada usando parâmetros de query ao invés de body JSON
    """
    anos = (ano_inicio, ano_fim) if ano_inicio or ano_fim else None
    
    filters = AtlasFilterRequest(
        anos=anos,
        uf=uf,
        tipo_desastre=tipo_desastre,
        min_afetados=min_afetados,
    )
    
    return await filter_disasters(filters)


# ============================================================================
# API Endpoints - Agregações e Estatísticas
# ============================================================================

@router.post("/aggregate/municipality", response_model=List[Dict[str, Any]])
async def aggregate_by_municipality(
    group_cols: List[str] = Body(default=["uf", "municipio", "tipo_desastre"]),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Agregar dados por município
    
    **group_cols**: Colunas para agrupamento (padrão: ["uf", "municipio", "tipo_desastre"])
    
    Opcionalmente aplica filtros antes da agregação
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
            min_afetados=filters.min_afetados,
            min_mortes=filters.min_mortes,
        )
    
    # Agregar
    df_agg = atlas_service.aggregate_by_municipality(df=df, group_cols=group_cols)
    
    return df_agg.to_dict(orient='records')


@router.get("/aggregate/year", response_model=List[Dict[str, Any]])
async def aggregate_by_year(
    group_by_uf: bool = Query(default=False, description="Agrupar também por UF"),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Agregar dados por ano
    
    Retorna série temporal de ocorrências de desastres
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Agregar por ano
    df_agg = atlas_service.aggregate_by_year(df=df, group_by_uf=group_by_uf)
    
    return df_agg.to_dict(orient='records')


@router.get("/statistics", response_model=AtlasStatistics)
async def get_statistics(filters: Optional[AtlasFilterRequest] = None):
    """
    Obter estatísticas descritivas dos dados
    
    Inclui:
    - Total de registros
    - Período coberto
    - Distribuição por UF
    - Tipos de desastres mais comuns
    - Impacto total (mortes, afetados, prejuízos)
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Calcular estatísticas
    stats = atlas_service.get_statistics(df=df)
    
    return AtlasStatistics(**stats)


# ============================================================================
# API Endpoints - Exportação
# ============================================================================

@router.post("/export/csv")
async def export_to_csv(
    filename: str = Body(..., embed=True),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Exportar dados filtrados para CSV
    
    **filename**: Nome do arquivo de saída
    
    Retorna o caminho do arquivo gerado
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Exportar
    filepath = atlas_service.export_to_csv(df=df, filename=filename)
    
    return {
        "status": "success",
        "filepath": filepath,
        "total_registros": len(df)
    }


@router.get("/export/csv/{filename}")
async def download_exported_csv(filename: str):
    """
    Baixar arquivo CSV exportado
    
    **filename**: Nome do arquivo (ex: atlas_rs_inundacoes.csv)
    """
    filepath = atlas_service.data_dir / filename
    
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arquivo não encontrado: {filename}"
        )
    
    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type="text/csv"
    )


# ============================================================================
# API Endpoints - Análise Específica
# ============================================================================

@router.get("/analysis/top-affected", response_model=List[Dict[str, Any]])
async def get_top_affected_municipalities(
    limit: int = Query(default=20, ge=1, le=100),
    metric: str = Query(default="qtd_ocorrencias", enum=["qtd_ocorrencias", "total_afetados", "total_mortes"]),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Obter municípios mais afetados
    
    **metric**: Métrica para ranking
    - qtd_ocorrencias: Número de ocorrências
    - total_afetados: Total de pessoas afetadas
    - total_mortes: Total de mortes
    
    **limit**: Número de municípios no ranking (1-100)
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Agregar por município
    df_agg = atlas_service.aggregate_by_municipality(
        df=df,
        group_cols=['uf', 'municipio']
    )
    
    # Ordenar pela métrica
    if metric in df_agg.columns:
        df_agg = df_agg.sort_values(metric, ascending=False).head(limit)
    else:
        df_agg = df_agg.sort_values('qtd_ocorrencias', ascending=False).head(limit)
    
    return df_agg.to_dict(orient='records')


@router.get("/analysis/trends", response_model=Dict[str, Any])
async def get_disaster_trends(
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Analisar tendências temporais de desastres
    
    Retorna:
    - Evolução anual de ocorrências
    - Taxa de crescimento
    - Sazonalidade (se disponível)
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    if 'ano' not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coluna 'ano' não encontrada nos dados"
        )
    
    # Agregação anual
    yearly_counts = df.groupby('ano').size().reset_index(name='qtd_ocorrencias')
    
    # Calcular taxa de crescimento
    if len(yearly_counts) > 1:
        yearly_counts['crescimento'] = yearly_counts['qtd_ocorrencias'].pct_change() * 100
        yearly_counts['crescimento_acumulado'] = (
            (yearly_counts['qtd_ocorrencias'] - yearly_counts['qtd_ocorrencias'].iloc[0]) /
            yearly_counts['qtd_ocorrencias'].iloc[0] * 100
        )
    
    # Estatísticas de tendência
    trends = {
        'evolucao_anual': yearly_counts.to_dict(orient='records'),
        'estatisticas': {
            'media_anual': float(yearly_counts['qtd_ocorrencias'].mean()),
            'desvio_padrao': float(yearly_counts['qtd_ocorrencias'].std()) if len(yearly_counts) > 1 else 0,
            'ano_max': int(yearly_counts.loc[yearly_counts['qtd_ocorrencias'].idxmax(), 'ano']) if len(yearly_counts) > 0 else None,
            'ano_min': int(yearly_counts.loc[yearly_counts['qtd_ocorrencias'].idxmin(), 'ano']) if len(yearly_counts) > 0 else None,
        }
    }
    
    return trends


@router.get("/analysis/by-disaster-type", response_model=Dict[str, Any])
async def analysis_by_disaster_type(
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Análise detalhada por tipo de desastre
    
    Retorna distribuição, impacto e estatísticas por tipo
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    if 'tipo_desastre' not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coluna 'tipo_desastre' não encontrada nos dados"
        )
    
    # Agregação por tipo
    type_stats = df.groupby('tipo_desastre').agg(
        qtd_ocorrencias=('ano', 'size'),
        total_mortes=('mortes_diretas', 'sum') if 'mortes_diretas' in df.columns else ('ano', 'count'),
        total_afetados=('afetados', 'sum') if 'afetados' in df.columns else ('ano', 'count'),
        media_afetados=('afetados', 'mean') if 'afetados' in df.columns else ('ano', 'count'),
    ).reset_index()
    
    type_stats = type_stats.sort_values('qtd_ocorrencias', ascending=False)
    
    # Porcentagem por tipo
    total = type_stats['qtd_ocorrencias'].sum()
    type_stats['percentual'] = (type_stats['qtd_ocorrencias'] / total * 100).round(2)
    
    return {
        'distribuicao': type_stats.to_dict(orient='records'),
        'total_registros': len(df),
        'tipos_encontrados': df['tipo_desastre'].nunique()
    }


# ============================================================================
# API Endpoints - Visualizações
# ============================================================================

@router.get("/visualizations/timeseries")
async def get_timeseries_chart(
    chart_type: str = Query(default="line", enum=["line", "bar", "area"]),
    group_by: Optional[str] = Query(None, description="Agrupar por coluna (ex: uf, tipo_desastre)"),
    return_base64: bool = Query(default=True, description="Retornar imagem em base64"),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Gerar gráfico de série temporal
    
    **chart_type**: Tipo de gráfico (line, bar, area)
    **group_by**: Agrupar por coluna específica
    **return_base64**: Retornar imagem codificada em base64
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Gerar gráfico
    img_data = visualization_service.create_time_series_chart(
        df=df,
        title="Evolução Temporal de Desastres",
        chart_type=chart_type,
        group_by=group_by,
        return_base64=return_base64,
    )
    
    if img_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de visualização não disponível (Matplotlib não instalado)"
        )
    
    return {
        "status": "success",
        "chart_type": "timeseries",
        "format": "base64" if return_base64 else "file",
        "data": img_data
    }


@router.get("/visualizations/map")
async def get_map_chart(
    return_base64: bool = Query(default=True, description="Retornar imagem em base64"),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Gerar mapa de calor por UF
    
    **return_base64**: Retornar imagem codificada em base64
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Gerar mapa
    img_data = visualization_service.create_map_chart(
        df=df,
        title="Distribuição Geográfica de Desastres",
        return_base64=return_base64,
    )
    
    if img_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de visualização não disponível"
        )
    
    return {
        "status": "success",
        "chart_type": "map",
        "format": "base64" if return_base64 else "file",
        "data": img_data
    }


@router.get("/visualizations/pie-chart")
async def get_pie_chart(
    return_base64: bool = Query(default=True, description="Retornar imagem em base64"),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Gerar gráfico de pizza por tipo de desastre
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Gerar gráfico
    img_data = visualization_service.create_disaster_type_pie_chart(
        df=df,
        title="Distribuição por Tipo de Desastre",
        return_base64=return_base64,
    )
    
    if img_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de visualização não disponível"
        )
    
    return {
        "status": "success",
        "chart_type": "pie_chart",
        "format": "base64" if return_base64 else "file",
        "data": img_data
    }


@router.get("/visualizations/impact-analysis")
async def get_impact_analysis_chart(
    return_base64: bool = Query(default=True, description="Retornar imagem em base64"),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Gerar gráfico de análise de impacto múltiplo
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Gerar gráfico
    img_data = visualization_service.create_impact_analysis_chart(
        df=df,
        title="Análise de Impacto de Desastres",
        return_base64=return_base64,
    )
    
    if img_data is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de visualização não disponível"
        )
    
    return {
        "status": "success",
        "chart_type": "impact_analysis",
        "format": "base64" if return_base64 else "file",
        "data": img_data
    }


@router.post("/visualizations/dashboard")
async def generate_dashboard(
    save_name: str = Body(default="dashboard_completo.html", embed=True),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Gerar dashboard completo com múltiplas visualizações
    
    Retorna caminho do arquivo HTML gerado
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Gerar dashboard
    dashboard_path = visualization_service.create_summary_dashboard(
        df=df,
        save_path=save_name,
    )
    
    if dashboard_path is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de visualização não disponível"
        )
    
    return {
        "status": "success",
        "dashboard_path": dashboard_path,
        "message": "Dashboard gerado com sucesso"
    }


@router.post("/visualizations/generate-all")
async def generate_all_visualizations(
    prefix: str = Body(default="atlas", embed=True),
    filters: Optional[AtlasFilterRequest] = None,
):
    """
    Gerar todas as visualizações disponíveis
    
    Retorna dicionário com caminhos de todos os arquivos gerados
    """
    df = _get_or_load_data()
    
    # Aplicar filtros se fornecidos
    if filters:
        df = atlas_service.filter_disasters(
            df=df,
            anos=filters.anos,
            uf=filters.uf,
            municipio=filters.municipio,
            tipo_desastre=filters.tipo_desastre,
        )
    
    # Gerar todas as visualizações
    results = visualization_service.generate_all_visualizations(
        df=df,
        prefix=prefix,
    )
    
    return {
        "status": "success",
        "visualizations": results,
        "total_generated": len(results)
    }
