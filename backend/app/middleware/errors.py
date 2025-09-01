"""Error handling middleware."""

import logging
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.models.schemas import ErrorResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle validation errors."""
    error_details = []
    
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
    else:
        error_details.append(str(exc))
    
    error_message = "Validation failed: " + "; ".join(error_details)
    
    logger.warning(f"Validation error: {error_message}")
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error=error_message).dict()
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail).dict()
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="Internal server error").dict()
    )


class QuoteGenerationError(Exception):
    """Custom exception for quote generation failures."""
    pass


async def quote_generation_exception_handler(
    request: Request,
    exc: QuoteGenerationError
) -> JSONResponse:
    """Handle quote generation errors."""
    logger.error(f"Quote generation error: {exc}")
    
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(error="Temporary error generating the offer (AI/PDF)").dict()
    )