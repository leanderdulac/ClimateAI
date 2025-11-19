"""
Concentration Risk Calculation Service
Implements: R_concentração = √[Σ_i (x_i - x̄)² / n] · ρ_climático

Where:
- x_i = value of the premium of property i in the cluster
- x̄ = average premium of all properties in the cluster
- n = number of properties in the cluster
- ρ_climático = spatial correlation of extreme events in the neighborhood (5km)

Based on: Spatial Concentration Risk Assessment Methodology
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN

logger = logging.getLogger(__name__)


@dataclass
class PropertyInfo:
    """Information about a property in the cluster"""

    property_id: str
    premium_value: float
    latitude: float
    longitude: float
    coverage_type: str  # 'property', 'agriculture', 'industrial', etc.
    asset_value: float
    construction_type: str  # 'residential', 'commercial', 'industrial', etc.
    elevation: float  # Elevation in meters
    climate_zone: str  # Climate zone classification


@dataclass
class ConcentrationRiskResult:
    """Result of concentration risk calculation"""

    concentration_risk: float  # R_concentração
    cluster_properties: List[PropertyInfo]
    average_premium: float
    cluster_std_dev: float
    climate_correlation: float
    cluster_size: int
    spatial_distribution: Dict[str, float]  # Metrics about spatial distribution
    risk_metrics: Dict[str, float]  # Additional risk metrics
    calculation_timestamp: datetime


@dataclass
class NeighborhoodDefinition:
    """Definition of neighborhood for correlation calculation"""

    radius_km: float = 5.0
    min_properties: int = 2  # Minimum number of properties to form a cluster
    climate_event_buffer: float = 0.5  # Buffer for climate event overlap in km


class ConcentrationRiskCalculator:
    """
    Calculates concentration risk using the specified formula:
    R_concentração = √[Σ_i (x_i - x̄)² / n] · ρ_climático
    """

    def __init__(self):
        # Default climate correlation parameters
        self.default_climate_correlation = 0.6  # Default correlation for extreme events
        self.distance_decay_factor = 0.1  # How quickly correlation drops with distance

        # Climate correlation by hazard type
        self.hazard_correlation = {
            "flood": 0.8,  # Floods tend to affect wide areas
            "wind": 0.4,  # Wind hazards can be more localized
            "fire": 0.3,  # Fire hazards somewhat localized
            "hail": 0.2,  # Hail hazards can be very localized
            "drought": 0.9,  # Droughts affect very large areas
        }

    def calculate_concentration_risk(
        self,
        properties: List[PropertyInfo],
        climate_correlation: Optional[float] = None,
        hazard_type: str = "flood",
        neighborhood_def: Optional[NeighborhoodDefinition] = None,
    ) -> ConcentrationRiskResult:
        """
        Calculate concentration risk using the specified formula:
        R_concentração = √[Σ_i (x_i - x̄)² / n] · ρ_climático

        Args:
            properties: List of properties in the cluster with their premiums
            climate_correlation: Climate correlation factor (ρ_climático)
            hazard_type: Type of hazard for correlation calculation
            neighborhood_def: Definition of neighborhood radius

        Returns:
            ConcentrationRiskResult with complete risk calculation
        """
        if not properties:
            return ConcentrationRiskResult(
                concentration_risk=0.0,
                cluster_properties=[],
                average_premium=0.0,
                cluster_std_dev=0.0,
                climate_correlation=0.0,
                cluster_size=0,
                spatial_distribution={},
                risk_metrics={},
                calculation_timestamp=datetime.now(),
            )

        if neighborhood_def is None:
            neighborhood_def = NeighborhoodDefinition()

        # Calculate average premium (x̄)
        premiums = [prop.premium_value for prop in properties]
        average_premium = np.mean(premiums)

        # Calculate the standard deviation component: √[Σ_i (x_i - x̄)² / n]
        squared_differences = [(premium - average_premium) ** 2 for premium in premiums]
        variance = sum(squared_differences) / len(
            premiums
        )  # n in denominator as per formula
        sd_component = np.sqrt(variance)  # This is the standard deviation of premiums

        # Get climate correlation factor
        if climate_correlation is None:
            climate_correlation = self._calculate_climate_correlation(
                properties, neighborhood_def.radius_km, hazard_type
            )

        # Calculate final concentration risk: standard_deviation * climate_correlation
        concentration_risk = sd_component * climate_correlation

        # Calculate additional spatial distribution metrics
        spatial_metrics = self._calculate_spatial_metrics(properties)

        # Calculate additional risk metrics
        risk_metrics = {
            "cv_premium": (
                sd_component / average_premium if average_premium > 0 else 0
            ),  # Coefficient of variation
            "premium_concentration_index": self._calculate_concentration_index(
                premiums
            ),
            "total_exposure": sum(premiums),
            "max_individual_premium": max(premiums) if premiums else 0,
        }

        return ConcentrationRiskResult(
            concentration_risk=concentration_risk,
            cluster_properties=properties,
            average_premium=average_premium,
            cluster_std_dev=sd_component,  # This is the standard deviation component
            climate_correlation=climate_correlation,
            cluster_size=len(properties),
            spatial_distribution=spatial_metrics,
            risk_metrics=risk_metrics,
            calculation_timestamp=datetime.now(),
        )

    def _calculate_climate_correlation(
        self,
        properties: List[PropertyInfo],
        neighborhood_radius: float,
        hazard_type: str,
    ) -> float:
        """
        Calculate climate correlation based on spatial proximity of properties
        """
        if len(properties) < 2:
            return 0.0  # No correlation with single property

        # Get coordinates
        coords = np.array([[prop.latitude, prop.longitude] for prop in properties])

        # Calculate pairwise distances in kilometers
        distances = self._calculate_pairwise_distances(coords)

        # Get base correlation for hazard type
        base_correlation = self.hazard_correlation.get(
            hazard_type, self.default_climate_correlation
        )

        # Calculate average correlation within neighborhood radius
        neighbor_mask = distances <= neighborhood_radius
        within_radius_count = np.sum(neighbor_mask)

        if within_radius_count <= 1:
            # No neighbors, use base correlation
            return base_correlation

        # Calculate distance-weighted correlation
        correlation_matrix = np.zeros_like(distances)
        for i in range(len(distances)):
            for j in range(len(distances)):
                if i != j:
                    # Correlation decreases with distance
                    dist_factor = max(0, 1 - distances[i, j] / neighborhood_radius)
                    correlation_matrix[i, j] = base_correlation * dist_factor

        # Calculate average correlation among neighboring properties
        avg_correlation = (
            np.mean(correlation_matrix[neighbor_mask])
            if np.any(neighbor_mask)
            else base_correlation
        )

        return max(0.01, min(0.99, avg_correlation))  # Keep in reasonable range

    def _calculate_pairwise_distances(self, coords: np.ndarray) -> np.ndarray:
        """
        Calculate pairwise distances between coordinates in kilometers using haversine formula
        """
        if coords.shape[0] < 2:
            return np.array([])

        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate distance between two points in kilometers"""
            R = 6371  # Earth radius in kilometers

            phi1 = np.radians(lat1)
            phi2 = np.radians(lat2)
            delta_phi = np.radians(lat2 - lat1)
            delta_lambda = np.radians(lon2 - lon1)

            a = (
                np.sin(delta_phi / 2) ** 2
                + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2) ** 2
            )
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

            return R * c

        n = len(coords)
        distances = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                dist = haversine_distance(
                    coords[i, 0], coords[i, 1], coords[j, 0], coords[j, 1]
                )
                distances[i, j] = dist
                distances[j, i] = dist  # Symmetric matrix

        return distances

    def _calculate_spatial_metrics(
        self, properties: List[PropertyInfo]
    ) -> Dict[str, float]:
        """Calculate additional spatial distribution metrics"""
        if not properties:
            return {}

        coords = np.array([[prop.latitude, prop.longitude] for prop in properties])

        if len(coords) == 1:
            return {
                "centroid_lat": coords[0, 0],
                "centroid_lon": coords[0, 1],
                "area_km2": 0.0,
                "compactness": 1.0,
                "max_distance_km": 0.0,
            }

        # Calculate centroid
        centroid_lat = np.mean(coords[:, 0])
        centroid_lon = np.mean(coords[:, 1])

        # Calculate distances from centroid
        distances_from_centroid = []
        for lat, lon in coords:
            dist = self._calculate_pairwise_distances(
                np.array([[centroid_lat, centroid_lon], [lat, lon]])
            )[0, 1]
            distances_from_centroid.append(dist)

        # Calculate area using convex hull concept (approximation)
        # For a cluster, we can use average distance from centroid
        avg_distance = np.mean(distances_from_centroid)
        area_approx = np.pi * avg_distance**2
        max_distance = max(distances_from_centroid)

        # Compactness (ratio of area to perimeter^2, simplified)
        compactness = avg_distance / max_distance if max_distance > 0 else 1.0

        return {
            "centroid_lat": centroid_lat,
            "centroid_lon": centroid_lon,
            "area_km2": float(area_approx),
            "compactness": float(compactness),
            "max_distance_km": float(max_distance),
            "avg_distance_from_centroid_km": float(avg_distance),
            "cluster_density": len(properties)
            / (area_approx if area_approx > 0 else 1),  # Properties per km²
        }

    def _calculate_concentration_index(self, premiums: List[float]) -> float:
        """
        Calculate concentration index based on premium distribution
        """
        if len(premiums) <= 1:
            return 0.0

        # Herfindahl-Hirschman Index (HHI) adapted for premium concentration
        total_premium = sum(premiums)
        if total_premium == 0:
            return 0.0

        shares = [p / total_premium for p in premiums]
        hhi = sum(s**2 for s in shares)

        # Normalize to 0-1 scale (HHI ranges from 1/n to 1)
        min_hhi = 1.0 / len(premiums)  # Perfect equality
        max_hhi = 1.0  # Perfect concentration

        if max_hhi == min_hhi:
            return 0.0

        normalized_concentration = (hhi - min_hhi) / (max_hhi - min_hhi)
        return normalized_concentration

    def identify_clusters(
        self,
        all_properties: List[PropertyInfo],
        min_cluster_size: int = 3,
        neighborhood_radius: float = 5.0,
    ) -> List[List[PropertyInfo]]:
        """
        Identify clusters of properties based on geographic proximity

        Args:
            all_properties: List of all properties to analyze
            min_cluster_size: Minimum number of properties to form a cluster
            neighborhood_radius: Radius in km to consider for clustering

        Returns:
            List of clusters, where each cluster is a list of properties
        """
        if not all_properties:
            return []

        # Extract coordinates
        coords = np.array([[prop.latitude, prop.longitude] for prop in all_properties])

        # Use DBSCAN for clustering based on geographic proximity
        # Convert radius from km to approximate degree differences
        # 1 degree is approximately 111 km
        radius_degrees = neighborhood_radius / 111.0

        dbscan = DBSCAN(eps=radius_degrees, min_samples=min_cluster_size)
        cluster_labels = dbscan.fit_predict(coords)

        # Group properties by cluster label
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(all_properties[i])

        # Return only clusters (not the noise points labeled as -1)
        cluster_list = [props for label, props in clusters.items() if label != -1]

        return cluster_list

    def calculate_cluster_concentration_by_coverage_type(
        self,
        all_properties: List[PropertyInfo],
        coverage_type: str,
        climate_correlation: Optional[float] = None,
        hazard_type: str = "flood",
        min_cluster_size: int = 3,
        neighborhood_radius: float = 5.0,
    ) -> List[ConcentrationRiskResult]:
        """
        Calculate concentration risk separately for properties of a specific coverage type

        Args:
            all_properties: List of all properties
            coverage_type: Type of coverage to filter for
            climate_correlation: Climate correlation factor
            hazard_type: Type of hazard for correlation calculation
            min_cluster_size: Minimum cluster size
            neighborhood_radius: Neighborhood radius in km

        Returns:
            List of concentration risk results for each cluster of the specified type
        """
        # Filter properties by coverage type
        filtered_properties = [
            prop
            for prop in all_properties
            if prop.coverage_type.lower() == coverage_type.lower()
        ]

        if not filtered_properties:
            return []

        # Identify clusters
        clusters = self.identify_clusters(
            filtered_properties, min_cluster_size, neighborhood_radius
        )

        # Calculate risk for each cluster
        results = []
        for cluster in clusters:
            result = self.calculate_concentration_risk(
                cluster, climate_correlation, hazard_type
            )
            results.append(result)

        return results

    def calculate_aggregate_concentration_risk(
        self,
        all_properties: List[PropertyInfo],
        climate_correlation: Optional[float] = None,
        hazard_type: str = "flood",
    ) -> Dict[str, Any]:
        """
        Calculate aggregate concentration risk across all properties

        Args:
            all_properties: List of all properties
            climate_correlation: Climate correlation factor
            hazard_type: Type of hazard for correlation calculation

        Returns:
            Dictionary with aggregate concentration risk metrics
        """
        if not all_properties:
            return {
                "aggregate_concentration_risk": 0.0,
                "total_properties": 0,
                "cluster_count": 0,
                "total_exposure": 0.0,
                "max_single_cluster_risk": 0.0,
                "calculation_timestamp": datetime.now().isoformat(),
            }

        # Identify all clusters
        clusters = self.identify_clusters(all_properties)

        # Calculate risk for each cluster
        cluster_results = []
        total_exposure = sum(prop.premium_value for prop in all_properties)

        for cluster in clusters:
            result = self.calculate_concentration_risk(
                cluster, climate_correlation, hazard_type
            )
            cluster_results.append(result)

        # Aggregate metrics
        aggregate_risk = sum(result.concentration_risk for result in cluster_results)
        max_cluster_risk = (
            max([result.concentration_risk for result in cluster_results], default=0.0)
            if cluster_results
            else 0.0
        )

        return {
            "aggregate_concentration_risk": aggregate_risk,
            "total_properties": len(all_properties),
            "cluster_count": len(cluster_results),
            "total_exposure": total_exposure,
            "max_single_cluster_risk": max_cluster_risk,
            "cluster_risks": [result.concentration_risk for result in cluster_results],
            "average_cluster_risk": (
                np.mean([result.concentration_risk for result in cluster_results])
                if cluster_results
                else 0.0
            ),
            "calculation_timestamp": datetime.now().isoformat(),
        }


# Global instance
concentration_risk_service = ConcentrationRiskCalculator()


def calculate_concentration_risk(
    properties: List[PropertyInfo],
    climate_correlation: Optional[float] = None,
    hazard_type: str = "flood",
    neighborhood_def: Optional[NeighborhoodDefinition] = None,
) -> ConcentrationRiskResult:
    """Convenience function to calculate concentration risk"""
    return concentration_risk_service.calculate_concentration_risk(
        properties, climate_correlation, hazard_type, neighborhood_def
    )


def identify_clusters(
    all_properties: List[PropertyInfo],
    min_cluster_size: int = 3,
    neighborhood_radius: float = 5.0,
) -> List[List[PropertyInfo]]:
    """Convenience function to identify clusters"""
    return concentration_risk_service.identify_clusters(
        all_properties, min_cluster_size, neighborhood_radius
    )


def calculate_cluster_concentration_by_coverage_type(
    all_properties: List[PropertyInfo],
    coverage_type: str,
    climate_correlation: Optional[float] = None,
    hazard_type: str = "flood",
    min_cluster_size: int = 3,
    neighborhood_radius: float = 5.0,
) -> List[ConcentrationRiskResult]:
    """Convenience function to calculate concentration risk by coverage type"""
    return concentration_risk_service.calculate_cluster_concentration_by_coverage_type(
        all_properties,
        coverage_type,
        climate_correlation,
        hazard_type,
        min_cluster_size,
        neighborhood_radius,
    )


def calculate_aggregate_concentration_risk(
    all_properties: List[PropertyInfo],
    climate_correlation: Optional[float] = None,
    hazard_type: str = "flood",
) -> Dict[str, Any]:
    """Convenience function to calculate aggregate concentration risk"""
    return concentration_risk_service.calculate_aggregate_concentration_risk(
        all_properties, climate_correlation, hazard_type
    )
