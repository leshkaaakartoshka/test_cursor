"""Test configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings
from app.models.schemas import LookupResult, PriceInfo, Prices, QtyBand, LeadTime


@pytest.fixture
def settings():
    """Test settings."""
    return Settings(
        openai_api_key="test_key",
        tg_bot_token="test_token",
        tg_manager_chat_id="test_chat",
        lookup_source="sheets",
        lookup_policy="strict",
        sheets_id="test_sheet",
        sheets_tab="TestTab",
        base_url="http://test.com",
        hash_salt="test_salt",
        pdf_dir="test_pdf"
    )


@pytest.fixture
def app(settings):
    """Test FastAPI app."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_lookup_result():
    """Mock lookup result."""
    return LookupResult(
        sku="0201-T23-300x200x150",
        qty_band=QtyBand(min=500, max=2000),
        lead_time=LeadTime(
            std="4 дн",
            rush="48 ч",
            strategic="7–10 дн"
        ),
        prices=Prices(
            std=PriceInfo(price_per_unit=23.40, margin_pct=24.0),
            rush=PriceInfo(price_per_unit=26.80, margin_pct=28.0),
            strategic=PriceInfo(price_per_unit=21.70, margin_pct=20.0)
        ),
        terms=[
            "Материал: Микрогофрокартон Крафт",
            "Печать: 1+0",
            "Доставка: По договоренности",
            "Оплата: 50% предоплата, 50% по факту",
            "OTIF: 95%"
        ]
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    from app.models.schemas import LLMResponse, Summary, Dimensions, Option, CTA
    
    return LLMResponse(
        lead_id="test-lead-123",
        echo_price_hash="test_hash_123",
        summary=Summary(
            fefco="0201",
            dimensions_mm=Dimensions(x=300, y=200, z=150),
            material="Микрогофрокартон Крафт",
            print="1+0",
            qty=1000,
            sku="0201-T23-300x200x150"
        ),
        options=[
            Option(
                name="Стандарт",
                price_per_unit_rub=23.40,
                lead_time="4 дн",
                margin_pct=24.0,
                notes=["Стандартные сроки изготовления"]
            ),
            Option(
                name="Срочно",
                price_per_unit_rub=26.80,
                lead_time="48 ч",
                margin_pct=28.0,
                notes=["Ускоренное изготовление"]
            ),
            Option(
                name="Стратегический",
                price_per_unit_rub=21.70,
                lead_time="7–10 дн",
                margin_pct=20.0,
                notes=["Оптимизированная цена"]
            )
        ],
        what_included=[
            "Изготовление коробок",
            "Печать в 1 цвет",
            "Упаковка для транспортировки"
        ],
        important=[
            "Цена действительна 7 дней",
            "Предоплата 50%"
        ],
        cta=CTA(
            confirm_variants=["Подтвердить заказ", "Связаться с менеджером"],
            followups=["Получить образцы", "Обсудить доставку"]
        ),
        html_block="<html><body>Test HTML</body></html>"
    )


@pytest.fixture
def sample_quote_form():
    """Sample quote form data."""
    from app.models.schemas import QuoteForm, FEFCOType, MaterialType, PrintType, SLAType
    
    return QuoteForm(
        fefco=FEFCOType.FEFCO_0201,
        x_mm=300,
        y_mm=200,
        z_mm=150,
        material=MaterialType.MICRO_CRAFT,
        print=PrintType.PRINT_1_0,
        qty=1000,
        sla_type=SLAType.STANDARD,
        company="ООО Ромашка",
        contact_name="Иван",
        city="Уфа",
        phone="+7 999 000-00-00",
        email="test@example.com",
        tg_username="@client"
    )