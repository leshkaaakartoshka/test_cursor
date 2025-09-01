"""Tests for quote API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.models.schemas import QuoteForm, FEFCOType, MaterialType, PrintType, SLAType


class TestQuoteAPI:
    """Test quote API endpoints."""
    
    def test_health_endpoint(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    @patch('app.routes.quote.get_lookup_provider')
    @patch('app.services.llm.LLMService.generate_quote')
    @patch('app.services.pdf.PDFService.html_to_pdf')
    @patch('app.services.telegram.TelegramService.send_pdf')
    def test_quote_generation_success(
        self,
        mock_telegram,
        mock_pdf,
        mock_llm,
        mock_lookup,
        client: TestClient,
        sample_quote_form,
        mock_lookup_result,
        mock_llm_response
    ):
        """Test successful quote generation."""
        # Setup mocks
        mock_lookup.return_value.lookup_price = AsyncMock(return_value=mock_lookup_result)
        mock_llm.return_value = mock_llm_response
        mock_pdf.return_value = "test_path.pdf"
        mock_telegram.return_value = True
        
        # Make request
        response = client.post("/api/quote", json=sample_quote_form.dict())
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "pdf_url" in data
        assert "lead_id" in data
        assert data["lead_id"] == "test-lead-123"
    
    def test_quote_validation_errors(self, client: TestClient):
        """Test quote form validation."""
        # Test invalid dimensions
        invalid_data = {
            "fefco": "0201",
            "x_mm": 10,  # Too small
            "y_mm": 200,
            "z_mm": 150,
            "material": "Микрогофрокартон Крафт",
            "print": "1+0",
            "qty": 1000,
            "sla_type": "стандарт",
            "company": "ООО Ромашка",
            "contact_name": "Иван",
            "city": "Уфа",
            "phone": "+7 999 000-00-00",
            "email": "test@example.com"
        }
        
        response = client.post("/api/quote", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_quote_invalid_email(self, client: TestClient):
        """Test invalid email format."""
        invalid_data = {
            "fefco": "0201",
            "x_mm": 300,
            "y_mm": 200,
            "z_mm": 150,
            "material": "Микрогофрокартон Крафт",
            "print": "1+0",
            "qty": 1000,
            "sla_type": "стандарт",
            "company": "ООО Ромашка",
            "contact_name": "Иван",
            "city": "Уфа",
            "phone": "+7 999 000-00-00",
            "email": "invalid-email"  # Invalid email
        }
        
        response = client.post("/api/quote", json=invalid_data)
        assert response.status_code == 422
    
    @patch('app.routes.quote.get_lookup_provider')
    def test_quote_lookup_not_found(
        self,
        mock_lookup,
        client: TestClient,
        sample_quote_form
    ):
        """Test quote when lookup returns no results."""
        # Setup mock to return None (not found)
        mock_lookup.return_value.lookup_price = AsyncMock(return_value=None)
        
        response = client.post("/api/quote", json=sample_quote_form.dict())
        
        assert response.status_code == 404
        data = response.json()
        assert data["ok"] is False
        assert "Price pack not found" in data["error"]
    
    @patch('app.routes.quote.get_lookup_provider')
    @patch('app.services.llm.LLMService.generate_quote')
    def test_quote_llm_failure(
        self,
        mock_llm,
        mock_lookup,
        client: TestClient,
        sample_quote_form,
        mock_lookup_result
    ):
        """Test quote when LLM generation fails."""
        # Setup mocks
        mock_lookup.return_value.lookup_price = AsyncMock(return_value=mock_lookup_result)
        mock_llm.side_effect = Exception("LLM generation failed")
        
        response = client.post("/api/quote", json=sample_quote_form.dict())
        
        assert response.status_code == 502
        data = response.json()
        assert data["ok"] is False
        assert "Temporary error generating the offer" in data["error"]
    
    @patch('app.routes.quote.get_lookup_provider')
    @patch('app.services.llm.LLMService.generate_quote')
    @patch('app.services.pdf.PDFService.html_to_pdf')
    def test_quote_pdf_failure(
        self,
        mock_pdf,
        mock_llm,
        mock_lookup,
        client: TestClient,
        sample_quote_form,
        mock_lookup_result,
        mock_llm_response
    ):
        """Test quote when PDF generation fails."""
        # Setup mocks
        mock_lookup.return_value.lookup_price = AsyncMock(return_value=mock_lookup_result)
        mock_llm.return_value = mock_llm_response
        mock_pdf.side_effect = Exception("PDF generation failed")
        
        response = client.post("/api/quote", json=sample_quote_form.dict())
        
        assert response.status_code == 502
        data = response.json()
        assert data["ok"] is False
        assert "Temporary error generating the offer" in data["error"]
    
    @patch('app.services.pdf.PDFService.pdf_exists')
    def test_serve_pdf_not_found(self, mock_exists, client: TestClient):
        """Test serving non-existent PDF."""
        mock_exists.return_value = False
        
        response = client.get("/pdf/nonexistent.pdf")
        
        assert response.status_code == 404
        data = response.json()
        assert "PDF not found" in data["detail"]
    
    @patch('app.services.pdf.PDFService.pdf_exists')
    @patch('app.services.pdf.PDFService.get_pdf_path')
    def test_serve_pdf_success(self, mock_path, mock_exists, client: TestClient):
        """Test serving existing PDF."""
        mock_exists.return_value = True
        mock_path.return_value = "test.pdf"
        
        with patch('fastapi.responses.FileResponse') as mock_file_response:
            response = client.get("/pdf/test-lead-123.pdf")
            # FileResponse is mocked, so we just check the call was made
            mock_file_response.assert_called_once()