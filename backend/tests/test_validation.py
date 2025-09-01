"""Tests for data validation."""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    QuoteForm, FEFCOType, MaterialType, PrintType, SLAType,
    LLMResponse, Summary, Dimensions, Option, CTA
)


class TestValidation:
    """Test data validation."""
    
    def test_valid_quote_form(self):
        """Test valid quote form."""
        form = QuoteForm(
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
            email="test@example.com"
        )
        
        assert form.fefco == FEFCOType.FEFCO_0201
        assert form.x_mm == 300
        assert form.email == "test@example.com"
    
    def test_invalid_dimensions(self):
        """Test invalid dimensions."""
        with pytest.raises(ValidationError):
            QuoteForm(
                fefco=FEFCOType.FEFCO_0201,
                x_mm=10,  # Too small
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
                email="test@example.com"
            )
    
    def test_invalid_quantity(self):
        """Test invalid quantity."""
        with pytest.raises(ValidationError):
            QuoteForm(
                fefco=FEFCOType.FEFCO_0201,
                x_mm=300,
                y_mm=200,
                z_mm=150,
                material=MaterialType.MICRO_CRAFT,
                print=PrintType.PRINT_1_0,
                qty=0,  # Too small
                sla_type=SLAType.STANDARD,
                company="ООО Ромашка",
                contact_name="Иван",
                city="Уфа",
                phone="+7 999 000-00-00",
                email="test@example.com"
            )
    
    def test_invalid_email(self):
        """Test invalid email format."""
        with pytest.raises(ValidationError):
            QuoteForm(
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
                email="invalid-email"  # Invalid format
            )
    
    def test_valid_llm_response(self):
        """Test valid LLM response."""
        response = LLMResponse(
            lead_id="test-lead-123",
            echo_price_hash="test_hash",
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
                    margin_pct=24.0
                ),
                Option(
                    name="Срочно",
                    price_per_unit_rub=26.80,
                    lead_time="48 ч",
                    margin_pct=28.0
                ),
                Option(
                    name="Стратегический",
                    price_per_unit_rub=21.70,
                    lead_time="7–10 дн",
                    margin_pct=20.0
                )
            ],
            what_included=["Изготовление коробок"],
            important=["Цена действительна 7 дней"],
            cta=CTA(confirm_variants=["Подтвердить заказ"]),
            html_block="<html><body>Test</body></html>"
        )
        
        assert len(response.options) == 3
        assert response.lead_id == "test-lead-123"
    
    def test_invalid_options_count(self):
        """Test LLM response with wrong number of options."""
        with pytest.raises(ValidationError):
            LLMResponse(
                lead_id="test-lead-123",
                echo_price_hash="test_hash",
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
                        margin_pct=24.0
                    )
                    # Only 1 option instead of 3
                ],
                what_included=["Изготовление коробок"],
                important=["Цена действительна 7 дней"],
                cta=CTA(confirm_variants=["Подтвердить заказ"]),
                html_block="<html><body>Test</body></html>"
            )