import requests
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

# =========================================================
# 1. CLIENTE GEOPORTAL SGB (Risco Geológico)
# =========================================================

@dataclass
class SGBGeoportalConfig:
    """Configuração para o Geoportal SGB-CPRM."""
    base_url: str = "https://geoportal.sgb.gov.br/server/rest/services"
    timeout: int = 30
    page_size: int = 1000


class SGBGeoportalClient:
    """
    Cliente para acessar dados do Serviço Geológico do Brasil (SGB-CPRM)
    via ArcGIS REST API. Inclui dados de suscetibilidade e áreas de risco.
    """
    
    # Serviços conhecidos no Geoportal SGB
    SERVICES = {
        "cemaden": "Cemaden/FeatureServer",
        "areas_risco": "SIGMINE/Areas_Risco/FeatureServer",  # Exemplo típico
        "suscetibilidade": "SIGMINE/Suscetibilidade/FeatureServer",
        "geologia": "SIGMINE/Geologia/MapServer",
    }
    
    def __init__(self, config: SGBGeoportalConfig = None):
        self.config = config or SGBGeoportalConfig()
    
    def _make_request(self, service_path: str, layer_id: int = 0, 
                      params: Dict = None) -> Dict:
        """Faz requisição ao serviço ArcGIS."""
        url = f"{self.config.base_url}/{service_path}/{layer_id}/query"
        default_params = {
            "f": "json",
            "outSR": 4326,  # WGS84
        }
        if params:
            default_params.update(params)
        
        resp = requests.get(url, params=default_params, timeout=self.config.timeout)
        resp.raise_for_status()
        data = resp.json()
        
        if "error" in data:
            raise RuntimeError(f"Erro ArcGIS: {data['error']}")
        return data
    
    def fetch_risk_areas_by_bbox(self, min_lon: float, min_lat: float, 
                                 max_lon: float, max_lat: float,
                                 geometry_type: str = "esriGeometryEnvelope") -> pd.DataFrame:
        """
        Busca áreas de risco geológico dentro de uma bounding box.
        
        Args:
            min_lon, min_lat, max_lon, max_lat: Coordenadas da bbox
            geometry_type: Tipo de geometria para consulta espacial
            
        Returns:
            DataFrame com áreas de risco e classificação
        """
        # Geometria no formato ArcGIS JSON
        geometry = {
            "xmin": min_lon,
            "ymin": min_lat,
            "xmax": max_lon,
            "ymax": max_lat,
            "spatialReference": {"wkid": 4326}
        }
        
        params = {
            "geometry": str(geometry).replace("'", '"'),
            "geometryType": geometry_type,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
        }
        
        try:
            # Tenta buscar no serviço de áreas de risco
            data = self._make_request(self.SERVICES.get("areas_risco", "Cemaden/FeatureServer"), 
                                     layer_id=0, params=params)
        except Exception as e:
            print(f"Serviço de áreas de risco não disponível, tentando alternativa: {e}")
            # Fallback para serviço Cemaden ou outro disponível
            data = self._make_request("Cemaden/FeatureServer", layer_id=0, params=params)
        
        return self._parse_features(data)
    
    def fetch_susceptibility_by_municipio(self, cod_ibge: str) -> pd.DataFrame:
        """
        Busca dados de suscetibilidade geológica por código IBGE do município.
        
        Args:
            cod_ibge: Código IBGE de 7 dígitos
            
        Returns:
            DataFrame com classes de suscetibilidade
        """
        where_clause = f"codigo_ibge = '{cod_ibge}' OR cod_ibge = '{cod_ibge}'"
        
        params = {
            "where": where_clause,
            "outFields": "codigo_ibge,municipio,uf,grau_suscetibilidade,tipo_processo,area_km2",
            "returnGeometry": "true",
        }
        
        try:
            data = self._make_request(self.SERVICES.get("suscetibilidade", "Cemaden/FeatureServer"), 
                                     layer_id=0, params=params)
        except Exception as e:
            print(f"Serviço de suscetibilidade indisponível: {e}")
            return pd.DataFrame()
        
        return self._parse_features(data)
    
    def _parse_features(self, data: Dict) -> pd.DataFrame:
        """Converte resposta ArcGIS em DataFrame."""
        features = data.get("features", [])
        if not features:
            return pd.DataFrame()
        
        records = []
        for feat in features:
            attrs = feat.get("attributes", {})
            geom = feat.get("geometry", {})
            
            # Extrai coordenadas do centroide se disponível
            if "x" in geom and "y" in geom:
                lat, lon = geom.get("y"), geom.get("x")
            else:
                lat, lon = None, None
            
            record = {
                "objectid": attrs.get("objectid"),
                "municipio": attrs.get("municipio") or attrs.get("nome"),
                "uf": attrs.get("uf") or attrs.get("sigla_uf"),
                "cod_ibge": attrs.get("codigo_ibge") or attrs.get("cod_ibge"),
                "risco": attrs.get("grau_risco") or attrs.get("risco"),
                "suscetibilidade": attrs.get("grau_suscetibilidade") or attrs.get("suscetibilidade"),
                "tipo_processo": attrs.get("tipo_processo"),
                "area_km2": attrs.get("area_km2"),
                "lat": lat,
                "lon": lon,
                "fonte": "SGB-CPRM",
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def get_risk_factor(self, lat: float, lon: float, buffer_km: float = 5.0) -> Dict[str, Any]:
        """
        Obtém fator de risco geológico para uma coordenada específica.
        Busca áreas de risco dentro de um raio (buffer) da coordenada.
        
        Returns:
            Dict com classificação de risco e fator de ajuste
        """
        # Converte km para graus (aproximado)
        buffer_deg = buffer_km / 111.0
        
        min_lon = lon - buffer_deg
        max_lon = lon + buffer_deg
        min_lat = lat - buffer_deg
        max_lat = lat + buffer_deg
        
        df = self.fetch_risk_areas_by_bbox(min_lon, min_lat, max_lon, max_lat)
        
        if df.empty:
            return {
                "risco_encontrado": False,
                "risco_classificacao": "Não classificado",
                "suscetibilidade": None,
                "fator_ajuste": 1.0,  # Sem ajuste
                "area_km2_total": 0,
                "n_areas": 0,
            }
        
        # Determina o maior risco encontrado
        risco_max = self._classify_risk_level(df)
        suscetibilidade_max = df["suscetibilidade"].dropna().max() if "suscetibilidade" in df.columns else None
        
        # Calcula fator de ajuste baseado no risco (1.0 = baseline)
        fator = self._calculate_risk_factor(risco_max, suscetibilidade_max)
        
        return {
            "risco_encontrado": True,
            "risco_classificacao": risco_max,
            "suscetibilidade": suscetibilidade_max,
            "fator_ajuste": fator,
            "area_km2_total": df["area_km2"].sum() if "area_km2" in df.columns else None,
            "n_areas": len(df),
        }
    
    def _classify_risk_level(self, df: pd.DataFrame) -> str:
        """Classifica o nível máximo de risco encontrado."""
        risco_col = None
        for col in ["risco", "grau_risco", "nivel_risco"]:
            if col in df.columns:
                risco_col = col
                break
        
        if risco_col is None:
            return "Desconhecido"
        
        # Hierarquia de risco
        riscos = df[risco_col].dropna().str.upper().unique()
        
        if any(r in ["ALTO", "ALTISSIMO", "ELEVADO", "MUITO ALTO"] for r in riscos):
            return "Alto"
        elif any(r in ["MEDIO", "MODERADO", "MÉDIO"] for r in riscos):
            return "Médio"
        elif any(r in ["BAIXO", "BAIXA"] for r in riscos):
            return "Baixo"
        else:
            return "Não classificado"
    
    def _calculate_risk_factor(self, risco_class: str, suscetibilidade: Optional[str]) -> float:
        """
        Calcula fator multiplicador para ajuste de prêmio/payout.
        
        Lógica:
        - Risco Alto: 1.5x (50% aumento no prêmio ou no payout)
        - Risco Médio: 1.2x (20% aumento)
        - Risco Baixo: 1.0x (baseline)
        - Suscetibilidade alta adiciona +0.2
        """
        fatores = {
            "Alto": 1.5,
            "Médio": 1.2,
            "Medio": 1.2,
            "Baixo": 1.0,
            "Baixa": 1.0,
            "Não classificado": 1.0,
            "Desconhecido": 1.0,
        }
        
        fator_base = fatores.get(risco_class, 1.0)
        
        # Adiciona ajuste por suscetibilidade se disponível
        if suscetibilidade:
            susc = str(suscetibilidade).upper()
            if any(s in susc for s in ["ALTO", "ALTA", "ELEVADO"]):
                fator_base += 0.2
            elif any(s in susc for s in ["MEDIO", "MÉDIO", "MODERADO"]):
                fator_base += 0.1
        
        return round(fator_base, 2)


# =========================================================
# 2. INTEGRADOR COM ÍNDICE PARAMÉTRICO (Sistema Híbrido)
# =========================================================

class GeologicalRiskAdjuster:
    """
    Integra dados do SGB (risco geológico) com a precificação paramétrica.
    Ajusta prêmios e payouts baseado na vulnerabilidade geológica do local.
    """
    
    def __init__(self, sgb_client: Optional[SGBGeoportalClient] = None):
        self.sgb = sgb_client or SGBGeoportalClient()
    
    def adjust_premium(self, base_premium: float, lat: float, lon: float) -> Dict[str, Any]:
        """
        Ajusta o prêmio base de um seguro paramétrico baseado no risco geológico.
        
        Args:
            base_premium: Prêmio calculado base (sem considerar risco geológico)
            lat, lon: Coordenadas do bem segurado
            
        Returns:
            Dict com prêmio ajustado e metadados
        """
        risk_data = self.sgb.get_risk_factor(lat, lon)
        fator = risk_data["fator_ajuste"]
        
        premium_adjusted = base_premium * fator
        
        return {
            "base_premium": base_premium,
            "adjusted_premium": round(premium_adjusted, 2),
            "risk_factor": fator,
            "risk_classification": risk_data["risco_classificacao"],
            "geological_vulnerability": risk_data.get("suscetibilidade"),
            "areas_found": risk_data.get("n_areas"),
        }
    
    def adjust_payout(self, base_payout: float, lat: float, lon: float) -> Dict[str, Any]:
        """
        Ajusta o payout (indenização) baseado no risco geológico.
        Em áreas de alto risco, o payout pode ser majorado.
        """
        risk_data = self.sgb.get_risk_factor(lat, lon)
        fator = risk_data["fator_ajuste"]
        
        payout_adjusted = base_payout * fator
        
        return {
            "base_payout": base_payout,
            "adjusted_payout": round(payout_adjusted, 2),
            "risk_factor": fator,
            "risk_classification": risk_data["risco_classificacao"],
        }


class EnhancedParametricInsuranceEngine:
    """
    Engine completa que combina:
    - Dados climáticos (CEMADEN, Open-Meteo)
    - Dados geológicos (SGB-CPRM)
    - Cálculo de payout com ajuste de vulnerabilidade
    """
    
    def __init__(self):
        # Reutiliza os clientes anteriores
        self.sgb = SGBGeoportalClient()
        self.risk_adjuster = GeologicalRiskAdjuster(self.sgb)
    
    def evaluate_location(self, lat: float, lon: float, 
                         base_capital: float = 100000.0,
                         rainfall_threshold: float = 100.0,
                         rainfall_observed: float = 120.0) -> Dict[str, Any]:
        """
        Avaliação completa de uma localização para seguro paramétrico.
        
        Returns:
            Dict completo com riscos climáticos e geológicos, prêmio e payout ajustados
        """
        # 1. Obtém fator de risco geológico
        geo_risk = self.sgb.get_risk_factor(lat, lon)
        
        # 2. Simula cálculo de payout baseado em chuva (exemplo)
        # Aqui você integraria com o CemadenClient real
        payout_base = base_capital * 0.6 if rainfall_observed >= rainfall_threshold else 0
        
        # 3. Aplica ajuste geológico
        payout_adj = self.risk_adjuster.adjust_payout(payout_base, lat, lon)
        premium_adj = self.risk_adjuster.adjust_premium(base_capital * 0.02, lat, lon)  # 2% base
        
        return {
            "location": {"lat": lat, "lon": lon},
            "geological_risk": geo_risk,
            "climate_trigger": {
                "threshold_mm": rainfall_threshold,
                "observed_mm": rainfall_observed,
                "triggered": rainfall_observed >= rainfall_threshold,
            },
            "financial": {
                "insured_capital": base_capital,
                "base_premium": premium_adj["base_premium"],
                "adjusted_premium": premium_adj["adjusted_premium"],
                "base_payout": payout_adj["base_payout"],
                "adjusted_payout": payout_adj["adjusted_payout"],
            },
            "recommendation": self._generate_recommendation(geo_risk, rainfall_observed >= rainfall_threshold),
        }
    
    def _generate_recommendation(self, geo_risk: Dict, climate_triggered: bool) -> str:
        """Gera recomendação de underwriting."""
        risco_alto = geo_risk.get("risco_classificacao", "").upper() in ["ALTO", "ALTÍSSIMO", "ALTISSIMO", "MUITO ALTO"]
        risco_medio = geo_risk.get("risco_classificacao", "").upper() in ["MÉDIO", "MEDIO", "MODERADO"]
        
        if risco_alto:
            if climate_triggered:
                return "ALERTA VERMELHO: Sinistro climático acionado em área de ALTO risco geológico. Necessária vistoria detalhada antes do pagamento."
            return "ALERTA: Localização em área de ALTO risco geológico. Cuidado ao subscrever novos riscos."
            
        if risco_medio:
            if climate_triggered:
                return "ATENÇÃO: Sinistro climático acionado em área de risco geológico MÉDIO. Aplicar ajustes de vulnerabilidade ao payout."
            return "NORMAL: Área de risco geológico médio. Monitoramento padrão."
            
        if climate_triggered:
            return "APROVADO: Sinistro climático acionado em área de baixo risco geológico. Seguir fluxo padrão de pagamento paramétrico."
            
        return "MONITORAMENTO: Sem gatilhos acionados. Risco geológico enquadrado no baseline."

# Instância global configurada
sgb_client = SGBGeoportalClient()
sgb_engine = EnhancedParametricInsuranceEngine()
