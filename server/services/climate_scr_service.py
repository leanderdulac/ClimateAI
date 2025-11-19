"""
Climate Solvency Capital Requirement (SCR) Calculation Service
Implements: SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
Where: SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]
And: Corr_{i,j} = 0.25 se i ≠ j  [baixa correlação entre perigos]
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ClimateSCR:
    """Climate Solvency Capital Requirement result"""

    total_scr: float
    individual_scrs: List[float]
    correlation_matrix: List[List[float]]
    expected_losses: List[float]
    var_995_losses: List[float]
    calculation_timestamp: datetime
    portfolio_size: int


class ClimateSCRService:
    """
    Service implementing climate risk aggregation using correlation-based approach:
    SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
    """

    def __init__(self):
        # Default correlation factor between different peril types
        self.default_correlation = 0.25  # 25% correlation between different perils

    def calculate_individual_scr(
        self, var_995_loss: float, expected_loss: float
    ) -> float:
        """
        Calculate individual SCR component:
        SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]

        Args:
            var_995_loss: VaR at 99.5% confidence level for the event
            expected_loss: Expected loss for the event

        Returns:
            Individual SCR component
        """
        scr = var_995_loss - expected_loss
        return max(0, scr)  # SCR should not be negative

    def create_correlation_matrix(
        self, n_events: int, correlation_value: float = 0.25
    ) -> List[List[float]]:
        """
        Create correlation matrix with 0.25 for i ≠ j as specified in the formula

        Args:
            n_events: Number of climate events/risk types
            correlation_value: Correlation value for different events (default 0.25)

        Returns:
            Correlation matrix as nested list
        """
        matrix = [[0.0 for _ in range(n_events)] for _ in range(n_events)]

        for i in range(n_events):
            for j in range(n_events):
                if i == j:
                    matrix[i][j] = 1.0  # Self-correlation is always 1
                else:
                    matrix[i][
                        j
                    ] = correlation_value  # Default correlation between different perils

        return matrix

    def calculate_portfolio_scr(
        self,
        var_995_losses: List[float],
        expected_losses: List[float],
        correlation_matrix: List[List[float]] = None,
    ) -> ClimateSCR:
        """
        Calculate portfolio-level climate SCR using the correlation-based formula:
        SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]

        Args:
            var_995_losses: List of VaR 99.5% losses for each event type
            expected_losses: List of expected losses for each event type
            correlation_matrix: Correlation matrix (if None, uses default 0.25 correlations)

        Returns:
            ClimateSCR object with total SCR and components
        """
        if len(var_995_losses) != len(expected_losses):
            raise ValueError("VaR and expected loss lists must have the same length")

        n_events = len(var_995_losses)

        # Calculate individual SCR components
        individual_scrs = []
        for i in range(n_events):
            scr_i = self.calculate_individual_scr(var_995_losses[i], expected_losses[i])
            individual_scrs.append(scr_i)

        # Use provided correlation matrix or create default one
        if correlation_matrix is None:
            correlation_matrix = self.create_correlation_matrix(
                n_events, self.default_correlation
            )
        else:
            if len(correlation_matrix) != n_events or any(
                len(row) != n_events for row in correlation_matrix
            ):
                raise ValueError(f"Correlation matrix must be {n_events}x{n_events}")

        # Calculate portfolio SCR: √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
        total_sum = 0.0
        for i in range(n_events):
            for j in range(n_events):
                total_sum += (
                    correlation_matrix[i][j] * individual_scrs[i] * individual_scrs[j]
                )

        portfolio_scr = np.sqrt(total_sum)

        result = ClimateSCR(
            total_scr=portfolio_scr,
            individual_scrs=individual_scrs,
            correlation_matrix=correlation_matrix,
            expected_losses=expected_losses,
            var_995_losses=var_995_losses,
            calculation_timestamp=datetime.now(),
            portfolio_size=n_events,
        )

        logger.info(
            f"Climate SCR calculated: {portfolio_scr:,.2f} (n_events: {n_events})"
        )
        return result

    def calculate_simple_portfolio_scr(
        self, var_995_losses: List[float], expected_losses: List[float]
    ) -> ClimateSCR:
        """
        Calculate portfolio SCR with default 0.25 correlation between different perils
        This is the most common use case following the specified formula.
        """
        return self.calculate_portfolio_scr(var_995_losses, expected_losses)

    def calculate_peril_specific_scr(
        self, peril_losses: Dict[str, Dict[str, float]]
    ) -> ClimateSCR:
        """
        Calculate SCR from peril-specific data

        Args:
            peril_losses: Dictionary with structure:
                         {
                           "flood": {"var_995": 10000, "expected": 2000},
                           "wind": {"var_995": 8000, "expected": 1500},
                           ...
                         }

        Returns:
            ClimateSCR object
        """
        var_995_losses = []
        expected_losses = []

        for peril, values in peril_losses.items():
            var_995_losses.append(values["var_995"])
            expected_losses.append(values["expected"])

        return self.calculate_portfolio_scr(var_995_losses, expected_losses)


# Global instance
climate_scr_service = ClimateSCRService()


# Convenience functions for API integration
def calculate_individual_scr(var_995_loss: float, expected_loss: float) -> float:
    """Calculate individual SCR component: SCR_i = VaR_99.5% - E[loss]"""
    return climate_scr_service.calculate_individual_scr(var_995_loss, expected_loss)


def create_correlation_matrix(
    n_events: int, correlation_value: float = 0.25
) -> List[List[float]]:
    """Create correlation matrix with default 0.25 correlation between different perils"""
    return climate_scr_service.create_correlation_matrix(n_events, correlation_value)


def calculate_portfolio_scr(
    var_995_losses: List[float],
    expected_losses: List[float],
    correlation_matrix: List[List[float]] = None,
) -> ClimateSCR:
    """Calculate portfolio-level climate SCR using correlation-based formula"""
    return climate_scr_service.calculate_portfolio_scr(
        var_995_losses, expected_losses, correlation_matrix
    )


def calculate_simple_portfolio_scr(
    var_995_losses: List[float], expected_losses: List[float]
) -> ClimateSCR:
    """Calculate portfolio SCR with default 0.25 correlation between different perils"""
    return climate_scr_service.calculate_simple_portfolio_scr(
        var_995_losses, expected_losses
    )


def calculate_peril_specific_scr(
    peril_losses: Dict[str, Dict[str, float]]
) -> ClimateSCR:
    """Calculate SCR from peril-specific data with default correlations"""
    return climate_scr_service.calculate_peril_specific_scr(peril_losses)
