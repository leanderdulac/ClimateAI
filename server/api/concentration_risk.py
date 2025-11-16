"""
API Router for Concentration Risk Calculation Service
Implements: R_concentração = √[Σ_i (x_i - x̄)² / n] · ρ_climático
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from services.concentration_risk_service import (
    ConcentrationRiskCalculator,
    PropertyInfo,
    ConcentrationRiskResult,
    NeighborhoodDefinition,
    calculate_concentration_risk,
    identify_clusters,
    calculate_cluster_concentration_by_coverage_type,
    calculate_aggregate_concentration_risk
)

router = APIRouter()

@router.post("/concentration-risk/calculate")
async def calculate_concentration_risk_endpoint(
    property_ids: List[str] = Query(..., description="List of property IDs in the cluster"),
    premium_values: List[float] = Query(..., description="List of premium values for each property"),
    latitudes: List[float] = Query(..., description="List of latitude values for each property"),
    longitudes: List[float] = Query(..., description="List of longitude values for each property"),
    coverage_types: List[str] = Query(..., description="List of coverage types for each property"),
    asset_values: List[float] = Query(..., description="List of asset values for each property"),
    construction_types: List[str] = Query(..., description="List of construction types for each property"),
    elevations: List[float] = Query(..., description="List of elevation values (meters) for each property"),
    climate_zones: List[str] = Query(..., description="List of climate zones for each property"),
    climate_correlation: float = Query(None, ge=0, le=1, description="Climate correlation factor (ρ_climático)"),
    hazard_type: str = Query("flood", description="Type of hazard: flood, wind, fire, hail, drought"),
    neighborhood_radius: float = Query(5.0, gt=0, description="Neighborhood radius in km for correlation calculation")
):
    """
    Calculate concentration risk using the specified formula:
    R_concentração = √[Σ_i (x_i - x̄)² / n] · ρ_climático
    """
    try:
        # Validate input lengths match
        if not (len(property_ids) == len(premium_values) == len(latitudes) == 
                len(longitudes) == len(coverage_types) == len(asset_values) == 
                len(construction_types) == len(elevations) == len(climate_zones)):
            raise HTTPException(
                status_code=400, 
                detail="All input lists must have the same length"
            )
        
        if len(property_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one property is required")
        
        # Create property info objects
        properties = []
        for i in range(len(property_ids)):
            property_info = PropertyInfo(
                property_id=property_ids[i],
                premium_value=premium_values[i],
                latitude=latitudes[i],
                longitude=longitudes[i],
                coverage_type=coverage_types[i],
                asset_value=asset_values[i],
                construction_type=construction_types[i],
                elevation=elevations[i],
                climate_zone=climate_zones[i]
            )
            properties.append(property_info)
        
        # Create neighborhood definition
        neighborhood_def = NeighborhoodDefinition(radius_km=neighborhood_radius)
        
        # Calculate concentration risk
        result = calculate_concentration_risk(
            properties,
            climate_correlation=climate_correlation,
            hazard_type=hazard_type,
            neighborhood_def=neighborhood_def
        )
        
        # Format response
        return {
            "concentration_risk": result.concentration_risk,
            "cluster_size": result.cluster_size,
            "average_premium": result.average_premium,
            "cluster_standard_deviation": result.cluster_std_dev,
            "climate_correlation": result.climate_correlation,
            "spatial_distribution": result.spatial_distribution,
            "risk_metrics": result.risk_metrics,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "properties_in_cluster": [
                {
                    "property_id": prop.property_id,
                    "premium_value": prop.premium_value,
                    "latitude": prop.latitude,
                    "longitude": prop.longitude,
                    "coverage_type": prop.coverage_type,
                    "asset_value": prop.asset_value
                } for prop in result.cluster_properties
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concentration risk calculation failed: {str(e)}")

@router.post("/concentration-risk/identify-clusters")
async def identify_clusters_endpoint(
    property_ids: List[str] = Query(..., description="List of property IDs"),
    latitudes: List[float] = Query(..., description="List of latitude values"),
    longitudes: List[float] = Query(..., description="List of longitude values"),
    coverage_types: List[str] = Query(..., description="List of coverage types"),
    premium_values: List[float] = Query(..., description="List of premium values"),
    asset_values: List[float] = Query(..., description="List of asset values"),
    construction_types: List[str] = Query(..., description="List of construction types"),
    elevations: List[float] = Query(..., description="List of elevation values (meters)"),
    climate_zones: List[str] = Query(..., description="List of climate zones"),
    min_cluster_size: int = Query(3, ge=1, description="Minimum number of properties to form a cluster"),
    neighborhood_radius: float = Query(5.0, gt=0, description="Neighborhood radius in km for clustering")
):
    """
    Identify clusters of properties based on geographic proximity
    """
    try:
        # Validate input lengths match
        if not (len(property_ids) == len(latitudes) == len(longitudes) == 
                len(coverage_types) == len(premium_values) == len(asset_values) == 
                len(construction_types) == len(elevations) == len(climate_zones)):
            raise HTTPException(
                status_code=400, 
                detail="All input lists must have the same length"
            )
        
        if len(property_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one property is required")
        
        # Create property info objects
        all_properties = []
        for i in range(len(property_ids)):
            property_info = PropertyInfo(
                property_id=property_ids[i],
                premium_value=premium_values[i],
                latitude=latitudes[i],
                longitude=longitudes[i],
                coverage_type=coverage_types[i],
                asset_value=asset_values[i],
                construction_type=construction_types[i],
                elevation=elevations[i],
                climate_zone=climate_zones[i]
            )
            all_properties.append(property_info)
        
        # Identify clusters
        clusters = identify_clusters(
            all_properties,
            min_cluster_size=min_cluster_size,
            neighborhood_radius=neighborhood_radius
        )
        
        # Format response
        formatted_clusters = []
        for i, cluster in enumerate(clusters):
            formatted_cluster = {
                "cluster_id": i,
                "properties": [
                    {
                        "property_id": prop.property_id,
                        "premium_value": prop.premium_value,
                        "latitude": prop.latitude,
                        "longitude": prop.longitude,
                        "coverage_type": prop.coverage_type,
                        "asset_value": prop.asset_value
                    } for prop in cluster
                ],
                "cluster_size": len(cluster),
                "centroid": {
                    "latitude": sum(p.latitude for p in cluster) / len(cluster),
                    "longitude": sum(p.longitude for p in cluster) / len(cluster)
                }
            }
            formatted_clusters.append(formatted_cluster)
        
        return {
            "total_clusters_identified": len(formatted_clusters),
            "clusters": formatted_clusters,
            "total_properties": len(all_properties),
            "identification_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cluster identification failed: {str(e)}")

@router.post("/concentration-risk/by-coverage-type")
async def calculate_concentration_by_coverage_type_endpoint(
    property_ids: List[str] = Query(..., description="List of property IDs"),
    premium_values: List[float] = Query(..., description="List of premium values"),
    latitudes: List[float] = Query(..., description="List of latitude values"),
    longitudes: List[float] = Query(..., description="List of longitude values"),
    coverage_types: List[str] = Query(..., description="List of coverage types"),
    asset_values: List[float] = Query(..., description="List of asset values"),
    construction_types: List[str] = Query(..., description="List of construction types"),
    elevations: List[float] = Query(..., description="List of elevation values (meters)"),
    climate_zones: List[str] = Query(..., description="List of climate zones"),
    coverage_type_filter: str = Query(..., description="Coverage type to calculate concentration risk for"),
    climate_correlation: float = Query(None, ge=0, le=1, description="Climate correlation factor"),
    hazard_type: str = Query("flood", description="Type of hazard for correlation calculation"),
    min_cluster_size: int = Query(3, ge=1, description="Minimum number of properties to form a cluster"),
    neighborhood_radius: float = Query(5.0, gt=0, description="Neighborhood radius in km")
):
    """
    Calculate concentration risk for clusters of a specific coverage type
    """
    try:
        # Validate input lengths match
        if not (len(property_ids) == len(premium_values) == len(latitudes) == 
                len(longitudes) == len(coverage_types) == len(asset_values) == 
                len(construction_types) == len(elevations) == len(climate_zones)):
            raise HTTPException(
                status_code=400, 
                detail="All input lists must have the same length"
            )
        
        if len(property_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one property is required")
        
        # Create property info objects
        all_properties = []
        for i in range(len(property_ids)):
            property_info = PropertyInfo(
                property_id=property_ids[i],
                premium_value=premium_values[i],
                latitude=latitudes[i],
                longitude=longitudes[i],
                coverage_type=coverage_types[i],
                asset_value=asset_values[i],
                construction_type=construction_types[i],
                elevation=elevations[i],
                climate_zone=climate_zones[i]
            )
            all_properties.append(property_info)
        
        # Calculate concentration risk for specific coverage type
        results = calculate_cluster_concentration_by_coverage_type(
            all_properties=all_properties,
            coverage_type=coverage_type_filter,
            climate_correlation=climate_correlation,
            hazard_type=hazard_type,
            min_cluster_size=min_cluster_size,
            neighborhood_radius=neighborhood_radius
        )
        
        # Format response
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                "cluster_id": i,
                "concentration_risk": result.concentration_risk,
                "cluster_size": result.cluster_size,
                "average_premium": result.average_premium,
                "cluster_standard_deviation": result.cluster_std_dev,
                "climate_correlation": result.climate_correlation,
                "spatial_metrics": result.spatial_distribution,
                "risk_metrics": result.risk_metrics,
                "properties": [
                    {
                        "property_id": prop.property_id,
                        "premium_value": prop.premium_value,
                        "latitude": prop.latitude,
                        "longitude": prop.longitude,
                        "coverage_type": prop.coverage_type,
                        "asset_value": prop.asset_value
                    } for prop in result.cluster_properties
                ]
            })
        
        return {
            "coverage_type": coverage_type_filter,
            "total_clusters_found": len(formatted_results),
            "results": formatted_results,
            "calculation_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coverage type concentration calculation failed: {str(e)}")

@router.post("/concentration-risk/aggregate-risk")
async def calculate_aggregate_concentration_risk_endpoint(
    property_ids: List[str] = Query(..., description="List of property IDs"),
    premium_values: List[float] = Query(..., description="List of premium values"),
    latitudes: List[float] = Query(..., description="List of latitude values"),
    longitudes: List[float] = Query(..., description="List of longitude values"),
    coverage_types: List[str] = Query(..., description="List of coverage types"),
    asset_values: List[float] = Query(..., description="List of asset values"),
    construction_types: List[str] = Query(..., description="List of construction types"),
    elevations: List[float] = Query(..., description="List of elevation values (meters)"),
    climate_zones: List[str] = Query(..., description="List of climate zones"),
    climate_correlation: float = Query(None, ge=0, le=1, description="Climate correlation factor"),
    hazard_type: str = Query("flood", description="Type of hazard for correlation calculation")
):
    """
    Calculate aggregate concentration risk across all properties
    """
    try:
        # Validate input lengths match
        if not (len(property_ids) == len(premium_values) == len(latitudes) == 
                len(longitudes) == len(coverage_types) == len(asset_values) == 
                len(construction_types) == len(elevations) == len(climate_zones)):
            raise HTTPException(
                status_code=400, 
                detail="All input lists must have the same length"
            )
        
        if len(property_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one property is required")
        
        # Create property info objects
        all_properties = []
        for i in range(len(property_ids)):
            property_info = PropertyInfo(
                property_id=property_ids[i],
                premium_value=premium_values[i],
                latitude=latitudes[i],
                longitude=longitudes[i],
                coverage_type=coverage_types[i],
                asset_value=asset_values[i],
                construction_type=construction_types[i],
                elevation=elevations[i],
                climate_zone=climate_zones[i]
            )
            all_properties.append(property_info)
        
        # Calculate aggregate concentration risk
        result = calculate_aggregate_concentration_risk(
            all_properties=all_properties,
            climate_correlation=climate_correlation,
            hazard_type=hazard_type
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregate concentration risk calculation failed: {str(e)}")

@router.get("/concentration-risk/info")
async def concentration_risk_info():
    """
    Get information about the concentration risk calculation service
    """
    return {
        "description": "Concentration Risk Calculation Service",
        "formula": "R_concentração = √[Σ_i (x_i - x̄)² / n] · ρ_climático",
        "variables": {
            "x_i": "value of the premium of property i in the cluster",
            "x̄": "average premium of all properties in the cluster",
            "n": "number of properties in the cluster",
            "ρ_climático": "spatial correlation of extreme events in the neighborhood (5km)"
        },
        "methodology": "Spatial Concentration Risk Assessment Methodology",
        "features": [
            "Spatial clustering of properties based on geographic proximity",
            "Premium volatility calculation within clusters",
            "Climate correlation modeling based on distance",
            "Coverage type-specific concentration analysis",
            "Aggregate risk assessment across all properties",
            "Hazard-specific correlation factors"
        ],
        "hazard_correlations": {
            "flood": 0.8,
            "wind": 0.4,
            "fire": 0.3,
            "hail": 0.2,
            "drought": 0.9
        },
        "spatial_metrics": [
            "Centroid location",
            "Area approximation",
            "Compactness",
            "Maximum distance",
            "Average distance from centroid",
            "Cluster density"
        ]
    }