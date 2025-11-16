"""
API Router for SIPS-Climate Performance Analytics Service
Implements performance metrics tracking based on:
- Taxa de sinistralidade: 65% → 58% (-7pp) 
- Sinistralidade climática: 42% → 31% (-11pp)
- Margem líquida: 8% → 14% (+6pp)
- Rejeições: 5% → 12% (+7pp)
- Prêmio médio: R$1.200 → R$1.650 (+38%)
- Retenção clientes: 78% → 85% (+7pp)
- Capital econômico: R$45M → R$52M (+15%)
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from services.sips_performance_analytics_service import (
    sips_analytics_service,
    create_performance_snapshot,
    calculate_performance_deltas,
    generate_performance_report,
    calculate_sips_impact_score,
    get_performance_trend,
    PerformanceMetric,
    PerformanceSnapshot,
    PerformanceDelta,
    PerformanceReport
)

router = APIRouter()

@router.post("/sips-analytics/create-snapshot")
async def create_performance_snapshot_endpoint(
    snapshot_id: str = Query(..., description="Unique identifier for the snapshot"),
    date: str = Query(datetime.now().isoformat(), description="Date of the snapshot (ISO format)"),
    claim_rate: float = Query(..., ge=0, le=1, description="Taxa de sinistralidade (0.0 to 1.0)"),
    climate_loss_rate: float = Query(..., ge=0, le=1, description="Sinistralidade climática (0.0 to 1.0)"),
    net_margin: float = Query(..., ge=0, le=1, description="Margem líquida (0.0 to 1.0)"),
    rejection_rate: float = Query(..., ge=0, le=1, description="Rejeições (0.0 to 1.0)"),
    average_premium: float = Query(..., gt=0, description="Prêmio médio in currency"),
    client_retention: float = Query(..., ge=0, le=1, description="Retenção clientes (0.0 to 1.0)"),
    economic_capital: float = Query(..., ge=0, description="Capital econômico in currency"),
    baseline_period: str = Query("custom", description="Period classification: before_sips, after_sips, monthly, quarterly")
):
    """
    Create a performance snapshot with current metrics
    """
    try:
        # Parse date
        try:
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00')) if 'T' in date else datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (e.g., 2023-01-01T00:00:00)")

        # Create performance snapshot
        snapshot = create_performance_snapshot(
            snapshot_id=snapshot_id,
            date=date_obj,
            claim_rate=claim_rate,
            climate_loss_rate=climate_loss_rate,
            net_margin=net_margin,
            rejection_rate=rejection_rate,
            average_premium=average_premium,
            client_retention=client_retention,
            economic_capital=economic_capital,
            baseline_period=baseline_period
        )

        return {
            "snapshot_id": snapshot.snapshot_id,
            "date": snapshot.date.isoformat(),
            "metrics": {
                "taxa_sinistralidade": snapshot.claim_rate,
                "sinistralidade_climatica": snapshot.climate_loss_rate,
                "margem_liquida": snapshot.net_margin,
                "rejeicoes": snapshot.rejection_rate,
                "premio_medio": snapshot.average_premium,
                "retencao_clientes": snapshot.client_retention,
                "capital_economico": snapshot.economic_capital
            },
            "baseline_period": snapshot.baseline_period,
            "calculation_method": snapshot.calculation_method,
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance snapshot creation failed: {str(e)}")

@router.post("/sips-analytics/calculate-deltas")
async def calculate_performance_deltas_endpoint(
    before_snapshot_id: str = Query(..., description="Baseline snapshot ID"),
    after_snapshot_id: str = Query(..., description="Compare to snapshot ID")
):
    """
    Calculate performance deltas between two snapshots
    """
    try:
        # Get snapshots
        before_snapshot = sips_analytics_service.performance_snapshots.get(before_snapshot_id)
        after_snapshot = sips_analytics_service.performance_snapshots.get(after_snapshot_id)
        
        if not before_snapshot:
            raise HTTPException(status_code=404, detail=f"Before snapshot not found: {before_snapshot_id}")
        if not after_snapshot:
            raise HTTPException(status_code=404, detail=f"After snapshot not found: {after_snapshot_id}")
        
        # Calculate deltas
        deltas = calculate_performance_deltas(before_snapshot, after_snapshot)
        
        # Format deltas
        formatted_deltas = []
        total_absolute_change = 0.0
        beneficial_changes = 0
        harmful_changes = 0
        
        for delta in deltas:
            formatted_deltas.append({
                "metric_name": delta.metric_name,
                "before_value": delta.before_value,
                "after_value": delta.after_value,
                "absolute_change": delta.absolute_change,
                "percentage_change": delta.percentage_change,
                "improvement": delta.improvement,
                "impact_category": delta.impact_category
            })
            
            total_absolute_change += abs(delta.absolute_change)
            if delta.improvement:
                beneficial_changes += 1
            else:
                harmful_changes += 1
        
        return {
            "before_snapshot_id": before_snapshot.snapshot_id,
            "after_snapshot_id": after_snapshot.snapshot_id,
            "before_date": before_snapshot.date.isoformat(),
            "after_date": after_snapshot.date.isoformat(),
            "deltas": formatted_deltas,
            "summary": {
                "total_metrics_analyzed": len(deltas),
                "beneficial_changes": beneficial_changes,
                "harmful_changes": harmful_changes,
                "total_absolute_change": total_absolute_change,
                "improvement_percentage": (beneficial_changes / len(deltas) * 100) if deltas else 0
            },
            "analysis": {
                "positive_impacts": [d["metric_name"] for d in formatted_deltas if d["improvement"]],
                "negative_impacts": [d["metric_name"] for d in formatted_deltas if not d["improvement"]],
                "highest_improvement": max(formatted_deltas, key=lambda x: abs(x["percentage_change"]), default=None)
            },
            "status": "calculated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance deltas calculation failed: {str(e)}")

@router.post("/sips-analytics/generate-report")
async def generate_performance_report_endpoint(
    report_id: str = Query(..., description="Unique identifier for the report"),
    baseline_snapshot_id: str = Query(..., description="Baseline snapshot ID"),
    current_snapshot_id: str = Query(..., description="Current snapshot ID")
):
    """
    Generate a comprehensive performance report
    """
    try:
        # Get snapshots
        baseline_snapshot = sips_analytics_service.performance_snapshots.get(baseline_snapshot_id)
        current_snapshot = sips_analytics_service.performance_snapshots.get(current_snapshot_id)
        
        if not baseline_snapshot:
            raise HTTPException(status_code=404, detail=f"Baseline snapshot not found: {baseline_snapshot_id}")
        if not current_snapshot:
            raise HTTPException(status_code=404, detail=f"Current snapshot not found: {current_snapshot_id}")
        
        # Generate performance report
        report = generate_performance_report(report_id, baseline_snapshot, current_snapshot)
        
        # Format deltas
        formatted_deltas = []
        for delta in report.deltas:
            formatted_deltas.append({
                "metric_name": delta.metric_name,
                "before_value": delta.before_value,
                "after_value": delta.after_value,
                "absolute_change": delta.absolute_change,
                "percentage_change": delta.percentage_change,
                "improvement": delta.improvement,
                "impact_category": delta.impact_category
            })
        
        return {
            "report_id": report.report_id,
            "generation_date": report.generation_date.isoformat(),
            "baseline_snapshot": {
                "snapshot_id": report.baseline_snapshot.snapshot_id,
                "date": report.baseline_snapshot.date.isoformat(),
                "metrics": {
                    "taxa_sinistralidade": report.baseline_snapshot.claim_rate,
                    "sinistralidade_climatica": report.baseline_snapshot.climate_loss_rate,
                    "margem_liquida": report.baseline_snapshot.net_margin,
                    "rejeicoes": report.baseline_snapshot.rejection_rate,
                    "premio_medio": report.baseline_snapshot.average_premium,
                    "retencao_clientes": report.baseline_snapshot.client_retention,
                    "capital_economico": report.baseline_snapshot.economic_capital
                }
            },
            "current_snapshot": {
                "snapshot_id": report.current_snapshot.snapshot_id,
                "date": report.current_snapshot.date.isoformat(),
                "metrics": {
                    "taxa_sinistralidade": report.current_snapshot.claim_rate,
                    "sinistralidade_climatica": report.current_snapshot.climate_loss_rate,
                    "margem_liquida": report.current_snapshot.net_margin,
                    "rejeicoes": report.current_snapshot.rejection_rate,
                    "premio_medio": report.current_snapshot.average_premium,
                    "retencao_clientes": report.current_snapshot.client_retention,
                    "capital_economico": report.current_snapshot.economic_capital
                }
            },
            "deltas": formatted_deltas,
            "overall_impact_score": report.overall_impact_score,
            "confidence_level": report.confidence_level,
            "recommendations": report.recommendations,
            "key_insights": report.key_insights,
            "report_summary": {
                "total_improvements": sum(1 for d in report.deltas if d.improvement),
                "total_metrics": len(report.deltas),
                "improvement_rate": sum(1 for d in report.deltas if d.improvement) / len(report.deltas) if report.deltas else 0
            },
            "status": "generated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance report generation failed: {str(e)}")

@router.get("/sips-analytics/calculate-sips-impact/{snapshot_id}")
async def calculate_sips_impact_score_endpoint(snapshot_id: str):
    """
    Calculate SIPS-Climate impact score for a specific snapshot
    """
    try:
        # Get snapshot
        snapshot = sips_analytics_service.performance_snapshots.get(snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")
        
        # Calculate SIPS impact score
        impact_score = calculate_sips_impact_score(snapshot)
        
        # Prepare detailed breakdown
        baseline_metrics = sips_analytics_service.baseline_metrics
        target_metrics = sips_analytics_service.target_metrics
        
        metric_analysis = {
            "taxa_sinistralidade": {
                "baseline": baseline_metrics[PerformanceMetric.CLAIM_RATE],
                "current": snapshot.claim_rate,
                "target": target_metrics[PerformanceMetric.CLAIM_RATE],
                "improvement_from_baseline": baseline_metrics[PerformanceMetric.CLAIM_RATE] - snapshot.claim_rate,
                "progress_to_target": (baseline_metrics[PerformanceMetric.CLAIM_RATE] - snapshot.claim_rate) / 
                                     (baseline_metrics[PerformanceMetric.CLAIM_RATE] - target_metrics[PerformanceMetric.CLAIM_RATE]) if (baseline_metrics[PerformanceMetric.CLAIM_RATE] - target_metrics[PerformanceMetric.CLAIM_RATE]) != 0 else 0
            },
            "sinistralidade_climatica": {
                "baseline": baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE],
                "current": snapshot.climate_loss_rate,
                "target": target_metrics[PerformanceMetric.CLIMATE_LOSS_RATE],
                "improvement_from_baseline": baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] - snapshot.climate_loss_rate,
                "progress_to_target": (baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] - snapshot.climate_loss_rate) / 
                                     (baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] - target_metrics[PerformanceMetric.CLIMATE_LOSS_RATE]) if (baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] - target_metrics[PerformanceMetric.CLIMATE_LOSS_RATE]) != 0 else 0
            },
            "margem_liquida": {
                "baseline": baseline_metrics[PerformanceMetric.NET_MARGIN],
                "current": snapshot.net_margin,
                "target": target_metrics[PerformanceMetric.NET_MARGIN],
                "improvement_from_baseline": snapshot.net_margin - baseline_metrics[PerformanceMetric.NET_MARGIN],
                "progress_to_target": (snapshot.net_margin - baseline_metrics[PerformanceMetric.NET_MARGIN]) / 
                                     (target_metrics[PerformanceMetric.NET_MARGIN] - baseline_metrics[PerformanceMetric.NET_MARGIN]) if (target_metrics[PerformanceMetric.NET_MARGIN] - baseline_metrics[PerformanceMetric.NET_MARGIN]) != 0 else 0
            }
        }
        
        # Calculate percentage improvements for display
        percentage_changes = {
            "claim_rate_improvement": ((baseline_metrics[PerformanceMetric.CLAIM_RATE] - snapshot.claim_rate) / baseline_metrics[PerformanceMetric.CLAIM_RATE] * 100) if baseline_metrics[PerformanceMetric.CLAIM_RATE] != 0 else 0,
            "climate_loss_improvement": ((baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] - snapshot.climate_loss_rate) / baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] * 100) if baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE] != 0 else 0,
            "margin_improvement": ((snapshot.net_margin - baseline_metrics[PerformanceMetric.NET_MARGIN]) / baseline_metrics[PerformanceMetric.NET_MARGIN] * 100) if baseline_metrics[PerformanceMetric.NET_MARGIN] != 0 else 0
        }
        
        return {
            "snapshot_id": snapshot_id,
            "sips_impact_score": impact_score,
            "date": snapshot.date.isoformat(),
            "comparative_analysis": {
                "baseline_metrics": {
                    "taxa_sinistralidade": baseline_metrics[PerformanceMetric.CLAIM_RATE],
                    "sinistralidade_climatica": baseline_metrics[PerformanceMetric.CLIMATE_LOSS_RATE],
                    "margem_liquida": baseline_metrics[PerformanceMetric.NET_MARGIN]
                },
                "target_metrics": {
                    "taxa_sinistralidade": target_metrics[PerformanceMetric.CLAIM_RATE],
                    "sinistralidade_climatica": target_metrics[PerformanceMetric.CLIMATE_LOSS_RATE],
                    "margem_liquida": target_metrics[PerformanceMetric.NET_MARGIN]
                },
                "current_metrics": {
                    "taxa_sinistralidade": snapshot.claim_rate,
                    "sinistralidade_climatica": snapshot.climate_loss_rate,
                    "margem_liquida": snapshot.net_margin
                },
                "percentage_improvements": percentage_changes,
                "metric_analysis": metric_analysis
            },
            "interpretation": {
                "score_rating": "excellent" if impact_score >= 80 else "good" if impact_score >= 60 else "fair" if impact_score >= 40 else "needs_improvement",
                "impact_level": "high_positive" if impact_score >= 85 else "positive" if impact_score >= 70 else "neutral" if impact_score >= 50 else "negative"
            },
            "status": "calculated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SIPS impact score calculation failed: {str(e)}")

@router.get("/sips-analytics/performance-trend/{metric_type}")
async def get_performance_trend_endpoint(
    metric_type: str,
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze (7-365)")
):
    """
    Get performance trend for a specific metric over time
    """
    try:
        # Map string to PerformanceMetric enum
        metric_mapping = {
            "claim_rate": PerformanceMetric.CLAIM_RATE,
            "climate_loss_rate": PerformanceMetric.CLIMATE_LOSS_RATE,
            "net_margin": PerformanceMetric.NET_MARGIN,
            "rejection_rate": PerformanceMetric.REJECTION_RATE,
            "average_premium": PerformanceMetric.AVERAGE_PREMIUM,
            "client_retention": PerformanceMetric.CLIENT_RETENTION,
            "economic_capital": PerformanceMetric.ECONOMIC_CAPITAL
        }
        
        if metric_type not in metric_mapping:
            raise HTTPException(status_code=400, detail=f"Invalid metric type. Valid types: {list(metric_mapping.keys())}")
        
        metric = metric_mapping[metric_type]
        
        # Get performance trend
        trend = get_performance_trend(metric, days)
        
        return {
            "metric_type": metric_type,
            "days_analyzed": days,
            "trend_analysis": trend,
            "interpretation": {
                "trend_description": f"The {metric_type} metric is {trend.get('trend', 'showing') if trend.get('trend') != 'insufficient_data' else 'insufficient data for'} trend",
                "data_quality": "sufficient" if trend.get("data_points", 0) >= 3 else "limited",
                "statistical_reliability": "high" if trend.get("data_points", 0) >= 10 else "moderate" if trend.get("data_points", 0) >= 5 else "low"
            },
            "status": "analyzed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance trend analysis failed: {str(e)}")

@router.get("/sips-analytics/dashboard-summary")
async def get_dashboard_summary():
    """
    Get a comprehensive dashboard summary of SIPS-Climate performance
    """
    try:
        # Get all snapshots to analyze trends
        snapshots = list(sips_analytics_service.performance_snapshots.values())
        
        if not snapshots:
            return {
                "dashboard_summary": "No performance data available",
                "snapshots_count": 0,
                "last_update": datetime.now().isoformat(),
                "status": "no_data"
            }
        
        # Sort snapshots by date
        sorted_snapshots = sorted(snapshots, key=lambda x: x.date)
        latest_snapshot = sorted_snapshots[-1]
        earliest_snapshot = sorted_snapshots[0]
        
        # Calculate overall improvements
        claim_improvement = ((earliest_snapshot.claim_rate - latest_snapshot.claim_rate) / earliest_snapshot.claim_rate * 100) if earliest_snapshot.claim_rate != 0 else 0
        climate_loss_improvement = ((earliest_snapshot.climate_loss_rate - latest_snapshot.climate_loss_rate) / earliest_snapshot.climate_loss_rate * 100) if earliest_snapshot.climate_loss_rate != 0 else 0
        margin_improvement = ((latest_snapshot.net_margin - earliest_snapshot.net_margin) / earliest_snapshot.net_margin * 100) if earliest_snapshot.net_margin != 0 else 0
        retention_improvement = ((latest_snapshot.client_retention - earliest_snapshot.client_retention) / earliest_snapshot.client_retention * 100) if earliest_snapshot.client_retention != 0 else 0
        premium_growth = ((latest_snapshot.average_premium - earliest_snapshot.average_premium) / earliest_snapshot.average_premium * 100) if earliest_snapshot.average_premium != 0 else 0
        
        # Calculate SIPS impact score for latest snapshot
        sips_score = calculate_sips_impact_score(latest_snapshot)
        
        # Summary statistics
        all_claim_rates = [s.claim_rate for s in snapshots]
        all_climate_losses = [s.climate_loss_rate for s in snapshots]
        all_net_margins = [s.net_margin for s in snapshots]
        all_premiums = [s.average_premium for s in snapshots]
        
        # Calculate additional statistics
        stats = {
            "claim_rate": {
                "min": min(all_claim_rates),
                "max": max(all_claim_rates),
                "avg": sum(all_claim_rates) / len(all_claim_rates),
                "trend": "decreasing" if all_claim_rates[-1] < all_claim_rates[0] else "increasing"
            },
            "climate_loss_rate": {
                "min": min(all_climate_losses),
                "max": max(all_climate_losses),
                "avg": sum(all_climate_losses) / len(all_climate_losses),
                "trend": "decreasing" if all_climate_losses[-1] < all_climate_losses[0] else "increasing"
            },
            "net_margin": {
                "min": min(all_net_margins),
                "max": max(all_net_margins),
                "avg": sum(all_net_margins) / len(all_net_margins),
                "trend": "increasing" if all_net_margins[-1] > all_net_margins[0] else "decreasing"
            },
            "average_premium": {
                "min": min(all_premiums),
                "max": max(all_premiums),
                "avg": sum(all_premiums) / len(all_premiums),
                "trend": "increasing" if all_premiums[-1] > all_premiums[0] else "decreasing"
            }
        }
        
        return {
            "dashboard_summary": {
                "period_analyzed": {
                    "start_date": earliest_snapshot.date.isoformat(),
                    "end_date": latest_snapshot.date.isoformat(),
                    "days_spanned": (latest_snapshot.date - earliest_snapshot.date).days
                },
                "current_metrics": {
                    "taxa_sinistralidade": latest_snapshot.claim_rate,
                    "sinistralidade_climatica": latest_snapshot.climate_loss_rate,
                    "margem_liquida": latest_snapshot.net_margin,
                    "rejeicoes": latest_snapshot.rejection_rate,
                    "premio_medio": latest_snapshot.average_premium,
                    "retencao_clientes": latest_snapshot.client_retention,
                    "capital_economico": latest_snapshot.economic_capital
                },
                "improvements": {
                    "claim_rate_improvement": f"{claim_improvement:+.2f}%",
                    "climate_loss_improvement": f"{climate_loss_improvement:+.2f}%",
                    "margin_improvement": f"{margin_improvement:+.2f}%",
                    "retention_improvement": f"{retention_improvement:+.2f}%",
                    "premium_growth": f"{premium_growth:+.2f}%"
                },
                "sips_impact_score": sips_score,
                "snapshots_count": len(snapshots)
            },
            "statistics": stats,
            "key_findings": [
                f"SIPS-Climate system has shown {abs(claim_improvement):.1f}% improvement in claim rates",
                f"Climate-related losses reduced by {abs(climate_loss_improvement):.1f}%",
                f"Net margin improved by {margin_improvement:+.2f} percentage points",
                f"Average premium increased by {premium_growth:+.2f}%",
                f"Client retention improved by {retention_improvement:+.2f}%"
            ],
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard summary generation failed: {str(e)}")

@router.get("/sips-analytics/specification")
async def get_performance_analytics_specification():
    """
    Get specification and requirements for SIPS-Climate performance analytics
    """
    return {
        "title": "SIPS-Climate Performance Analytics Specification",
        "version": "1.0",
        "description": "Performance metrics tracking based on demonstrated SIPS-Climate improvements",
        "demonstrated_improvements": {
            "taxa_sinistralidade": {"before": "65%", "after": "58%", "improvement": "-7pp"},
            "sinistralidade_climatica": {"before": "42%", "after": "31%", "improvement": "-11pp"},
            "margem_liquida": {"before": "8%", "after": "14%", "improvement": "+6pp"},
            "rejeicoes": {"before": "5%", "after": "12%", "improvement": "+7pp"}, 
            "premio_medio": {"before": "R$ 1.200", "after": "R$ 1.650", "improvement": "+38%"},
            "retencao_clientes": {"before": "78%", "after": "85%", "improvement": "+7pp"},
            "capital_economico": {"before": "R$ 45M", "after": "R$ 52M", "improvement": "+15%"}
        },
        "tracked_metrics": [
            "Taxa de sinistralidade",
            "Sinistralidade climática", 
            "Margem líquida",
            "Rejeições",
            "Prêmio médio",
            "Retenção clientes",
            "Capital econômico"
        ],
        "metric_weights": {
            "taxa_sinistralidade": 0.20,
            "sinistralidade_climatica": 0.15, 
            "margem_liquida": 0.20,
            "rejeicoes": 0.10,
            "premio_medio": 0.10,
            "retencao_clientes": 0.15,
            "capital_economico": 0.10
        },
        "improvement_directions": {
            "taxa_sinistralidade": "decrease",
            "sinistralidade_climatica": "decrease",
            "margem_liquida": "increase",
            "rejeicoes": "increase", 
            "premio_medio": "increase",
            "retencao_clientes": "increase",
            "capital_economico": "increase"
        },
        "calculation_methods": [
            "Direct percentage change calculation",
            "Weighted impact scoring",
            "Trend analysis over time periods",
            "Comparison against baseline and target metrics"
        ],
        "reporting_features": [
            "Performance deltas calculation",
            "Impact score generation",
            "Trend analysis",
            "Dashboard summaries",
            "Recommendations based on metrics"
        ],
        "implementation_notes": [
            "Real-time performance tracking",
            "Historical trend analysis",
            "Comparative benchmarking",
            "Automated improvement detection"
        ],
        "compliance_requirements": [
            "Accurate performance measurement",
            "Transparent metric calculation",
            "Regular reporting schedules",
            "Audit trail for calculations"
        ],
        "timestamp": datetime.now().isoformat()
    }