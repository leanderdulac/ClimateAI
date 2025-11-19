import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.audit_service import audit_service

router = APIRouter()


@router.get("/alerts")
async def get_alerts(
    acknowledged: Optional[bool] = Query(
        None, description="Filter by acknowledged status"
    ),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    severity: Optional[str] = Query(
        None, description="Filter by severity (critical, high, medium, low)"
    ),
    limit: int = Query(
        50, description="Maximum number of alerts to return", ge=1, le=1000
    ),
    offset: int = Query(0, description="Number of alerts to skip", ge=0),
) -> Dict[str, Any]:
    """
    Get alerts with optional filtering
    """
    try:
        alerts = audit_service.get_alerts(
            limit=limit,
            offset=offset,
            acknowledged=acknowledged,
            resolved=resolved,
            severity=severity,
        )

        # Get total count for pagination
        total_count = len(audit_service.get_alerts(limit=10000))  # Get all for count

        return {
            "alerts": alerts,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving alerts: {str(e)}"
        )


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Mark an alert as acknowledged
    """
    try:
        success = audit_service.acknowledge_alert(alert_id)

        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": "Alert acknowledged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error acknowledging alert: {str(e)}"
        )


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolution_notes: Optional[str] = None):
    """
    Mark an alert as resolved
    """
    try:
        success = audit_service.resolve_alert(alert_id, resolution_notes)

        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": "Alert resolved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")


@router.get("/alerts/stats")
async def get_alert_stats():
    """
    Get alert statistics
    """
    try:
        stats = audit_service.get_alert_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving alert stats: {str(e)}"
        )


@router.get("/alerts/summary")
async def get_alert_summary():
    """
    Get alert summary with counts by severity and type
    """
    try:
        summary = audit_service.get_alert_summary()
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving alert summary: {str(e)}"
        )


@router.get("/logs")
async def get_audit_logs(
    operation: Optional[str] = Query(None, description="Filter by operation type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(
        100, description="Maximum number of logs to return", ge=1, le=1000
    ),
    offset: int = Query(0, description="Number of logs to skip", ge=0),
) -> Dict[str, Any]:
    """
    Get audit logs with optional filtering
    """
    try:
        # Parse dates if provided
        start_timestamp = None
        end_timestamp = None

        if start_date:
            try:
                start_timestamp = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use ISO format."
                )

        if end_date:
            try:
                end_timestamp = datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use ISO format."
                )

        logs = audit_service.get_audit_logs(
            operation=operation,
            resource_type=resource_type,
            user_id=user_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            limit=limit,
            offset=offset,
        )

        # Get total count for pagination
        total_count = len(audit_service.get_audit_logs(limit=10000))

        return {
            "logs": logs,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving audit logs: {str(e)}"
        )


@router.get("/compliance/report")
async def get_compliance_report(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
) -> Dict[str, Any]:
    """
    Get compliance report
    """
    try:
        # Parse dates if provided
        start_timestamp = None
        end_timestamp = None

        if start_date:
            try:
                start_timestamp = datetime.fromisoformat(
                    start_date.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use ISO format."
                )

        if end_date:
            try:
                end_timestamp = datetime.fromisoformat(
                    end_date.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use ISO format."
                )

        report = audit_service.get_compliance_report(
            start_timestamp=start_timestamp, end_timestamp=end_timestamp
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving compliance report: {str(e)}"
        )


@router.post("/compliance/rules")
async def add_compliance_rule(
    name: str,
    description: str,
    rule_type: str,
    conditions: Dict[str, Any],
    severity: str = "medium",
    is_active: bool = True,
) -> Dict[str, str]:
    """
    Add a new compliance rule
    """
    try:
        rule_id = audit_service.add_compliance_rule(
            name=name,
            description=description,
            rule_type=rule_type,
            conditions=conditions,
            severity=severity,
            is_active=is_active,
        )

        return {"rule_id": rule_id, "message": "Compliance rule added successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding compliance rule: {str(e)}"
        )


@router.get("/compliance/rules")
async def get_compliance_rules(
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> List[Dict[str, Any]]:
    """
    Get compliance rules
    """
    try:
        rules = audit_service.get_compliance_rules(is_active=is_active)
        return rules

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving compliance rules: {str(e)}"
        )
