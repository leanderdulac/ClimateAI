from fastapi import APIRouter, HTTPException, Depends
import logging
from typing import Dict, Any, List

from services.celestrak_service import celestrak_service

router = APIRouter()
logger = logging.getLogger(__name__)

from config.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from models.sqlalchemy_models import SpaceWeatherLog

@router.get("/space-weather")
async def get_space_weather(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Obter clima espacial atual do CelesTrak"""
    try:
        data = celestrak_service.get_space_weather(use_cache=True)
        if not data:
            raise HTTPException(status_code=503, detail="CelesTrak data unavailable")
        
        response_data = {
            "timestamp": data.timestamp.isoformat(),
            "kp_index": data.kp_index,
            "ap_index": data.ap_index,
            "solar_flux": data.solar_flux,
            "geomagnetic_storm_active": data.geomagnetic_storm,
            "geomagnetic_storm_level": data.storm_level,
            "solar_radiation_storm": data.solar_radiation_storm,
            "radiation_level": data.radiation_level,
            "radio_blackout": data.radio_blackout,
            "blackout_level": data.blackout_level,
            "status": "Estável" if not data.geomagnetic_storm else f"Tempestade ({data.storm_level})"
        }
        
        # Persist to Supabase DB via SQLAlchemy
        db_log = SpaceWeatherLog(
            timestamp=data.timestamp,
            kp_index=data.kp_index,
            ap_index=data.ap_index,
            solar_flux=data.solar_flux,
            geomagnetic_storm=data.geomagnetic_storm,
            storm_level=data.storm_level,
            solar_radiation_storm=data.solar_radiation_storm,
            radiation_level=data.radiation_level,
            radio_blackout=data.radio_blackout,
            blackout_level=data.blackout_level
        )
        
        try:
            db.add(db_log)
            await db.commit()
        except Exception as db_e:
            await db.rollback()
            logger.error(f"Failed to persist SpaceWeatherLog to DB: {db_e}")
            
        return response_data
    except Exception as e:
        logger.error(f"Erro ao obter clima espacial: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/conjunctions")
async def get_conjunction_alerts() -> Dict[str, Any]:
    """Obter os top 10 alertas de conjunção do SOCRATES"""
    try:
        alerts = celestrak_service.get_conjunction_alerts(use_cache=True)
        
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                "conjunction_id": alert.conjunction_id,
                "satellite_1": alert.object1_name,
                "satellite_2": alert.object2_name,
                "tca_time": alert.tca.isoformat(),
                "miss_distance_km": round(alert.miss_distance_km, 3),
                "probability": f"{alert.collision_probability:.2e}",
                "risk_level": alert.risk_level.value
            })
            
            # Limitar a 10 para o dashboard
            if len(formatted_alerts) >= 10:
                break
                
        return {
            "alerts": formatted_alerts,
            "count": len(formatted_alerts)
        }
    except Exception as e:
        logger.error(f"Erro ao obter alertas de conjunção: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
