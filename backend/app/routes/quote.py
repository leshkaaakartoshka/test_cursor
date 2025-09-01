"""Quote generation endpoint."""

import asyncio
import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import Settings, get_settings, LookupSource
from app.models.schemas import QuoteForm, QuoteResponse
from app.providers.lookup.base import LookupProvider
from app.providers.lookup.sheets import SheetsLookupProvider
from app.providers.lookup.postgres import PostgresLookupProvider
from app.services.llm import LLMService
from app.services.pdf import PDFService
from app.services.telegram import TelegramService
from app.middleware.errors import QuoteGenerationError

router = APIRouter()


def get_lookup_provider(settings: Settings) -> LookupProvider:
    """Get the appropriate lookup provider based on configuration."""
    if settings.lookup_source == LookupSource.SHEETS:
        return SheetsLookupProvider(settings)
    elif settings.lookup_source == LookupSource.POSTGRES:
        return PostgresLookupProvider(settings)
    else:
        raise ValueError(f"Unsupported lookup source: {settings.lookup_source}")


@router.post("/api/quote", response_model=QuoteResponse)
async def generate_quote(
    quote_form: QuoteForm,
    settings: Settings = Depends(get_settings)
):
    """
    Generate a quote based on form data.
    
    This endpoint:
    1. Validates the input data
    2. Looks up pricing information
    3. Generates structured output via LLM
    4. Creates a PDF
    5. Sends the PDF to Telegram
    6. Returns the PDF URL
    """
    start_time = time.time()
    lead_id = None
    
    try:
        # Initialize services
        lookup_provider = get_lookup_provider(settings)
        llm_service = LLMService(settings)
        pdf_service = PDFService(settings)
        telegram_service = TelegramService(settings)
        
        # Step 1: Lookup pricing
        lookup_start = time.time()
        lookup_result = await lookup_provider.lookup_price(
            fefco=quote_form.fefco,
            x_mm=quote_form.x_mm,
            y_mm=quote_form.y_mm,
            z_mm=quote_form.z_mm,
            material=quote_form.material,
            print=quote_form.print,
            sla_type=quote_form.sla_type,
            qty=quote_form.qty
        )
        lookup_ms = int((time.time() - lookup_start) * 1000)
        
        if lookup_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price pack not found"
            )
        
        # Step 2: Generate LLM response
        llm_start = time.time()
        llm_response = await llm_service.generate_quote(quote_form, lookup_result)
        llm_ms = int((time.time() - llm_start) * 1000)
        lead_id = llm_response.lead_id
        
        # Step 3: Generate PDF
        pdf_start = time.time()
        pdf_path = pdf_service.get_pdf_path(lead_id)
        await pdf_service.html_to_pdf(
            html_content=llm_response.html_block,
            output_path=pdf_path,
            lead_id=lead_id
        )
        pdf_ms = int((time.time() - pdf_start) * 1000)
        
        # Step 4: Send to Telegram
        tg_start = time.time()
        caption = (
            f"КП {lead_id} — {quote_form.fefco} "
            f"{quote_form.x_mm}×{quote_form.y_mm}×{quote_form.z_mm}, "
            f"{quote_form.qty} шт"
        )
        
        telegram_success = await telegram_service.send_pdf(
            file_path=pdf_path,
            caption=caption,
            lead_id=lead_id
        )
        tg_ms = int((time.time() - tg_start) * 1000)
        
        if not telegram_success:
            # Log warning but don't fail the request
            print(f"Warning: Failed to send PDF to Telegram for lead {lead_id}")
        
        # Step 5: Return response
        total_ms = int((time.time() - start_time) * 1000)
        pdf_url = pdf_service.get_pdf_url(lead_id)
        
        # Log performance metrics
        print(f"Quote generation completed for {lead_id}: "
              f"lookup={lookup_ms}ms, llm={llm_ms}ms, pdf={pdf_ms}ms, "
              f"telegram={tg_ms}ms, total={total_ms}ms")
        
        return QuoteResponse(
            ok=True,
            pdf_url=pdf_url,
            lead_id=lead_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Quote generation failed: {e}"
        print(f"Error for lead {lead_id or 'unknown'}: {error_msg}")
        raise QuoteGenerationError(error_msg)


@router.get("/pdf/{lead_id}.pdf")
async def serve_pdf(
    lead_id: str,
    settings: Settings = Depends(get_settings)
):
    """
    Serve PDF file by lead ID.
    
    Args:
        lead_id: Lead ID to serve PDF for
        
    Returns:
        PDF file or 404 if not found
    """
    pdf_service = PDFService(settings)
    pdf_path = pdf_service.get_pdf_path(lead_id)
    
    if not pdf_service.pdf_exists(lead_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found"
        )
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{lead_id}.pdf"
    )