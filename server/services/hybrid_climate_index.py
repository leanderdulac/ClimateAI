import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

# ============================================================================
# 1. CLIENTE CEMADEN (ArcGIS)
# ============================================================================

LAYER_URL = (
    "https://observatorio.infraestrutura.mg.gov.br/server/rest/services/"
    "00_PUBLICACOES/cemaden_estacoes_pluviometricas/MapServer/1/query"
)

DEFAULT_FIELDS = (
    "objectid,data,acumulado,codestacao,nomeestacao,cidade,codibge,uf,"
    "latitude,longitude"
)


class CemadenClient:
    def __init__(self, layer_url: str = LAYER_URL, page_size: int = 1000, timeout: int = 30):
        self.layer_url = layer_url
        self.page_size = page_size
        self.timeout = timeout

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.get(self.layer_url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Erro na API ArcGIS: {data['error']}")
        return data

    def fetch_features(
        self,
        where: str = "1=1",
        out_fields: str = DEFAULT_FIELDS,
        return_geometry: bool = True,
        max_records: Optional[int] = None,
    ) -> pd.DataFrame:
        records: List[Dict[str, Any]] = []
        offset = 0
        total_fetched = 0

        while True:
            remaining = None if max_records is None else max_records - total_fetched
            if remaining is not None and remaining <= 0:
                break

            page_size = self.page_size if remaining is None else min(self.page_size, remaining)

            params = {
                "where": where,
                "outFields": out_fields,
                "f": "json",
                "returnGeometry": "true" if return_geometry else "false",
                "outSR": 4326,
                "resultOffset": offset,
                "resultRecordCount": page_size,
            }

            data = self._request(params)
            features = data.get("features", [])
            if not features:
                break

            for feat in features:
                attrs = feat.get("attributes", {})
                geom = feat.get("geometry", {}) if return_geometry else {}

                records.append({
                    "objectid": attrs.get("objectid"),
                    "data_raw": attrs.get("data"),
                    "acumulado_mm": self._safe_float(attrs.get("acumulado")),
                    "codestacao": attrs.get("codestacao"),
                    "nomeestacao": attrs.get("nomeestacao"),
                    "municipio": attrs.get("cidade"),
                    "codibge": attrs.get("codibge"),
                    "uf": attrs.get("uf"),
                    "lat": geom.get("y") or self._safe_float(attrs.get("latitude")),
                    "lon": geom.get("x") or self._safe_float(attrs.get("longitude")),
                    "fonte": "CEMADEN",
                })

            fetched = len(features)
            total_fetched += fetched
            offset += fetched

            if fetched < page_size:
                break

        df = pd.DataFrame(records)
        if not df.empty and "data_raw" in df.columns:
            df["data"] = pd.to_datetime(df["data_raw"], unit="ms", errors="coerce")
        else:
            df["data"] = pd.NaT
        return df

    def _safe_float(self, val):
        try:
            return float(val) if val is not None else np.nan
        except (ValueError, TypeError):
            return np.nan

    def fetch_by_uf(self, uf: str) -> pd.DataFrame:
        return self.fetch_features(where=f"uf = '{uf}'")

    def fetch_by_bbox(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> pd.DataFrame:
        """Busca por bounding box (útil para cidades específicas)."""
        where = (
            f"latitude >= {min_lat} AND latitude <= {max_lat} AND "
            f"longitude >= {min_lon} AND longitude <= {max_lon}"
        )
        return self.fetch_features(where=where)


# ============================================================================
# 2. CLIENTE OPEN-METEO (Fallback/Backup para INMET/ERA5)
# ============================================================================

@dataclass
class OpenMeteoConfig:
    url: str = "https://api.open-meteo.com/v1/forecast"
    historical_url: str = "https://archive-api.open-meteo.com/v1/archive"


class OpenMeteoClient:
    """Cliente para Open-Meteo (gratuito, sem API key) como fallback."""
    
    def __init__(self, config: OpenMeteoConfig = None):
        self.config = config or OpenMeteoConfig()
    
    def fetch_precipitation(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        historical: bool = True
    ) -> pd.DataFrame:
        """
        Busca precipitação diária (mm) para coordenadas específicas.
        Retorna DataFrame com ['data', 'precipitation_sum', 'lat', 'lon', 'fonte'].
        """
        url = self.config.historical_url if historical else self.config.url
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "precipitation_sum",
            "timezone": "America/Sao_Paulo",
        }
        
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        daily = data.get("daily", {})
        df = pd.DataFrame({
            "data": pd.to_datetime(daily.get("time")),
            "acumulado_mm": daily.get("precipitation_sum"),
            "lat": lat,
            "lon": lon,
            "fonte": "OPENMETEO",
        })
        return df


# ============================================================================
# 3. ENGINE DE PAYOUT PARAMÉTRICO
# ============================================================================

@dataclass
class PayoutTier:
    """Define um nível de payout."""
    threshold_mm: float          # Limiar inferior (inclusivo)
    max_mm: Optional[float]      # Limiar superior (exclusivo), None = infinito
    payout_pct: float            # Percentual do limite segurado (0-1)
    tier_name: str               # Nome do tier (ex: "Moderado", "Severo", "Extremo")


class ParametricPayoutEngine:
    """
    Engine de cálculo de payout para seguros paramétricos climáticos.
    Suporta múltiplos tiers (ex: 30%/60%/100%) ou função contínua.
    """
    
    def __init__(self, tiers: Optional[List[PayoutTier]] = None):
        # Default: 3 tiers - 30%, 60%, 100%
        self.tiers = tiers or [
            PayoutTier(threshold_mm=50, max_mm=100, payout_pct=0.30, tier_name="Moderado"),
            PayoutTier(threshold_mm=100, max_mm=150, payout_pct=0.60, tier_name="Severo"),
            PayoutTier(threshold_mm=150, max_mm=None, payout_pct=1.00, tier_name="Extremo"),
        ]
        self.tiers.sort(key=lambda t: t.threshold_mm)
    
    def calculate_payout(self, rainfall_mm: float, insured_capital: float) -> Dict[str, Any]:
        """
        Calcula o payout para um valor de chuva específico.
        
        Returns:
            dict com: payout_value, payout_pct, tier_name, triggered (bool)
        """
        if pd.isna(rainfall_mm) or rainfall_mm <= 0:
            return {
                "payout_value": 0.0,
                "payout_pct": 0.0,
                "tier_name": "Nenhum",
                "triggered": False,
                "rainfall_mm": rainfall_mm,
            }
        
        for tier in self.tiers:
            if tier.max_mm is None:
                if rainfall_mm >= tier.threshold_mm:
                    return {
                        "payout_value": insured_capital * tier.payout_pct,
                        "payout_pct": tier.payout_pct,
                        "tier_name": tier.tier_name,
                        "triggered": True,
                        "rainfall_mm": rainfall_mm,
                    }
            else:
                if tier.threshold_mm <= rainfall_mm < tier.max_mm:
                    return {
                        "payout_value": insured_capital * tier.payout_pct,
                        "payout_pct": tier.payout_pct,
                        "tier_name": tier.tier_name,
                        "triggered": True,
                        "rainfall_mm": rainfall_mm,
                    }
        
        # Abaixo do primeiro tier
        return {
            "payout_value": 0.0,
            "payout_pct": 0.0,
            "tier_name": "Nenhum",
            "triggered": False,
            "rainfall_mm": rainfall_mm,
        }
    
    def apply_to_dataframe(
        self, 
        df: pd.DataFrame, 
        insured_capital: float,
        rainfall_col: str = "acumulado_mm"
    ) -> pd.DataFrame:
        """
        Aplica o cálculo de payout em todo o DataFrame.
        """
        df = df.copy()
        
        payouts = []
        for _, row in df.iterrows():
            rain = row.get(rainfall_col, 0)
            result = self.calculate_payout(rain, insured_capital)
            payouts.append(result)
        
        payout_df = pd.DataFrame(payouts)
        df = pd.concat([df.reset_index(drop=True), payout_df], axis=1)
        
        return df


# ============================================================================
# 4. ÍNDICE HÍBRIDO (CEMADEN + Fallback Open-Meteo)
# ============================================================================

class HybridClimateIndex:
    """
    Orquestra dados de múltiplas fontes com lógica de fallback:
    1. Tenta CEMADEN (dados oficiais, alta resolução temporal)
    2. Se não houver dado para coordenada, busca Open-Meteo
    3. Integra tudo em um índice unificado para precificação.
    """
    
    def __init__(
        self,
        cemaden_client: Optional[CemadenClient] = None,
        openmeteo_client: Optional[OpenMeteoClient] = None,
        payout_engine: Optional[ParametricPayoutEngine] = None,
    ):
        self.cemaden = cemaden_client or CemadenClient()
        self.openmeteo = openmeteo_client or OpenMeteoClient()
        self.payout = payout_engine or ParametricPayoutEngine()
    
    def fetch_municipal_data(
        self,
        municipio: str,
        uf: str,
        data_inicio: str,
        data_fim: str,
        raio_km_fallback: float = 10.0,
    ) -> pd.DataFrame:
        """
        Busca dados para um município específico.
        """
        # Busca CEMADEN
        df_cemaden = self.cemaden.fetch_features(
            where=f"UPPER(cidade) = '{municipio.upper()}' AND uf = '{uf}'"
        )
        
        # Se encontrou dados do CEMADEN com valores válidos, usa-os
        if not df_cemaden.empty and "acumulado_mm" in df_cemaden.columns and df_cemaden["acumulado_mm"].notna().any():
            return df_cemaden
        
        # Fallback para Open-Meteo
        coord_fallbacks = {
            "PORTO ALEGRE": (-30.0346, -51.2177),
            "SANTOS": (-23.9608, -46.3336),
            "SAO PAULO": (-23.5505, -46.6333),
            "RIO DE JANEIRO": (-22.9068, -43.1729),
        }
        
        coords = coord_fallbacks.get(municipio.upper())
        if not coords:
            # Fallback generico SP se não achar
            coords = (-23.5505, -46.6333)
            
        lat, lon = coords
        df_open = self.openmeteo.fetch_precipitation(
            lat=lat, lon=lon,
            start_date=data_inicio,
            end_date=data_fim,
            historical=True
        )
        return df_open

    def fetch_by_coordinates(
        self,
        lat: float,
        lon: float,
        data_inicio: str,
        data_fim: str,
        raio_graus: float = 0.1  # aprox 11km
    ) -> pd.DataFrame:
        """
        Busca dados de chuva por coordenada (lat/lon).
        """
        # Tenta CEMADEN com bounding box
        df_cemaden = self.cemaden.fetch_by_bbox(
            min_lat=lat - raio_graus,
            max_lat=lat + raio_graus,
            min_lon=lon - raio_graus,
            max_lon=lon + raio_graus
        )
        
        if not df_cemaden.empty and "acumulado_mm" in df_cemaden.columns and df_cemaden["acumulado_mm"].notna().any():
            # Filtra dados de precipitação validos
            return df_cemaden[df_cemaden["acumulado_mm"].notna()]
            
        # Fallback Open-Meteo para a exata coordenada
        df_open = self.openmeteo.fetch_precipitation(
            lat=lat, lon=lon,
            start_date=data_inicio,
            end_date=data_fim,
            historical=True
        )
        return df_open
    
    def calculate_parametric_payout(
        self,
        df: pd.DataFrame,
        insured_capital: float = 100000.0,
    ) -> pd.DataFrame:
        return self.payout.apply_to_dataframe(df, insured_capital)
    
    def generate_pricing_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        triggered = df[df.get("triggered", False) == True]
        
        report = {
            "total_registros": len(df),
            "eventos_gatilho": len(triggered),
            "taxa_disparo": len(triggered) / len(df) if len(df) > 0 else 0,
            "payout_total_estimado": triggered.get("payout_value", pd.Series([0])).sum(),
            "payout_medio_evento": triggered.get("payout_value", pd.Series([0])).mean() if len(triggered) > 0 else 0,
            "chuva_maxima": df.get("acumulado_mm", pd.Series([0])).max(),
            "chuva_media": df.get("acumulado_mm", pd.Series([0])).mean(),
            "fontes_utilizadas": df.get("fonte", pd.Series(["desconhecido"])).unique().tolist(),
        }
        return report

