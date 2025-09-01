"""Pydantic models for all data contracts."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# Enums for validation
class FEFCOType(str, Enum):
    """Valid FEFCO codes."""
    FEFCO_0201 = "0201"
    FEFCO_0202 = "0202"
    FEFCO_0203 = "0203"
    FEFCO_0204 = "0204"
    FEFCO_0205 = "0205"
    FEFCO_0206 = "0206"
    FEFCO_0207 = "0207"
    FEFCO_0208 = "0208"
    FEFCO_0209 = "0209"
    FEFCO_0210 = "0210"


class MaterialType(str, Enum):
    """Valid material types."""
    MICRO_CRAFT = "Микрогофрокартон Крафт"
    MICRO_WHITE = "Микрогофрокартон Белый"
    SINGLE_WALL = "Одностенный гофрокартон"
    DOUBLE_WALL = "Двухстенный гофрокартон"
    TRIPLE_WALL = "Трехстенный гофрокартон"


class PrintType(str, Enum):
    """Valid print types."""
    PRINT_1_0 = "1+0"
    PRINT_1_1 = "1+1"
    PRINT_2_0 = "2+0"
    PRINT_2_1 = "2+1"
    PRINT_4_0 = "4+0"
    PRINT_4_1 = "4+1"


class SLAType(str, Enum):
    """Valid SLA types."""
    STANDARD = "стандарт"
    RUSH = "срочно"
    STRATEGIC = "стратегический"


class OptionType(str, Enum):
    """Valid option types for LLM response."""
    STANDARD = "Стандарт"
    RUSH = "Срочно"
    STRATEGIC = "Стратегический"


# Request/Response Models
class QuoteForm(BaseModel):
    """Quote form data from frontend."""
    
    # Box specifications
    fefco: FEFCOType
    x_mm: int = Field(..., ge=20, le=1200, description="Width in mm")
    y_mm: int = Field(..., ge=20, le=1200, description="Length in mm")
    z_mm: int = Field(..., ge=20, le=1200, description="Height in mm")
    
    # Material and print
    material: MaterialType
    print: PrintType
    
    # Quantity
    qty: int = Field(..., ge=1, le=100000, description="Quantity")
    sla_type: SLAType
    
    # Company information
    company: str = Field(..., min_length=1, max_length=200)
    contact_name: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    tg_username: Optional[str] = Field(None, max_length=50)
    
    # Optional consent flag for GDPR/152-FZ
    consent_given: Optional[bool] = Field(False)


class QuoteResponse(BaseModel):
    """Response from quote endpoint."""
    ok: bool
    pdf_url: Optional[str] = None
    lead_id: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["ok"] = "ok"


# Lookup Models
class QtyBand(BaseModel):
    """Quantity band definition."""
    min: int
    max: int


class LeadTime(BaseModel):
    """Lead time definitions."""
    std: str
    rush: str
    strategic: str


class PriceInfo(BaseModel):
    """Price information for a specific SLA type."""
    price_per_unit: float
    margin_pct: float


class Prices(BaseModel):
    """Price information for all SLA types."""
    std: PriceInfo
    rush: PriceInfo
    strategic: PriceInfo


class LookupResult(BaseModel):
    """Result from price lookup."""
    sku: str
    qty_band: QtyBand
    lead_time: LeadTime
    prices: Prices
    terms: List[str]


# LLM Models
class Dimensions(BaseModel):
    """Box dimensions."""
    x: int
    y: int
    z: int


class Summary(BaseModel):
    """Quote summary."""
    fefco: str
    dimensions_mm: Dimensions
    material: str
    print: str
    qty: int
    sku: str


class Option(BaseModel):
    """Quote option."""
    name: OptionType
    price_per_unit_rub: float
    lead_time: str
    margin_pct: float
    notes: Optional[List[str]] = None


class CTA(BaseModel):
    """Call to action."""
    confirm_variants: List[str]
    followups: Optional[List[str]] = None


class LLMResponse(BaseModel):
    """Response from OpenAI with structured output."""
    lead_id: str
    echo_price_hash: str
    summary: Summary
    options: List[Option] = Field(..., min_items=3, max_items=3)
    what_included: List[str]
    important: List[str]
    cta: CTA
    html_block: str
    
    @field_validator('options')
    @classmethod
    def validate_options_count(cls, v):
        if len(v) != 3:
            raise ValueError('Must have exactly 3 options')
        return v


class Buyer(BaseModel):
    """Buyer information."""
    company: str
    contact_name: str
    city: str
    phone: str
    email: str
    tg_username: Optional[str] = None


class Inputs(BaseModel):
    """Input specifications."""
    fefco: str
    x_mm: int
    y_mm: int
    z_mm: int
    material: str
    print: str
    qty: int
    sla_type: str


class LookupData(BaseModel):
    """Lookup data for LLM."""
    sku: str
    qty_band: QtyBand
    lead_time: LeadTime
    prices: Prices
    terms: List[str]


class Branding(BaseModel):
    """Branding information."""
    company_name: str = "CPQ System"
    logo_url: Optional[str] = None
    contact_info: str = "+7 (495) 123-45-67"


class Control(BaseModel):
    """Control information for LLM."""
    lead_id: str
    date_today: str
    valid_until: str
    price_hash: str


class LLMRequest(BaseModel):
    """Request payload for OpenAI."""
    control: Control
    buyer: Buyer
    inputs: Inputs
    lookup: LookupData
    branding: Branding


# Error Models
class ErrorResponse(BaseModel):
    """Error response format."""
    ok: bool = False
    error: str