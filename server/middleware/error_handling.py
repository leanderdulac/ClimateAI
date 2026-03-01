"""
Advanced Error Handling Middleware for ClimateWise
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AdvancedErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Advanced error handling middleware that provides additional error tracking
    and reporting capabilities beyond the exception handlers.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            response = await call_next(request)

            # Log successful requests with timing information
            if hasattr(request.state, "start_time"):
                duration = datetime.utcnow() - request.state.start_time
                logger.info(
                    f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration.total_seconds():.3f}s",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration": duration.total_seconds(),
                        "client_host": request.client.host if request.client else None,
                    },
                )

            return response

        except StarletteHTTPException:
            # Re-raise HTTP exceptions to be handled by registered exception handlers
            raise

        except Exception as e:
            # Generate unique trace ID for this error
            trace_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            # Log the error with full context
            logger.error(
                f"Unhandled error in request: {request.method} {request.url.path}",
                extra={
                    "trace_id": trace_id,
                    "timestamp": timestamp,
                    "method": request.method,
                    "path": request.url.path,
                    "client_host": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                },
                exc_info=True,  # Include full stack trace
            )

            # Return a generic error response
            error_response = {
                "error_code": "REQUEST_PROCESSING_ERROR",
                "message": "An error occurred while processing your request",
                "trace_id": trace_id,
                "timestamp": timestamp,
            }

            return JSONResponse(status_code=500, content=error_response)


def setup_error_middleware(app):
    """
    Sets up the advanced error handling middleware for the FastAPI application.
    """
    app.add_middleware(AdvancedErrorHandlingMiddleware)
    logger.info("Advanced error handling middleware registered")
