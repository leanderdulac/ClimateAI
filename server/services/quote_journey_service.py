"""Quote journey event persistence service."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.sqlalchemy_models import QuoteJourneyEvent


class QuoteJourneyService:
    async def log_event(
        self,
        *,
        db: AsyncSession,
        session_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> QuoteJourneyEvent:
        event_payload = payload or {}

        location = event_payload.get("location") or {}
        quote = event_payload.get("quote_context") or {}

        event = QuoteJourneyEvent(
            session_id=session_id,
            event_type=event_type,
            user_id=user_id,
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
            city=location.get("city"),
            state=location.get("state"),
            quote_premium=quote.get("premium"),
            quote_coverage_period=quote.get("coverage_period"),
            quote_frequency=quote.get("frequency"),
            quote_severity=quote.get("severity"),
            quote_event_id=quote.get("event_id"),
            quote_status=quote.get("status"),
            payload=event_payload,
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event


quote_journey_service = QuoteJourneyService()
