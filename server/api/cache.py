"""
Cache Router - Endpoints para gerenciamento de cache
"""

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()

# Instância do cache será injetada
_smart_cache = None


def set_cache_instance(cache):
    """Configura a instância do cache a ser usada"""
    global _smart_cache
    _smart_cache = cache


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do sistema de cache

    Returns:
        Estatísticas de uso do cache
    """
    if _smart_cache is None:
        return {"error": "Cache não inicializado"}

    return {
        "total_entries": len(_smart_cache.cache),
        "cache_size_mb": len(str(_smart_cache.cache)) / (1024 * 1024),
        "max_age_seconds": _smart_cache.max_age,
        "uptime": "Sistema ativo",
    }


@router.post("/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Limpa todo o cache

    Returns:
        Mensagem de confirmação
    """
    if _smart_cache is None:
        return {"error": "Cache não inicializado"}

    _smart_cache.cache.clear()
    _smart_cache.cache_timestamps.clear()
    return {"message": "Cache limpo com sucesso"}


@router.post("/clear-expired")
async def clear_expired_cache() -> Dict[str, str]:
    """
    Remove apenas entradas expiradas do cache

    Returns:
        Mensagem de confirmação
    """
    if _smart_cache is None:
        return {"error": "Cache não inicializado"}

    _smart_cache.clear_expired()
    return {"message": "Entradas expiradas removidas"}
