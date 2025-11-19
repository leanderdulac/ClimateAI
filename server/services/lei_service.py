"""
Loss Expectancy Index (LEI) Calculation Service
Implements: LEI = Exp_o × t_o × f_o × SCR_normalizado
Where:
- Exp_o = Valor exposto do imóvel (reconstrução)
- t_o = taxa de sinistralidade histórica da região (ajustada)
- f_o = fator de exposição ocupacional (residencial, comercial)
- SCR_normalizado = SCR / 1000  [transformação probabilística]

Climate adjustment of rate:
t_o_clim = t_o × (1 + γ·SCR)^δ
γ = 0.35 (sensitivity coefficient)
δ = 1.2 (risk exponentiality)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PropertyExposure:
    """Information about property exposure"""

    property_id: str
    exposed_value: float  # Reconstruction value (Exp_o)
    property_type: (
        str  # Property type (residential, commercial, etc.) determines f_o factor
    )
    location_coordinates: Tuple[float, float]
    occupancy_factor: float = 1.0  # Occupancy-specific factor (f_o component)


@dataclass
class RegionalSinistralityData:
    """Regional sinistrality data with climate adjustment coefficients"""

    region_id: str
    historical_sinistrality_rate: float  # Base t_o rate
    climate_sensitivity_gamma: float = 0.35  # γ = 0.35
    climate_exponentiality_delta: float = 1.2  # δ = 1.2
    last_updated: datetime = datetime.now()


@dataclass
class LEIResult:
    """Result of LEI calculation"""

    lei_value: float  # Loss Expectancy Index
    exposed_value: float  # Exp_o component
    base_sinistrality_rate: float  # t_o component
    climate_adjusted_rate: float  # t_o_clim component
    occupational_factor: float  # f_o component
    normalized_scr: float  # SCR_normalized component
    climate_sensitivity_coeff: float  # γ coefficient
    climate_exponentiality_coeff: float  # δ coefficient
    calculation_timestamp: datetime


class LEICalculator:
    """
    Calculator for Loss Expectancy Index with climate-adjusted regional sinistrality rates
    Implements: LEI = Exp_o × t_o × f_o × SCR_normalizado
    with climate-adjusted rate: t_o_clim = t_o × (1 + γ·SCR)^δ
    """

    def __init__(self):
        # Default occupational exposure factors (f_o values)
        self.occupational_factors = {
            "residential": 0.8,
            "commercial": 1.2,
            "industrial": 1.5,
            "agricultural": 1.0,
            "institutional": 1.1,
        }

        # Default climate coefficients
        self.default_gamma = 0.35  # γ sensitivity coefficient
        self.default_delta = 1.2  # δ exponentiality coefficient

        # Regional sinistrality data
        self.regional_data = {}

        # Add some default regions
        self._initialize_default_regions()

    def _initialize_default_regions(self):
        """Initialize some default regional sinistrality data"""
        default_regions = {
            "sao_paulo": RegionalSinistralityData(
                region_id="sao_paulo",
                historical_sinistrality_rate=0.025,  # 2.5% base rate
                climate_sensitivity_gamma=self.default_gamma,
                climate_exponentiality_delta=self.default_delta,
            ),
            "rio_de_janeiro": RegionalSinistralityData(
                region_id="rio_de_janeiro",
                historical_sinistrality_rate=0.030,  # 3.0% base rate (higher due to floods)
                climate_sensitivity_gamma=self.default_gamma,
                climate_exponentiality_delta=self.default_delta,
            ),
            "curitiba": RegionalSinistralityData(
                region_id="curitiba",
                historical_sinistrality_rate=0.020,  # 2.0% base rate (milder climate)
                climate_sensitivity_gamma=self.default_gamma,
                climate_exponentiality_delta=self.default_delta,
            ),
            "salvador": RegionalSinistralityData(
                region_id="salvador",
                historical_sinistrality_rate=0.028,  # 2.8% base rate
                climate_sensitivity_gamma=self.default_gamma,
                climate_exponentiality_delta=self.default_delta,
            ),
            "brasilia": RegionalSinistralityData(
                region_id="brasilia",
                historical_sinistrality_rate=0.018,  # 1.8% base rate (controlled environment)
                climate_sensitivity_gamma=self.default_gamma,
                climate_exponentiality_delta=self.default_delta,
            ),
        }

        for region_id, data in default_regions.items():
            self.regional_data[region_id] = data

    def update_regional_data(self, region_data: RegionalSinistralityData):
        """Update or add regional sinistrality data"""
        self.regional_data[region_data.region_id] = region_data

    def get_regional_data(self, region_id: str) -> Optional[RegionalSinistralityData]:
        """Get regional sinistrality data"""
        return self.regional_data.get(region_id)

    def calculate_climate_adjusted_rate(
        self,
        base_rate: float,
        scr_score: float,
        gamma: Optional[float] = None,
        delta: Optional[float] = None,
    ) -> float:
        """
        Calculate climate-adjusted sinistrality rate:
        t_o_clim = t_o × (1 + γ·SCR)^δ

        Args:
            base_rate: Base historical sinistrality rate (t_o)
            scr_score: Current SCR score
            gamma: Sensitivity coefficient γ (default from instance)
            delta: Exponentiality coefficient δ (default from instance)

        Returns:
            Climate-adjusted sinistrality rate (t_o_clim)
        """
        if gamma is None:
            gamma = self.default_gamma
        if delta is None:
            delta = self.default_delta

        # Normalize SCR to prevent exponential explosion
        # Use normalized SCR value similar to the LEI normalization (dividing by 1000)
        normalized_scr = scr_score / 1000.0

        # Cap the normalized SCR to prevent extremely high adjustment factors
        capped_scr = min(
            normalized_scr, 5.0
        )  # Cap at 5x normalized value to prevent explosion

        # Calculate climate adjustment factor: (1 + γ·SCR_normalized)^δ
        adjustment_factor = (1 + gamma * capped_scr) ** delta

        # Apply adjustment to base rate
        adjusted_rate = base_rate * adjustment_factor

        return adjusted_rate

    def calculate_normalized_scr(self, scr_score: float) -> float:
        """
        Calculate normalized SCR: SCR_normalizado = SCR / 1000

        Args:
            scr_score: Raw SCR score

        Returns:
            Normalized SCR value
        """
        return scr_score / 1000.0

    def calculate_lei_score(
        self,
        property_exposure: PropertyExposure,
        region_id: str,
        scr_score: float,
        custom_occupational_factor: Optional[float] = None,
        custom_gamma: Optional[float] = None,
        custom_delta: Optional[float] = None,
    ) -> LEIResult:
        """
        Calculate Loss Expectancy Index using the specified formula:
        LEI = Exp_o × t_o × f_o × SCR_normalizado

        With climate-adjusted rate: t_o_clim = t_o × (1 + γ·SCR)^δ

        Args:
            property_exposure: Property exposure information
            region_id: Region identifier for sinistrality data
            scr_score: Current SCR score
            custom_occupational_factor: Custom occupational factor (if different from property type)
            custom_gamma: Custom sensitivity coefficient γ
            custom_delta: Custom exponentiality coefficient δ

        Returns:
            LEIResult with complete calculation breakdown
        """
        # Get regional data
        regional_data = self.get_regional_data(region_id)
        if not regional_data:
            raise ValueError(f"No sinistrality data found for region: {region_id}")

        # Get base rate from regional data
        base_rate = regional_data.historical_sinistrality_rate

        # Use custom coefficients if provided, otherwise use regional defaults
        gamma = (
            custom_gamma
            if custom_gamma is not None
            else regional_data.climate_sensitivity_gamma
        )
        delta = (
            custom_delta
            if custom_delta is not None
            else regional_data.climate_exponentiality_delta
        )

        # Calculate climate-adjusted rate
        climate_adjusted_rate = self.calculate_climate_adjusted_rate(
            base_rate, scr_score, gamma, delta
        )

        # Get occupational factor (f_o)
        if custom_occupational_factor is not None:
            occupational_factor = custom_occupational_factor
        else:
            base_occupational_factor = self.occupational_factors.get(
                property_exposure.property_type.lower(), 1.0
            )
            occupational_factor = (
                base_occupational_factor * property_exposure.occupancy_factor
            )

        # Calculate normalized SCR
        normalized_scr = self.calculate_normalized_scr(scr_score)

        # Calculate LEI: Exp_o × t_o_clim × f_o × SCR_normalizado
        lei_value = (
            property_exposure.exposed_value
            * climate_adjusted_rate
            * occupational_factor
            * normalized_scr
        )

        # Apply final check to ensure reasonable values
        # Even with capping, high exposure values can create large LEI values
        # So we implement a reasonableness check
        max_reasonable_lei = (
            property_exposure.exposed_value * 5.0
        )  # Maximum 5x exposure value
        lei_value = min(lei_value, max_reasonable_lei)

        return LEIResult(
            lei_value=lei_value,
            exposed_value=property_exposure.exposed_value,
            base_sinistrality_rate=base_rate,
            climate_adjusted_rate=climate_adjusted_rate,
            occupational_factor=occupational_factor,
            normalized_scr=normalized_scr,
            climate_sensitivity_coeff=gamma,
            climate_exponentiality_coeff=delta,
            calculation_timestamp=datetime.now(),
        )


# Global instance
lei_calculator = LEICalculator()


def calculate_lei_score(
    property_exposure: PropertyExposure,
    region_id: str,
    scr_score: float,
    custom_occupational_factor: Optional[float] = None,
    custom_gamma: Optional[float] = None,
    custom_delta: Optional[float] = None,
) -> LEIResult:
    """Convenience function to calculate LEI score"""
    return lei_calculator.calculate_lei_score(
        property_exposure,
        region_id,
        scr_score,
        custom_occupational_factor,
        custom_gamma,
        custom_delta,
    )
