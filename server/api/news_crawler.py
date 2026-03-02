"""
News Crawler API Router
Endpoints para o Radar de Notícias em tempo real
"""

from fastapi import APIRouter, Query
from typing import Optional
from services.news_crawler_service import get_news_crawler_service

router = APIRouter(prefix="/v1/news-crawler", tags=["News Crawler"])


@router.get("/alerts")
async def get_alerts(
    limit: int = Query(20, ge=1, le=100),
    disaster_type: Optional[str] = Query(None, description="Filtrar por tipo de desastre")
):
    """Retorna alertas climáticos detectados via notícias"""
    service = get_news_crawler_service()

    # Auto-crawl on first request if never crawled
    if service._last_crawl is None:
        await service.force_refresh()

    alerts = service.get_recent_alerts(limit=limit, disaster_type=disaster_type)
    return {
        "alerts": alerts,
        "total": len(alerts),
        "last_crawl": service._last_crawl.isoformat() if service._last_crawl else None,
    }


@router.get("/stats")
async def get_stats():
    """Estatísticas dos alertas coletados"""
    service = get_news_crawler_service()
    return service.get_stats()


@router.post("/refresh")
async def force_refresh():
    """Força uma varredura imediata dos feeds RSS"""
    service = get_news_crawler_service()
    result = await service.force_refresh()
    return result


@router.get("/risk-adjustment")
async def get_risk_adjustment(uf: Optional[str] = Query(None, description="Filtrar por UF")):
    """Retorna fator de ajuste de risco dinâmico baseado no fluxo de notícias"""
    service = get_news_crawler_service()
    return service.get_risk_adjustment_factor(uf=uf)


@router.get("/oracle-events")
async def get_oracle_events(limit: int = Query(20, ge=1, le=100)):
    """Retorna alertas de notícias já convertidos para formato Oracle"""
    service = get_news_crawler_service()
    events = service.get_oracle_events()
    return {"events": events[:limit], "total": len(events)}
