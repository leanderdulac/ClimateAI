"""
Climate Regime Hidden Markov Model Service
Implements time-varying HMM for climate regime transitions with climate forcing factors:
P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t)
P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)
Where θ_t = vector of climate forcings (CO₂, CH₄, aerosols)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import multivariate_normal
from sklearn.mixture import GaussianMixture

logger = logging.getLogger(__name__)


@dataclass
class ClimateRegimeState:
    """Represents a climate regime state"""

    state_id: int
    mean: np.ndarray
    covariance: np.ndarray
    description: str


class ClimateHMMService:
    """
    Service implementing Hidden Markov Model for climate regime transitions
    with climate forcing factors affecting transition probabilities
    P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t)
    P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)
    Where θ_t = [CO₂, CH₄, aerosols]
    """

    def __init__(self):
        self.n_states = 0
        self.transition_matrices = (
            {}
        )  # Will store A(ΔT_t) for different temperature changes
        self.emission_means = (
            {}
        )  # μ_j(θ_t) - state means that depend on climate forcings
        self.emission_covariances = {}  # Σ_j - state covariances
        self.current_state_probs = None
        self.forcing_sensitivities = (
            {}
        )  # How sensitive transition probabilities are to forcing
        self.regime_descriptions = {
            0: "Cool/Precipitous",
            1: "Warm/Dry",
            2: "Hot/Arid",
            3: "Variable/Moderate",
        }

    def estimate_transition_matrix(
        self,
        climate_forcing: float,
        base_transition_matrix: np.ndarray,
        sensitivity_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Estimate time-varying transition matrix A(ΔT_t) based on climate forcing

        Args:
            climate_forcing: Climate forcing factor (e.g., temperature change ΔT_t)
            base_transition_matrix: Base transition matrix A^0
            sensitivity_matrix: Sensitivity matrix S where A(ΔT_t) ≈ A^0 + S * ΔT_t

        Returns:
            Adjusted transition matrix A(ΔT_t)
        """
        # Adjust base transition matrix based on climate forcing
        adjusted_matrix = base_transition_matrix + sensitivity_matrix * climate_forcing

        # Ensure rows sum to 1 (re-normalize)
        row_sums = np.sum(adjusted_matrix, axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        adjusted_matrix = adjusted_matrix / row_sums

        # Ensure non-negative probabilities
        adjusted_matrix = np.clip(adjusted_matrix, 0, 1)

        return adjusted_matrix

    def calculate_emission_mean(
        self, state: int, climate_forcings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate state-dependent emission mean μ_j(θ_t) that depends on climate forcings

        Args:
            state: Current regime state
            climate_forcings: Climate forcing vector θ_t = [CO₂, CH₄, aerosols]

        Returns:
            Emission mean vector for the given state and forcings
        """
        # Base mean for this state
        base_mean = np.array(
            [20.0, 10.0, 1013.0]
        )  # [temperature, precipitation, pressure] - example

        # Forcing-dependent adjustments
        # Each forcing component affects the mean differently based on climate physics
        co2_effect = climate_forcings[0] * 0.02  # CO₂ increases temp
        ch4_effect = climate_forcings[1] * 0.01  # CH₄ also increases temp
        aerosol_effect = climate_forcings[2] * -0.005  # Aerosols decrease temp

        # State-specific response
        state_multiplier = np.array(
            [1.0, 0.5, 0.8]
        )  # Different for each observed variable
        if state == 0:  # Cool/Precipitous
            state_multiplier = np.array([0.7, 1.5, 1.0])  # Cooler, more precipitation
        elif state == 1:  # Warm/Dry
            state_multiplier = np.array([1.3, 0.3, 0.95])  # Warmer, less precipitation
        elif state == 2:  # Hot/Arid
            state_multiplier = np.array([1.8, 0.1, 0.98])  # Hot, very dry
        elif state == 3:  # Variable/Moderate
            state_multiplier = np.array([1.0, 1.0, 1.0])  # Baseline

        forcing_adjustment = np.array(
            [
                co2_effect + ch4_effect + aerosol_effect,
                ch4_effect * 0.3,  # CH₄ also affects precipitation
                aerosol_effect * 0.1,
            ]
        )  # Aerosols slightly affect pressure

        return base_mean * state_multiplier + forcing_adjustment

    def compute_regime_transition_probabilities(
        self,
        current_forcing: np.ndarray,
        previous_temperatures: List[float],
        n_states: int = 4,
    ) -> Dict[str, Any]:
        """
        Compute regime transition probabilities based on climate forcings

        Args:
            current_forcing: Climate forcing vector θ_t = [CO₂, CH₄, aerosols]
            previous_temperatures: Recent temperature history
            n_states: Number of climate regimes

        Returns:
            Dictionary with transition probabilities and regime information
        """
        # Define base transition matrix (typical climate regime transitions)
        # State 0: Cool/Precipitous, State 1: Warm/Dry, State 2: Hot/Arid, State 3: Variable/Moderate
        base_transition = np.array(
            [
                [0.8, 0.15, 0.03, 0.02],  # From Cool/Precipitous
                [0.1, 0.7, 0.15, 0.05],  # From Warm/Dry
                [0.02, 0.15, 0.8, 0.03],  # From Hot/Arid
                [0.15, 0.2, 0.1, 0.55],  # From Variable/Moderate
            ]
        )

        # Sensitivity matrix: how transitions change with forcing
        sensitivity_matrix = np.array(
            [
                [-0.05, 0.04, 0.01, 0.0],  # From Cool/Precipitous
                [0.02, -0.03, 0.05, -0.04],  # From Warm/Dry
                [0.01, 0.03, -0.06, 0.02],  # From Hot/Arid
                [0.01, 0.01, 0.01, -0.03],  # From Variable/Moderate
            ]
        )

        # Calculate recent temperature change as forcing indicator
        if len(previous_temperatures) > 1:
            temp_change = previous_temperatures[-1] - previous_temperatures[-2]
        else:
            temp_change = 0.0

        # Estimate transition matrix based on forcing
        transition_matrix = self.estimate_transition_matrix(
            temp_change, base_transition, sensitivity_matrix
        )

        # Calculate climate sensitivity parameters
        co2_equiv = (
            current_forcing[0] * 1.0 + current_forcing[1] * 25 * 0.001
        )  # CH₄ is ~25x CO₂ over 100 years
        co2_equiv += current_forcing[2] * -0.3  # Aerosols have negative forcing

        # Adjust transition matrix based on cumulative forcing
        forcing_factor = max(
            0.1, min(2.0, 1.0 + co2_equiv * 0.01)
        )  # Limit to 10% - 200% adjustment
        adjusted_transition = transition_matrix * forcing_factor
        # Renormalize rows
        row_sums = np.sum(adjusted_transition, axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        adjusted_transition = adjusted_transition / row_sums

        return {
            "transition_matrix": adjusted_transition.tolist(),
            "base_transition_matrix": base_transition.tolist(),
            "sensitivity_matrix": sensitivity_matrix.tolist(),
            "current_forcing": current_forcing.tolist(),
            "temperature_change": temp_change,
            "co2_equivalent_forcing": co2_equiv,
            "n_states": n_states,
            "regime_names": [
                self.regime_descriptions.get(i, f"Regime {i}") for i in range(n_states)
            ],
        }

    def compute_emission_probabilities(
        self, observations: np.ndarray, current_forcing: np.ndarray, n_states: int = 4
    ) -> Dict[str, Any]:
        """
        Compute emission probabilities P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)

        Args:
            observations: Observed climate data [temp, precip, pressure, ...]
            current_forcing: Climate forcing vector θ_t = [CO₂, CH₄, aerosols]
            n_states: Number of climate regimes

        Returns:
            Dictionary with emission probabilities for each state
        """
        emission_probs = {}
        means = []
        covariances = []

        for state in range(n_states):
            # Calculate state-specific mean based on climate forcings
            mean = self.calculate_emission_mean(state, current_forcing)
            means.append(mean)

            # Set state-specific covariance (this could be learned from data)
            if state == 0:  # Cool/Precipitous regime
                cov = np.array([[2.0, 0.5, 0.1], [0.5, 25.0, 0.5], [0.1, 0.5, 10.0]])
            elif state == 1:  # Warm/Dry regime
                cov = np.array([[1.5, 0.2, 0.1], [0.2, 10.0, 0.2], [0.1, 0.2, 8.0]])
            elif state == 2:  # Hot/Arid regime
                cov = np.array([[2.5, 0.1, 0.1], [0.1, 5.0, 0.1], [0.1, 0.1, 6.0]])
            else:  # Variable/Moderate regime
                cov = np.array([[3.0, 1.0, 0.5], [1.0, 40.0, 1.0], [0.5, 1.0, 15.0]])

            covariances.append(cov)

            # Calculate emission probability using multivariate normal
            try:
                prob = multivariate_normal.pdf(observations, mean=mean, cov=cov)
                emission_probs[f"state_{state}"] = float(prob)
            except Exception as e:
                logger.warning(
                    f"Error computing emission probability for state {state}: {e}"
                )
                emission_probs[f"state_{state}"] = 0.01  # Default small probability

        return {
            "emission_probabilities": emission_probs,
            "state_means": [mean.tolist() for mean in means],
            "state_covariances": [cov.tolist() for cov in covariances],
            "current_forcing": current_forcing.tolist(),
            "observations": (
                observations.tolist()
                if isinstance(observations, np.ndarray)
                else observations
            ),
        }

    def viterbi_decode(
        self,
        observations: List[np.ndarray],
        transition_matrices: List[np.ndarray],
        emission_probs: List[Dict[str, float]],
        initial_probs: Optional[np.ndarray] = None,
    ) -> List[int]:
        """
        Viterbi algorithm to find the most likely sequence of climate regimes

        Args:
            observations: Sequence of observed climate data
            transition_matrices: Sequence of transition matrices A(ΔT_t)
            emission_probs: Sequence of emission probabilities for each state
            initial_probs: Initial state probabilities

        Returns:
            Most likely sequence of climate regime states
        """
        n_time_steps = len(observations)
        if n_time_steps == 0:
            return []

        n_states = len(emission_probs[0]) if emission_probs else 4

        if initial_probs is None:
            initial_probs = np.ones(n_states) / n_states

        # Initialize Viterbi table and path
        viterbi_table = np.zeros((n_time_steps, n_states))
        path_table = np.zeros((n_time_steps, n_states), dtype=int)

        # Initialize first time step
        for state in range(n_states):
            emission_prob = emission_probs[0].get(f"state_{state}", 0.01)
            viterbi_table[0, state] = initial_probs[state] * emission_prob

        # Forward pass
        for t in range(1, n_time_steps):
            for j in range(n_states):
                emission_prob = emission_probs[t].get(f"state_{j}", 0.01)

                # Find best previous state
                state_probs = []
                for i in range(n_states):
                    prob = (
                        viterbi_table[t - 1, i]
                        * transition_matrices[t - 1][i, j]
                        * emission_prob
                    )
                    state_probs.append(prob)

                best_prob_idx = np.argmax(state_probs)
                viterbi_table[t, j] = state_probs[best_prob_idx]
                path_table[t, j] = best_prob_idx

        # Backward pass to find optimal path
        path = [0] * n_time_steps
        path[n_time_steps - 1] = int(np.argmax(viterbi_table[n_time_steps - 1]))

        for t in range(n_time_steps - 2, -1, -1):
            path[t] = path_table[t + 1, path[t + 1]]

        return path

    def compute_climate_regime_model(
        self,
        climate_observations: List[List[float]],
        climate_forcings: List[List[float]],
        temperatures_history: List[float],
        n_states: int = 4,
    ) -> Dict[str, Any]:
        """
        Complete climate regime Hidden Markov Model:
        P(S_t = j | S_{t-1} = i) = A_ij(ΔT_t)
        P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)
        Where θ_t = [CO₂, CH₄, aerosols]

        Args:
            climate_observations: Sequence of [temperature, precipitation, pressure, ...]
            climate_forcings: Sequence of [CO₂, CH₄, aerosols] forcing vectors
            temperatures_history: Historical temperature data for transition calculations
            n_states: Number of climate regimes

        Returns:
            Complete HMM analysis results
        """
        if not climate_observations or not climate_forcings:
            raise ValueError("Climate observations and forcings must be provided")

        # Process each time step
        transition_matrices = []
        emission_probabilities = []

        for t in range(len(climate_observations)):
            obs = np.array(climate_observations[t])
            forcing = np.array(climate_forcings[t])

            # Get subset of temperature history for this time step
            temp_hist_start = max(0, t - 10)  # Use last 10 temperature values
            current_temp_hist = temperatures_history[temp_hist_start : t + 1]
            if len(current_temp_hist) < 2:
                current_temp_hist = (
                    temperatures_history[:2]
                    if len(temperatures_history) >= 2
                    else [20.0, 20.0]
                )

            # Calculate transition probabilities for this time step
            transition_info = self.compute_regime_transition_probabilities(
                forcing, current_temp_hist, n_states
            )
            transition_matrices.append(np.array(transition_info["transition_matrix"]))

            # Calculate emission probabilities for this time step
            emission_info = self.compute_emission_probabilities(obs, forcing, n_states)
            emission_probabilities.append(emission_info["emission_probabilities"])

        # Run Viterbi to find most likely regime sequence
        if len(transition_matrices) > 1:
            initial_probs = np.ones(n_states) / n_states
            regime_sequence = self.viterbi_decode(
                climate_observations,
                transition_matrices,
                emission_probabilities,
                initial_probs,
            )
        else:
            # If only one time step, pick the most probable state
            if emission_probabilities:
                probs = list(emission_probabilities[0].values())
                best_state = probs.index(max(probs))
                regime_sequence = [best_state]
            else:
                regime_sequence = [0]

        # Calculate regime statistics
        regime_counts = {}
        for regime in regime_sequence:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1

        return {
            "regime_sequence": regime_sequence,
            "regime_statistics": {
                "regime_counts": regime_counts,
                "regime_durations": self._calculate_regime_durations(regime_sequence),
                "dominant_regime": (
                    max(set(regime_sequence), key=regime_sequence.count)
                    if regime_sequence
                    else 0
                ),
                "regime_switches": self._count_regime_switches(regime_sequence),
            },
            "transition_matrices": [tm.tolist() for tm in transition_matrices],
            "emission_probabilities": emission_probabilities,
            "regime_descriptions": {
                i: self.regime_descriptions.get(i, f"Regime {i}")
                for i in range(n_states)
            },
            "n_states": n_states,
            "n_observations": len(climate_observations),
            "climate_forcing_analysis": {
                "mean_co2": (
                    np.mean([forcing[0] for forcing in climate_forcings])
                    if climate_forcings
                    else 0
                ),
                "mean_ch4": (
                    np.mean([forcing[1] for forcing in climate_forcings])
                    if climate_forcings
                    else 0
                ),
                "mean_aerosols": (
                    np.mean([forcing[2] for forcing in climate_forcings])
                    if climate_forcings
                    else 0
                ),
            },
        }

    def _calculate_regime_durations(self, regime_sequence: List[int]) -> List[int]:
        """
        Calculate consecutive duration of each regime in the sequence
        """
        if not regime_sequence:
            return []

        durations = []
        current_regime = regime_sequence[0]
        current_duration = 1

        for i in range(1, len(regime_sequence)):
            if regime_sequence[i] == current_regime:
                current_duration += 1
            else:
                durations.append(current_duration)
                current_regime = regime_sequence[i]
                current_duration = 1

        durations.append(current_duration)  # Add last duration
        return durations

    def _count_regime_switches(self, regime_sequence: List[int]) -> int:
        """
        Count the number of regime transitions in the sequence
        """
        if len(regime_sequence) < 2:
            return 0

        switches = 0
        for i in range(1, len(regime_sequence)):
            if regime_sequence[i] != regime_sequence[i - 1]:
                switches += 1

        return switches


# Global instance
climate_hmm_service = ClimateHMMService()


# Convenience functions for API integration
def compute_regime_transition_probabilities(
    current_forcing: List[float], previous_temperatures: List[float], n_states: int = 4
) -> Dict[str, Any]:
    """Compute regime transition probabilities based on climate forcings"""
    return climate_hmm_service.compute_regime_transition_probabilities(
        np.array(current_forcing), previous_temperatures, n_states
    )


def compute_emission_probabilities(
    observations: List[float], current_forcing: List[float], n_states: int = 4
) -> Dict[str, Any]:
    """Compute emission probabilities P(O_t | S_t = j) = N(μ_j(θ_t), Σ_j)"""
    return climate_hmm_service.compute_emission_probabilities(
        np.array(observations), np.array(current_forcing), n_states
    )


def compute_climate_regime_model(
    climate_observations: List[List[float]],
    climate_forcings: List[List[float]],
    temperatures_history: List[float],
    n_states: int = 4,
) -> Dict[str, Any]:
    """Complete climate regime Hidden Markov Model analysis"""
    return climate_hmm_service.compute_climate_regime_model(
        climate_observations, climate_forcings, temperatures_history, n_states
    )
