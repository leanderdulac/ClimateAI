"""
Microsegmentation Service for Granular Risk Analysis
Provides detailed risk analysis by dividing regions into micro-segments
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import json

logger = logging.getLogger(__name__)

class MicrosegmentationService:
    """
    Service for microsegmenting regions into smaller areas for granular risk analysis.
    Uses clustering algorithms to identify risk patterns and create micro-segments.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.clustering_model = None
        self.microsegments = {}
        self.risk_profiles = {}

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth

        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers

        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        a = sin(dlat/2) * sin(dlat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2) * sin(dlon/2)
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def create_microsegments(self, region_bounds: Dict[str, Any], n_segments: int = 20) -> Dict[str, Any]:
        """
        Create micro-segments within a geographic region

        Args:
            region_bounds: Dictionary with region boundaries and characteristics
            n_segments: Number of micro-segments to create

        Returns:
            Dictionary containing micro-segment definitions and characteristics
        """
        try:
            # Extract region bounds
            min_lat = region_bounds.get('min_lat', -33)
            max_lat = region_bounds.get('max_lat', 5)
            min_lon = region_bounds.get('min_lon', -73)
            max_lon = region_bounds.get('max_lon', -35)

            # Generate grid of points within the region
            lat_points = np.linspace(min_lat, max_lat, int(np.sqrt(n_segments)))
            lon_points = np.linspace(min_lon, max_lon, int(np.sqrt(n_segments)))

            grid_points = []
            for lat in lat_points:
                for lon in lon_points:
                    grid_points.append([lat, lon])

            grid_points = np.array(grid_points)

            # Generate synthetic risk factors for each point
            risk_factors = self._generate_risk_factors(grid_points, region_bounds)

            # Apply clustering to identify micro-segments
            features_for_clustering = risk_factors[['weather_risk', 'soil_risk', 'economic_risk', 'infrastructure_risk']].values

            # Scale features
            scaled_features = self.scaler.fit_transform(features_for_clustering)

            # Use K-means clustering
            self.clustering_model = KMeans(n_clusters=min(n_segments, len(grid_points)), random_state=42, n_init=10)
            clusters = self.clustering_model.fit_predict(scaled_features)

            # Create micro-segments
            microsegments = []
            for cluster_id in range(self.clustering_model.n_clusters):
                cluster_points = grid_points[clusters == cluster_id]
                cluster_risks = risk_factors.iloc[clusters == cluster_id]

                # Calculate cluster centroid
                centroid_lat = np.mean(cluster_points[:, 0])
                centroid_lon = np.mean(cluster_points[:, 1])

                # Calculate risk profile for the cluster
                risk_profile = {
                    'weather_risk': float(cluster_risks['weather_risk'].mean()),
                    'soil_risk': float(cluster_risks['soil_risk'].mean()),
                    'economic_risk': float(cluster_risks['economic_risk'].mean()),
                    'infrastructure_risk': float(cluster_risks['infrastructure_risk'].mean()),
                    'overall_risk': float(cluster_risks[['weather_risk', 'soil_risk', 'economic_risk', 'infrastructure_risk']].mean().mean())
                }

                # Calculate cluster boundaries
                bounds = {
                    'min_lat': float(cluster_points[:, 0].min()),
                    'max_lat': float(cluster_points[:, 0].max()),
                    'min_lon': float(cluster_points[:, 1].min()),
                    'max_lon': float(cluster_points[:, 1].max())
                }

                microsegment = {
                    'id': f'microsegment_{cluster_id}',
                    'centroid': {'latitude': centroid_lat, 'longitude': centroid_lon},
                    'bounds': bounds,
                    'point_count': len(cluster_points),
                    'risk_profile': risk_profile,
                    'risk_category': self._categorize_risk(risk_profile['overall_risk']),
                    'coordinates': cluster_points.tolist()
                }

                microsegments.append(microsegment)

            # Sort by overall risk (highest risk first)
            microsegments.sort(key=lambda x: x['risk_profile']['overall_risk'], reverse=True)

            result = {
                'region_bounds': region_bounds,
                'total_microsegments': len(microsegments),
                'microsegments': microsegments,
                'clustering_info': {
                    'algorithm': 'K-means',
                    'n_clusters': self.clustering_model.n_clusters,
                    'silhouette_score': float(silhouette_score(scaled_features, clusters)) if len(np.unique(clusters)) > 1 else 0
                },
                'timestamp': datetime.now().isoformat()
            }

            # Store for later use
            self.microsegments[region_bounds.get('region_id', 'default')] = result

            return result

        except Exception as e:
            logger.error(f"Error creating microsegments: {e}")
            return {
                'error': str(e),
                'region_bounds': region_bounds,
                'timestamp': datetime.now().isoformat()
            }

    def _generate_risk_factors(self, grid_points: np.ndarray, region_bounds: Dict[str, Any]) -> pd.DataFrame:
        """
        Generate synthetic risk factors for each point in the grid

        Args:
            grid_points: Array of [lat, lon] coordinates
            region_bounds: Region characteristics

        Returns:
            DataFrame with risk factors for each point
        """
        risk_data = []

        # Base risk patterns for Brazil
        for point in grid_points:
            lat, lon = point

            # Weather risk (higher in tropical areas and during rainy seasons)
            weather_risk = 0.3 + 0.4 * abs(lat) / 30  # Higher risk in extreme latitudes
            weather_risk += 0.2 * np.sin(np.radians(lat * 10))  # Seasonal variation

            # Soil risk (higher in certain soil types and topography)
            soil_risk = 0.2 + 0.3 * np.random.random()  # Random soil variation
            soil_risk += 0.1 if lat < -10 else 0  # Higher risk in northern Brazil

            # Economic risk (higher in less developed areas)
            economic_risk = 0.25 + 0.3 * abs(lat) / 30  # Economic development gradient
            economic_risk += 0.15 * np.random.random()

            # Infrastructure risk (higher in remote areas)
            infrastructure_risk = 0.2 + 0.4 * (abs(lat) / 30 + abs(lon + 50) / 40)
            infrastructure_risk += 0.1 * np.random.random()

            # Add some spatial correlation
            distance_from_center = self.haversine_distance(lat, lon, -15, -47)  # Distance from Brasília
            spatial_factor = min(distance_from_center / 2000, 1)  # Normalize to 0-1
            infrastructure_risk += 0.2 * spatial_factor

            risk_data.append({
                'latitude': lat,
                'longitude': lon,
                'weather_risk': min(weather_risk, 1.0),
                'soil_risk': min(soil_risk, 1.0),
                'economic_risk': min(economic_risk, 1.0),
                'infrastructure_risk': min(infrastructure_risk, 1.0)
            })

        return pd.DataFrame(risk_data)

    def _categorize_risk(self, risk_score: float) -> str:
        """
        Categorize risk score into qualitative levels

        Args:
            risk_score: Numerical risk score (0-1)

        Returns:
            Risk category string
        """
        if risk_score >= 0.8:
            return 'Muito Alto'
        elif risk_score >= 0.6:
            return 'Alto'
        elif risk_score >= 0.4:
            return 'Médio'
        elif risk_score >= 0.2:
            return 'Baixo'
        else:
            return 'Muito Baixo'

    def analyze_location_risk(self, latitude: float, longitude: float, region_id: str = 'default') -> Dict[str, Any]:
        """
        Analyze risk for a specific location using microsegmentation

        Args:
            latitude, longitude: Location coordinates
            region_id: Region identifier

        Returns:
            Risk analysis for the location
        """
        try:
            if region_id not in self.microsegments:
                logger.warning(f"Microsegments not found for region {region_id}")
                return {
                    'error': f'Microsegments not available for region {region_id}',
                    'latitude': latitude,
                    'longitude': longitude
                }

            microsegments_data = self.microsegments[region_id]
            microsegments = microsegments_data['microsegments']

            # Find the closest microsegment to the location
            min_distance = float('inf')
            closest_segment = None

            for segment in microsegments:
                centroid = segment['centroid']
                distance = self.haversine_distance(
                    latitude, longitude,
                    centroid['latitude'], centroid['longitude']
                )

                if distance < min_distance:
                    min_distance = distance
                    closest_segment = segment

            if not closest_segment:
                return {
                    'error': 'No microsegment found',
                    'latitude': latitude,
                    'longitude': longitude
                }

            # Check if location is within segment bounds
            bounds = closest_segment['bounds']
            is_within_bounds = (
                bounds['min_lat'] <= latitude <= bounds['max_lat'] and
                bounds['min_lon'] <= longitude <= bounds['max_lon']
            )

            return {
                'location': {'latitude': latitude, 'longitude': longitude},
                'microsegment': closest_segment,
                'distance_to_centroid': min_distance,
                'is_within_bounds': is_within_bounds,
                'risk_analysis': {
                    'overall_risk': closest_segment['risk_profile']['overall_risk'],
                    'risk_category': closest_segment['risk_category'],
                    'risk_factors': closest_segment['risk_profile'],
                    'recommendations': self._generate_risk_recommendations(closest_segment['risk_profile'])
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing location risk: {e}")
            return {
                'error': str(e),
                'latitude': latitude,
                'longitude': longitude
            }

    def _generate_risk_recommendations(self, risk_profile: Dict[str, float]) -> List[str]:
        """
        Generate risk mitigation recommendations based on risk profile

        Args:
            risk_profile: Dictionary with risk factors

        Returns:
            List of recommendations
        """
        recommendations = []

        if risk_profile['weather_risk'] > 0.6:
            recommendations.append("Implementar sistemas de irrigação e drenagem para mitigar riscos climáticos")
            recommendations.append("Considerar seguros contra eventos climáticos extremos")

        if risk_profile['soil_risk'] > 0.6:
            recommendations.append("Realizar análise de solo detalhada e implementar práticas de conservação")
            recommendations.append("Diversificar culturas para reduzir dependência de solos específicos")

        if risk_profile['economic_risk'] > 0.6:
            recommendations.append("Desenvolver parcerias com cooperativas locais para estabilidade econômica")
            recommendations.append("Implementar contratos de preço futuro para proteger contra volatilidade")

        if risk_profile['infrastructure_risk'] > 0.6:
            recommendations.append("Investir em infraestrutura de transporte e armazenamento")
            recommendations.append("Desenvolver redes de distribuição alternativas")

        if not recommendations:
            recommendations.append("Manter monitoramento regular dos fatores de risco")
            recommendations.append("Continuar com práticas de gestão de risco atuais")

        return recommendations

    def get_microsegmentation_summary(self, region_id: str = 'default') -> Dict[str, Any]:
        """
        Get summary statistics for microsegmentation analysis

        Args:
            region_id: Region identifier

        Returns:
            Summary statistics
        """
        try:
            if region_id not in self.microsegments:
                return {'error': f'Microsegments not found for region {region_id}'}

            data = self.microsegments[region_id]
            microsegments = data['microsegments']

            risk_scores = [seg['risk_profile']['overall_risk'] for seg in microsegments]
            risk_categories = [seg['risk_category'] for seg in microsegments]

            # Count categories
            category_counts = {}
            for category in ['Muito Alto', 'Alto', 'Médio', 'Baixo', 'Muito Baixo']:
                category_counts[category] = risk_categories.count(category)

            return {
                'region_id': region_id,
                'total_microsegments': len(microsegments),
                'risk_statistics': {
                    'mean_risk': float(np.mean(risk_scores)),
                    'std_risk': float(np.std(risk_scores)),
                    'min_risk': float(np.min(risk_scores)),
                    'max_risk': float(np.max(risk_scores)),
                    'risk_categories': category_counts
                },
                'clustering_info': data.get('clustering_info', {}),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting microsegmentation summary: {e}")
            return {'error': str(e)}

# Global instance
microsegmentation_service = MicrosegmentationService()

# Convenience functions
def create_microsegments(region_bounds: Dict[str, Any], n_segments: int = 20) -> Dict[str, Any]:
    """Create micro-segments for a region"""
    return microsegmentation_service.create_microsegments(region_bounds, n_segments)

def analyze_location_risk(latitude: float, longitude: float, region_id: str = 'default') -> Dict[str, Any]:
    """Analyze risk for a specific location"""
    return microsegmentation_service.analyze_location_risk(latitude, longitude, region_id)

def get_microsegmentation_summary(region_id: str = 'default') -> Dict[str, Any]:
    """Get summary of microsegmentation analysis"""
    return microsegmentation_service.get_microsegmentation_summary(region_id)