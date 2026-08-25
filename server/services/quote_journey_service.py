"""Quote journey event persistence service."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from models.sqlalchemy_models import QuoteJourneyEvent

logger = logging.getLogger("fimce")


def _is_missing_journey_table(exc: BaseException) -> bool:
    message = str(exc).lower()
    return "quote_journey_events" in message and (
        "no such table" in message
        or "does not exist" in message
        or "undefinedtable" in message
    )


class QuoteJourneyService:
    async def ensure_table(self, db: AsyncSession) -> None:
        def _create(sync_session) -> None:
            QuoteJourneyEvent.__table__.create(sync_session.get_bind(), checkfirst=True)

        await db.run_sync(_create)

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

        try:
            db.add(event)
            await db.commit()
            await db.refresh(event)
            return event
        except (OperationalError, ProgrammingError, DBAPIError) as exc:
            await db.rollback()
            if _is_missing_journey_table(exc):
                logger.warning("quote_journey_events missing; creating table and retrying")
                try:
                    await self.ensure_table(db)
                    db.add(event)
                    await db.commit()
                    await db.refresh(event)
                    return event
                except Exception:
                    await db.rollback()
                    logger.exception("Could not auto-create quote_journey_events")
                    return event
            logger.exception("Failed to persist quote journey event")
            return event


quote_journey_service = QuoteJourneyService()
