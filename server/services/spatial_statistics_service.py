"""
Advanced Spatial Statistics and Geospatial Analysis Service
Implements KDE, spatial correlation, and geospatial exposure modeling for climate risk
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import haversine_distances
from sklearn.neighbors import KernelDensity

logger = logging.getLogger(__name__)


@dataclass
class SpatialRiskMetrics:
    """Metrics for spatial risk assessment"""

    kde_density: float
    spatial_correlation: float
    cluster_risk: float
    distance_to_centroid: float
    exposure_density: float


class SpatialStatisticsService:
    """
    Service implementing advanced spatial statistics including:
    - Kernel Density Estimation (KDE) for exposure modeling
    - Spatial correlation analysis
    - Geospatial clustering for risk zones
    """

    def __init__(self):
        self.kde_models = {}
        self.spatial_models = {}

    def calculate_kernel_density_estimation(
        self,
        coordinates: List[Tuple[float, float]],
        values: List[float],
        bandwidth: float = 0.5,
    ) -> np.ndarray:
        """
        Calculate Kernel Density Estimation for spatial exposure modeling

        Args:
            coordinates: List of (latitude, longitude) tuples
            values: Associated values for each coordinate (e.g., asset values, risk scores)
            bandwidth: KDE bandwidth parameter

        Returns:
            KDE values for each coordinate
        """
        if len(coordinates) < 2:
            raise ValueError("Need at least 2 coordinates for KDE")

        # Convert coordinates to array
        coords_array = np.array(coordinates)

        # Create KDE model
        kde = KernelDensity(bandwidth=bandwidth, kernel="gaussian")

        # Fit KDE to coordinates weighted by values
        # Fit KDE to coordinates weighted by values
        if values is not None and len(values) == len(coordinates):
            # Use sample_weight instead of duplicating points
            # Normalize values to be positive weights if needed, though KDE handles weights directly
            weights = np.array(values)
            # Ensure non-negative weights
            weights = np.maximum(0, weights)

            kde.fit(coords_array, sample_weight=weights)
            densities = np.exp(kde.score_samples(coords_array))
        else:
            kde.fit(coords_array)
            densities = np.exp(kde.score_samples(coords_array))

        return densities

    def calculate_spatial_correlation(
        self,
        coordinates: List[Tuple[float, float]],
        values: List[float],
        max_distance: float = 100.0,
    ) -> Dict[str, float]:
        """
        Calculate spatial correlation using geographic distances

        Args:
            coordinates: List of (latitude, longitude) tuples
            values: Associated values for each coordinate
            max_distance: Maximum distance for correlation analysis

        Returns:
            Dictionary with spatial correlation metrics
        """
        if len(coordinates) < 2 or len(coordinates) != len(values):
            raise ValueError(
                "Need same number of coordinates and values, at least 2 points"
            )

        coords_array = np.array(coordinates)
        values_array = np.array(values)

        # Calculate geographic distances (approximately in km)
        distances = self._haversine_distances(coords_array)

        # Only consider pairs within max_distance
        mask = distances <= max_distance
        valid_distances = distances[mask]
        valid_value_pairs = []

        # Get value pairs for valid distances
        n = len(coords_array)
        for i in range(n):
            for j in range(i + 1, n):
                if distances[i, j] <= max_distance:
                    valid_value_pairs.append([values_array[i], values_array[j]])

        if len(valid_value_pairs) < 2:
            return {
                "spatial_correlation": 0.0,
                "avg_distance": np.mean(distances) if distances.size > 0 else 0.0,
                "correlation_range": 0.0,
                "n_valid_pairs": 0,
            }

        valid_value_pairs = np.array(valid_value_pairs)

        # Calculate spatial correlation as correlation between nearby values
        if len(valid_value_pairs) > 1:
            spatial_corr = np.corrcoef(
                valid_value_pairs[:, 0], valid_value_pairs[:, 1]
            )[0, 1]
            if np.isnan(spatial_corr):
                spatial_corr = 0.0
        else:
            spatial_corr = 0.0

        # Calculate average distance of correlated pairs
        avg_distance = np.mean(valid_distances) if len(valid_distances) > 0 else 0.0

        # Estimate correlation range (distance where correlation drops below 0.05)
        correlation_by_distance = self._calculate_correlation_by_distance(
            coords_array, values_array, max_distance
        )

        correlation_range = self._estimate_correlation_range(correlation_by_distance)

        return {
            "spatial_correlation": float(spatial_corr),
            "avg_distance": float(avg_distance),
            "correlation_range": correlation_range,
            "n_valid_pairs": len(valid_value_pairs),
        }

    def _haversine_distances(self, coords: np.ndarray) -> np.ndarray:
        """
        Calculate pairwise distances using sklearn's vectorized haversine_distances
        """
        # Convert to radians
        coords_rad = np.radians(coords)

        # Calculate pairwise distances using sklearn (returns radians)
        # Note: sklearn expects [lat, lon], which matches our input
        dists_rad = haversine_distances(coords_rad)

        # Convert to km
        r = 6371  # Earth radius in km
        return dists_rad * r

    def _calculate_correlation_by_distance(
        self, coords: np.ndarray, values: np.ndarray, max_distance: float
    ) -> Dict[float, float]:
        """
        Calculate correlation at different distance intervals
        """
        distances = self._haversine_distances(coords)
        correlations = {}

        # Define distance bins
        bins = np.arange(0, max_distance + 10, 10)

        # Pre-calculate upper triangle indices to avoid double counting and self-correlation
        triu_indices = np.triu_indices_from(distances, k=1)
        upper_distances = distances[triu_indices]

        # Create pairs matrix once: [val_i, val_j] for all i < j
        # values[triu_indices[0]] gives array of val_i
        # values[triu_indices[1]] gives array of val_j
        all_pairs = np.column_stack((values[triu_indices[0]], values[triu_indices[1]]))

        for i in range(len(bins) - 1):
            lower, upper = bins[i], bins[i + 1]

            # Find indices in the flattened upper triangle array that match distance criteria
            mask = (upper_distances >= lower) & (upper_distances < upper)

            # Filter pairs using the mask
            pairs_in_bin = all_pairs[mask]

            if len(pairs_in_bin) > 1:
                # Calculate correlation for this bin
                corr = np.corrcoef(pairs_in_bin[:, 0], pairs_in_bin[:, 1])[0, 1]
                if not np.isnan(corr):
                    correlations[upper] = corr
                else:
                    correlations[upper] = 0.0
            else:
                correlations[upper] = 0.0

        return correlations

    def _estimate_correlation_range(
        self, correlation_by_distance: Dict[float, float]
    ) -> float:
        """
        Estimate the distance where correlation drops below 0.05 (effective range)
        """
        for distance, corr in sorted(correlation_by_distance.items()):
            if abs(corr) < 0.05:
                return distance
        return max(correlation_by_distance.keys()) if correlation_by_distance else 0.0

    def geospatial_clustering(
        self,
        coordinates: List[Tuple[float, float]],
        values: List[float] = None,
        eps: float = 5.0,
        min_samples: int = 3,
    ) -> Dict[str, Any]:
        """
        Perform geospatial clustering to identify risk zones

        Args:
            coordinates: List of (latitude, longitude) tuples
            values: Associated values for clustering
            eps: Maximum distance between points in same cluster
            min_samples: Minimum samples in neighborhood for core point

        Returns:
            Dictionary with clustering results and risk metrics
        """
        coords_array = np.array(coordinates)

        if values is not None and len(values) == len(coordinates):
            # Combine coordinates with values for clustering
            data_for_clustering = np.column_stack([coords_array, values])
        else:
            data_for_clustering = coords_array

        # Perform DBSCAN clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(data_for_clustering)
        labels = clustering.labels_

        # Calculate cluster statistics
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (
            1 if -1 in labels else 0
        )  # Exclude noise points
        n_noise = list(labels).count(-1)

        # Calculate cluster risk metrics
        clusters_info = []
        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue

            mask = labels == label
            cluster_coords = coords_array[mask]
            cluster_values = (
                np.array(values)[mask] if values else np.ones(len(cluster_coords))
            )

            # Calculate cluster centroid
            centroid_lat = np.mean(cluster_coords[:, 0])
            centroid_lon = np.mean(cluster_coords[:, 1])

            # Calculate cluster statistics
            cluster_info = {
                "cluster_id": int(label),
                "size": int(np.sum(mask)),
                "centroid": {"lat": float(centroid_lat), "lon": float(centroid_lon)},
                "avg_value": float(np.mean(cluster_values)),
                "std_value": float(np.std(cluster_values)),
                "total_value": float(np.sum(cluster_values)),
                "density": float(
                    len(cluster_coords)
                    / max(1, self._calculate_cluster_area(cluster_coords))
                ),
            }
            clusters_info.append(cluster_info)

        return {
            "n_clusters": n_clusters,
            "n_noise_points": n_noise,
            "total_points": len(coordinates),
            "clusters": clusters_info,
            "labels": labels.tolist(),
            "clustering_params": {"eps": eps, "min_samples": min_samples},
        }

    def _calculate_cluster_area(self, coords: np.ndarray) -> float:
        """
        Calculate approximate area of a cluster using bounding box
        """
        if len(coords) < 2:
            return 0.0

        min_lat, max_lat = np.min(coords[:, 0]), np.max(coords[:, 0])
        min_lon, max_lon = np.min(coords[:, 1]), np.max(coords[:, 1])

        # Approximate area using haversine distance between extremes
        area = self._haversine_distance(min_lat, min_lon, max_lat, max_lon) ** 2
        return area

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate haversine distance between two points
        """
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Earth radius in km
        return r * c

    def calculate_exposure_density(
        self,
        coordinates: List[Tuple[float, float]],
        asset_values: List[float],
        radius: float = 5.0,
    ) -> List[float]:
        """
        Calculate exposure density around each coordinate point

        Args:
            coordinates: List of (latitude, longitude) tuples
            asset_values: Asset values at each coordinate
            radius: Radius in km to calculate density

        Returns:
            List of exposure densities for each coordinate
        """
        coords_array = np.array(coordinates)
        values_array = np.array(asset_values)

        # Create KDTree for efficient nearest neighbor search
        tree = cKDTree(coords_array)

        densities = []
        for i, coord in enumerate(coords_array):
            # Find points within radius
            indices = tree.query_ball_point(
                coord, r=radius / 111.0
            )  # Approximate km to degrees

            # Calculate total exposure within radius
            total_exposure = np.sum(values_array[indices])
            area = np.pi * (radius**2)
            density = total_exposure / area if area > 0 else 0.0
            densities.append(density)

        return densities

    def combined_spatial_risk_assessment(
        self,
        coordinates: List[Tuple[float, float]],
        asset_values: List[float],
        risk_scores: List[float],
    ) -> Dict[str, Any]:
        """
        Perform combined spatial risk assessment using all methods

        Args:
            coordinates: List of (latitude, longitude) tuples
            asset_values: Asset values at each location
            risk_scores: Risk scores for each location

        Returns:
            Comprehensive spatial risk assessment
        """
        # Calculate KDE for exposure density
        kde_values = self.calculate_kernel_density_estimation(
            coordinates, asset_values, bandwidth=1.0
        )

        # Calculate spatial correlation
        spatial_corr = self.calculate_spatial_correlation(
            coordinates, risk_scores, max_distance=50.0
        )

        # Perform geospatial clustering
        clusters = self.geospatial_clustering(
            coordinates, risk_scores, eps=10.0, min_samples=2
        )

        # Calculate exposure densities
        exposure_densities = self.calculate_exposure_density(
            coordinates, asset_values, radius=5.0
        )

        # Combine all metrics
        combined_metrics = []
        for i in range(len(coordinates)):
            metric = SpatialRiskMetrics(
                kde_density=float(kde_values[i]),
                spatial_correlation=spatial_corr["spatial_correlation"],
                cluster_risk=float(risk_scores[i]) if i < len(risk_scores) else 0.0,
                distance_to_centroid=0.0,  # To be calculated based on cluster
                exposure_density=exposure_densities[i],
            )
            combined_metrics.append(metric)

        return {
            "kernel_density_estimation": kde_values.tolist(),
            "spatial_correlation_analysis": spatial_corr,
            "geospatial_clustering": clusters,
            "exposure_density": exposure_densities,
            "combined_risk_scores": [
                m.kde_density * m.exposure_density for m in combined_metrics
            ],
            "total_exposure": float(np.sum(asset_values)),
            "weighted_risk_score": float(np.average(risk_scores, weights=asset_values)),
            "timestamp": datetime.now().isoformat(),
        }

    def spatial_gaussian_process_model(
        self,
        coordinates: List[Tuple[float, float]],
        observations: List[float],
        covariates: Optional[List[List[float]]] = None,
        nugget: float = 0.1,
        range_param: float = 1.0,
        variance_param: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Implement the spatial Gaussian Process model:
        Z(s) = X(s)β + W(s) + ε(s)
        W(s) ~ Gaussian Process(0, Σ(θ))
        Σ_ij = σ² exp(-||s_i - s_j||/φ) + η²·I(i=j)

        Args:
            coordinates: List of (latitude, longitude) tuples
            observations: Observed values at each coordinate
            covariates: Optional matrix of covariates [n_samples, n_covariates]
            nugget: Nugget effect parameter (η²)
            range_param: Range parameter (φ)
            variance_param: Variance parameter (σ²)

        Returns:
            Dictionary with GP model parameters and predictions
        """
        coords_array = np.array(coordinates)
        obs_array = np.array(observations)

        if len(coords_array) != len(obs_array):
            raise ValueError("Coordinates and observations must have same length")

        n = len(coords_array)

        # Calculate pairwise distances
        distances = self._haversine_distances(coords_array)

        # Build covariance matrix Σ
        # Σ_ij = σ² exp(-||s_i - s_j||/φ) + η²·I(i=j)
        cov_matrix = variance_param * np.exp(-distances / range_param)

        # Add nugget effect (diagonal elements)
        np.fill_diagonal(cov_matrix, cov_matrix.diagonal() + nugget)

        # If covariates provided, solve Z(s) = X(s)β + W(s) + ε(s)
        if covariates is not None and len(covariates) == len(obs_array):
            X = np.array(covariates)
            # Add intercept term
            X = np.column_stack([np.ones(n), X])  # [intercept, covariates]

            # Estimate β using generalized least squares approach
            try:
                # Use Cholesky decomposition for stability and speed
                # Σ = L L^T
                L = np.linalg.cholesky(cov_matrix)

                # Solve Σ^(-1) Z = (L L^T)^(-1) Z = (L^T)^(-1) L^(-1) Z
                # Let y = L^(-1) Z => L y = Z (solve for y)
                # Let x = (L^T)^(-1) y => L^T x = y (solve for x)
                # In scipy/numpy: cho_solve((L, lower=True), Z) does exactly Σ^(-1) Z
                from scipy.linalg import cho_solve

                # Calculate X^T Σ^(-1) X
                # First calculate Σ^(-1) X
                Sigma_inv_X = cho_solve((L, True), X)

                # Then X^T (Σ^(-1) X)
                Xt_Sigma_inv_X = X.T @ Sigma_inv_X

                # Calculate X^T Σ^(-1) Z
                # First calculate Σ^(-1) Z
                Sigma_inv_Z = cho_solve((L, True), obs_array)
                Xt_Sigma_inv_Z = X.T @ Sigma_inv_Z

                # Solve for β: (X^T Σ^(-1) X) β = X^T Σ^(-1) Z
                beta_est = np.linalg.solve(Xt_Sigma_inv_X, Xt_Sigma_inv_Z)

                # Residuals after removing covariate effect
                Z_trend_removed = obs_array - X @ beta_est

            except np.linalg.LinAlgError:
                # Fallback to OLS if Cholesky fails (matrix not positive definite)
                beta_est = np.linalg.lstsq(X, obs_array, rcond=None)[0]
                Z_trend_removed = obs_array - X @ beta_est
        else:
            # No covariates, just pure GP
            X = np.ones((n, 1))  # Just intercept
            beta_est = np.array([np.mean(obs_array)])
            Z_trend_removed = obs_array - np.mean(obs_array)

        # Perform prediction at observed locations (for validation)
        try:
            # Calculate prediction using kriging
            # For each point i: prediction = X[i]β̂ + Σ[i,-i] Σ[-i,-i]^(-1) (Z[-i] - X[-i]β̂)
            predictions = []
            prediction_variances = []

            for i in range(n):
                # Leave-one-out approach for prediction at each location
                mask = np.ones(n, dtype=bool)
                mask[i] = False

                # Covariance between point i and all other points
                cov_i_others = cov_matrix[i, mask]

                # Covariance matrix for all other points
                cov_others = cov_matrix[mask][:, mask]

                try:
                    # Inverse of others covariance matrix
                    cov_others_inv = np.linalg.inv(cov_others)

                    # Calculate leave-one-out prediction
                    z_others = (
                        Z_trend_removed[mask]
                        if covariates is None
                        else Z_trend_removed[mask]
                    )
                    x_i = X[i : i + 1] if covariates is not None else X[i : i + 1]

                    # Simple kriging: prediction = x_i * β̂ + weights * residuals
                    weights = cov_i_others @ cov_others_inv
                    residual_pred = weights @ z_others
                    pred_value = x_i @ beta_est + residual_pred

                    # Prediction variance
                    pred_var = variance_param - weights @ cov_i_others.T

                    predictions.append(
                        float(pred_value[0])
                        if hasattr(pred_value, "__len__")
                        else float(pred_value)
                    )
                    prediction_variances.append(float(pred_var))

                except np.linalg.LinAlgError:
                    # Fallback to nearest neighbor if matrix is singular
                    distances_i = distances[i]
                    distances_i[i] = np.inf  # Exclude self
                    nearest_idx = np.argmin(distances_i)
                    predictions.append(float(obs_array[nearest_idx]))
                    prediction_variances.append(
                        float(nugget)
                    )  # Uncertainty of nearest point

        except Exception:
            # If kriging fails completely, use simple mean
            predictions = [float(np.mean(obs_array))] * n
            prediction_variances = [float(np.var(obs_array))] * n

        return {
            "model_type": "spatial_gaussian_process",
            "parameters": {
                "nugget": float(nugget),  # η² (nugget effect)
                "range": float(range_param),  # φ (range parameter)
                "variance": float(variance_param),  # σ² (partial sill)
            },
            "covariates_used": covariates is not None,
            "estimated_beta": beta_est.tolist(),
            "covariance_matrix": {
                "min_distance": float(
                    np.min(distances[np.triu_indices_from(distances, k=1)])
                    if n > 1
                    else 0
                ),
                "max_distance": float(np.max(distances)),
                "mean_distance": float(np.mean(distances)),
            },
            "predictions": predictions,
            "prediction_variances": prediction_variances,
            "residuals": (obs_array - np.array(predictions)).tolist(),
            "rmse": float(np.sqrt(np.mean((obs_array - np.array(predictions)) ** 2))),
            "n_observations": n,
            "coordinates": coordinates,
            "observations": observations,
        }

    def predict_at_new_locations(
        self,
        fitted_model: Dict[str, Any],
        new_coordinates: List[Tuple[float, float]],
        new_covariates: Optional[List[List[float]]] = None,
    ) -> Dict[str, Any]:
        """
        Predict at new locations using a fitted spatial GP model

        Args:
            fitted_model: Previously fitted spatial GP model
            new_coordinates: List of new (lat, lon) coordinates for prediction
            new_covariates: Covariates for new locations

        Returns:
            Predictions and uncertainties for new locations
        """
        # Extract model parameters from fitted model
        coords_array = np.array(fitted_model.get("coordinates", []))
        obs_array = np.array(fitted_model.get("observations", []))
        beta_est = np.array(fitted_model.get("estimated_beta", [np.mean(obs_array)]))
        params = fitted_model.get("parameters", {})

        nugget = params.get("nugget", 0.1)
        range_param = params.get("range", 1.0)
        variance_param = params.get("variance", 1.0)

        n_existing = len(coords_array)
        n_new = len(new_coordinates)

        if n_existing == 0:
            raise ValueError("Cannot predict from an empty fitted model")

        # Calculate distances between new and existing points
        new_coords_array = np.array(new_coordinates)
        all_distances = self._haversine_distances(
            np.vstack([coords_array, new_coords_array])
        )
        cross_distances = all_distances[:n_existing, n_existing:]  # Existing to new
        new_distances = all_distances[n_existing:, n_existing:]  # New to new

        # Build cross-covariance matrix
        cross_cov = variance_param * np.exp(-cross_distances / range_param)

        # Build existing covariance matrix
        existing_distances = all_distances[:n_existing, :n_existing]
        existing_cov = variance_param * np.exp(-existing_distances / range_param)
        np.fill_diagonal(existing_cov, existing_cov.diagonal() + nugget)

        # Calculate residuals from original fit
        predictions = np.array(fitted_model["predictions"])
        residuals = obs_array - predictions

        # Make predictions at new locations
        new_predictions = []
        new_prediction_vars = []

        # Get inverse of existing covariance matrix
        try:
            existing_cov_inv = np.linalg.inv(existing_cov)
        except np.linalg.LinAlgError:
            existing_cov_inv = np.linalg.pinv(existing_cov)

        for j in range(n_new):
            # Cross-covariance for this new point
            cross_cov_j = cross_cov[:, j]

            # Calculate kriging weights
            weights = cross_cov_j @ existing_cov_inv

            # Prediction: trend + kriging adjustment
            if new_covariates is not None and j < len(new_covariates):
                new_x = np.array([1.0] + new_covariates[j])  # Add intercept
            else:
                new_x = np.array([1.0])  # Just intercept
                if len(beta_est) > 1:
                    new_x = np.append(
                        new_x, np.zeros(len(beta_est) - 1)
                    )  # Pad with zeros

            trend_pred = new_x @ beta_est
            kriging_pred = weights @ residuals
            final_pred = trend_pred + kriging_pred

            # Prediction variance
            existing_var_reduction = weights @ cross_cov_j
            pred_var = variance_param + nugget - existing_var_reduction

            new_predictions.append(float(final_pred))
            new_prediction_vars.append(float(max(0, pred_var)))  # Ensure non-negative

        return {
            "new_coordinates": new_coordinates,
            "new_predictions": new_predictions,
            "prediction_variances": new_prediction_vars,
            "model_parameters_used": params,
        }


# Global instance
spatial_statistics_service = SpatialStatisticsService()


# Convenience functions for API integration
def calculate_kernel_density_estimation(
    coordinates: List[Tuple[float, float]], values: List[float], bandwidth: float = 0.5
) -> np.ndarray:
    """Calculate Kernel Density Estimation for spatial exposure modeling"""
    return spatial_statistics_service.calculate_kernel_density_estimation(
        coordinates, values, bandwidth
    )


def calculate_spatial_correlation(
    coordinates: List[Tuple[float, float]],
    values: List[float],
    max_distance: float = 100.0,
) -> Dict[str, float]:
    """Calculate spatial correlation using geographic distances"""
    return spatial_statistics_service.calculate_spatial_correlation(
        coordinates, values, max_distance
    )


def geospatial_clustering(
    coordinates: List[Tuple[float, float]], values: List[float] = None
) -> Dict[str, Any]:
    """Perform geospatial clustering to identify risk zones"""
    return spatial_statistics_service.geospatial_clustering(
        coordinates, values, eps=5.0, min_samples=3
    )


def combined_spatial_risk_assessment(
    coordinates: List[Tuple[float, float]],
    asset_values: List[float],
    risk_scores: List[float],
) -> Dict[str, Any]:
    """Perform combined spatial risk assessment using all methods"""
    return spatial_statistics_service.combined_spatial_risk_assessment(
        coordinates, asset_values, risk_scores
    )


def spatial_gaussian_process_model(
    coordinates: List[Tuple[float, float]],
    observations: List[float],
    covariates: Optional[List[List[float]]] = None,
    nugget: float = 0.1,
    range_param: float = 1.0,
    variance_param: float = 1.0,
) -> Dict[str, Any]:
    """Fit a spatial Gaussian Process model: Z(s) = X(s)β + W(s) + ε(s)"""
    return spatial_statistics_service.spatial_gaussian_process_model(
        coordinates, observations, covariates, nugget, range_param, variance_param
    )


def predict_at_new_locations(
    fitted_model: Dict[str, Any],
    new_coordinates: List[Tuple[float, float]],
    new_covariates: Optional[List[List[float]]] = None,
) -> Dict[str, Any]:
    """Predict at new locations using a fitted spatial GP model"""
    return spatial_statistics_service.predict_at_new_locations(
        fitted_model, new_coordinates, new_covariates
    )
