"""LLM service for generating structured quotes."""

import json
from datetime import datetime, timedelta
from typing import Dict, Any

import openai
from openai import OpenAI

from app.core.config import Settings
from app.models.schemas import (
    LLMRequest, LLMResponse, QuoteForm, LookupResult,
    Control, Buyer, Inputs, LookupData, Branding
)
from app.utils.hash import compute_price_hash, generate_lead_id


class LLMService:
    """Service for interacting with OpenAI's structured outputs API."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)
        
        # JSON Schema for structured output
        self.response_schema = {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "echo_price_hash": {"type": "string"},
                "summary": {
                    "type": "object",
                    "properties": {
                        "fefco": {"type": "string"},
                        "dimensions_mm": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"},
                                "z": {"type": "integer"}
                            },
                            "required": ["x", "y", "z"]
                        },
                        "material": {"type": "string"},
                        "print": {"type": "string"},
                        "qty": {"type": "integer"},
                        "sku": {"type": "string"}
                    },
                    "required": ["fefco", "dimensions_mm", "material", "print", "qty", "sku"]
                },
                "options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "enum": ["Стандарт", "Срочно", "Стратегический"]},
                            "price_per_unit_rub": {"type": "number"},
                            "lead_time": {"type": "string"},
                            "margin_pct": {"type": "number"},
                            "notes": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "price_per_unit_rub", "lead_time", "margin_pct"]
                    },
                    "minItems": 3,
                    "maxItems": 3
                },
                "what_included": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "important": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "cta": {
                    "type": "object",
                    "properties": {
                        "confirm_variants": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "followups": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["confirm_variants"]
                },
                "html_block": {"type": "string"}
            },
            "required": [
                "lead_id", "echo_price_hash", "summary", "options",
                "what_included", "important", "cta", "html_block"
            ]
        }
    
    def _build_llm_payload(
        self,
        quote_form: QuoteForm,
        lookup_result: LookupResult,
        lead_id: str,
        price_hash: str
    ) -> LLMRequest:
        """Build the payload for LLM request."""
        
        # Calculate valid until date (7 days from now)
        valid_until = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        control = Control(
            lead_id=lead_id,
            date_today=datetime.now().strftime("%Y-%m-%d"),
            valid_until=valid_until,
            price_hash=price_hash
        )
        
        buyer = Buyer(
            company=quote_form.company,
            contact_name=quote_form.contact_name,
            city=quote_form.city,
            phone=quote_form.phone,
            email=quote_form.email,
            tg_username=quote_form.tg_username
        )
        
        inputs = Inputs(
            fefco=quote_form.fefco,
            x_mm=quote_form.x_mm,
            y_mm=quote_form.y_mm,
            z_mm=quote_form.z_mm,
            material=quote_form.material,
            print=quote_form.print,
            qty=quote_form.qty,
            sla_type=quote_form.sla_type
        )
        
        lookup_data = LookupData(
            sku=lookup_result.sku,
            qty_band=lookup_result.qty_band,
            lead_time=lookup_result.lead_time,
            prices=lookup_result.prices,
            terms=lookup_result.terms
        )
        
        branding = Branding()
        
        return LLMRequest(
            control=control,
            buyer=buyer,
            inputs=inputs,
            lookup=lookup_data,
            branding=branding
        )
    
    def _compute_price_hash(
        self,
        lookup_result: LookupResult,
        qty: int
    ) -> str:
        """Compute price hash for validation."""
        prices_dict = {
            "std": {
                "price_per_unit": lookup_result.prices.std.price_per_unit,
                "margin_pct": lookup_result.prices.std.margin_pct
            },
            "rush": {
                "price_per_unit": lookup_result.prices.rush.price_per_unit,
                "margin_pct": lookup_result.prices.rush.margin_pct
            },
            "strategic": {
                "price_per_unit": lookup_result.prices.strategic.price_per_unit,
                "margin_pct": lookup_result.prices.strategic.margin_pct
            }
        }
        
        qty_band_dict = {
            "min": lookup_result.qty_band.min,
            "max": lookup_result.qty_band.max
        }
        
        lead_time_dict = {
            "std": lookup_result.lead_time.std,
            "rush": lookup_result.lead_time.rush,
            "strategic": lookup_result.lead_time.strategic
        }
        
        return compute_price_hash(
            prices_dict,
            qty,
            qty_band_dict,
            lead_time_dict,
            self.settings.hash_salt
        )
    
    async def generate_quote(
        self,
        quote_form: QuoteForm,
        lookup_result: LookupResult
    ) -> LLMResponse:
        """
        Generate a structured quote using OpenAI's structured outputs.
        
        Args:
            quote_form: Quote form data
            lookup_result: Lookup result with pricing
            
        Returns:
            LLMResponse with structured quote data
            
        Raises:
            ValueError: If LLM response doesn't match schema or hash
        """
        lead_id = generate_lead_id()
        price_hash = self._compute_price_hash(lookup_result, quote_form.qty)
        
        # Build LLM payload
        llm_payload = self._build_llm_payload(
            quote_form, lookup_result, lead_id, price_hash
        )
        
        # Create the prompt
        prompt = self._create_prompt(llm_payload)
        
        try:
            # Call OpenAI with structured output
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional sales assistant for a packaging company. Generate a detailed commercial proposal in Russian with exactly 3 pricing options."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "quote_response",
                        "schema": self.response_schema,
                        "strict": True
                    }
                }
            )
            
            # Parse response
            response_content = response.choices[0].message.content
            response_data = json.loads(response_content)
            
            # Validate response
            llm_response = LLMResponse(**response_data)
            
            # Validate price hash
            if llm_response.echo_price_hash != price_hash:
                raise ValueError("Price hash mismatch in LLM response")
            
            # Validate options count
            if len(llm_response.options) != 3:
                raise ValueError(f"Expected exactly 3 options, got {len(llm_response.options)}")
            
            return llm_response
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            raise ValueError(f"LLM generation failed: {e}")
    
    def _create_prompt(self, payload: LLMRequest) -> str:
        """Create the prompt for LLM."""
        return f"""
Создайте коммерческое предложение для упаковочной компании на основе следующих данных:

КОНТРОЛЬ:
- ID заявки: {payload.control.lead_id}
- Дата: {payload.control.date_today}
- Действительно до: {payload.control.valid_until}
- Хеш цен: {payload.control.price_hash}

ПОКУПАТЕЛЬ:
- Компания: {payload.buyer.company}
- Контакт: {payload.buyer.contact_name}
- Город: {payload.buyer.city}
- Телефон: {payload.buyer.phone}
- Email: {payload.buyer.email}
- Telegram: {payload.buyer.tg_username or 'не указан'}

ПАРАМЕТРЫ ЗАКАЗА:
- FEFCO: {payload.inputs.fefco}
- Размеры: {payload.inputs.x_mm}×{payload.inputs.y_mm}×{payload.inputs.z_mm} мм
- Материал: {payload.inputs.material}
- Печать: {payload.inputs.print}
- Количество: {payload.inputs.qty} шт
- Тип SLA: {payload.inputs.sla_type}

ДАННЫЕ ИЗ КАТАЛОГА:
- SKU: {payload.lookup.sku}
- Количественный диапазон: {payload.lookup.qty_band.min}-{payload.lookup.qty_band.max} шт
- Сроки изготовления:
  * Стандарт: {payload.lookup.lead_time.std}
  * Срочно: {payload.lookup.lead_time.rush}
  * Стратегический: {payload.lookup.lead_time.strategic}
- Цены:
  * Стандарт: {payload.lookup.prices.std.price_per_unit} руб/шт (маржа {payload.lookup.prices.std.margin_pct}%)
  * Срочно: {payload.lookup.prices.rush.price_per_unit} руб/шт (маржа {payload.lookup.prices.rush.margin_pct}%)
  * Стратегический: {payload.lookup.prices.strategic.price_per_unit} руб/шт (маржа {payload.lookup.prices.strategic.margin_pct}%)
- Условия: {', '.join(payload.lookup.terms)}

БРЕНДИНГ:
- Название компании: {payload.branding.company_name}
- Контакты: {payload.branding.contact_info}

ТРЕБОВАНИЯ:
1. Создайте ТОЧНО 3 варианта: "Стандарт", "Срочно", "Стратегический"
2. Используйте точные цены и сроки из каталога
3. Включите профессиональное описание каждого варианта
4. Добавьте важные условия и что входит в стоимость
5. Создайте призыв к действию
6. Сгенерируйте HTML-блок для PDF
7. Обязательно верните echo_price_hash равным {payload.control.price_hash}

Ответ должен быть в формате JSON согласно схеме.
"""