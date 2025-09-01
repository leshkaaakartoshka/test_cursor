"""Tests for lookup providers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.providers.lookup.sheets import SheetsLookupProvider
from app.providers.lookup.postgres import PostgresLookupProvider
from app.core.config import Settings, LookupSource, LookupPolicy


class TestSheetsLookupProvider:
    """Test Google Sheets lookup provider."""
    
    @pytest.fixture
    def settings(self):
        return Settings(
            lookup_source=LookupSource.SHEETS,
            lookup_policy=LookupPolicy.STRICT,
            sheets_id="test_sheet",
            sheets_tab="TestTab"
        )
    
    @pytest.fixture
    def provider(self, settings):
        return SheetsLookupProvider(settings)
    
    @patch('app.providers.lookup.sheets.SheetsLookupProvider._load_sheet_data')
    def test_lookup_exact_match(self, mock_load_data, provider):
        """Test exact match lookup."""
        mock_load_data.return_value = [
            {
                "fefco": "0201",
                "x_mm": "300",
                "y_mm": "200",
                "z_mm": "150",
                "material": "Микрогофрокартон Крафт",
                "print": "1+0",
                "sla_type": "стандарт",
                "qty_min": "500",
                "qty_max": "2000",
                "sku": "0201-T23-300x200x150",
                "lead_time_std": "4 дн",
                "lead_time_rush": "48 ч",
                "lead_time_strg": "7–10 дн",
                "price_std": "23.40",
                "margin_std": "24.0",
                "price_rush": "26.80",
                "margin_rush": "28.0",
                "price_strg": "21.70",
                "margin_strg": "20.0",
                "terms": "Материал: Микрогофрокартон Крафт; Печать: 1+0"
            }
        ]
        
        result = await provider.lookup_price(
            fefco="0201",
            x_mm=300,
            y_mm=200,
            z_mm=150,
            material="Микрогофрокартон Крафт",
            print="1+0",
            sla_type="стандарт",
            qty=1000
        )
        
        assert result is not None
        assert result.sku == "0201-T23-300x200x150"
        assert result.prices.std.price_per_unit == 23.40
    
    @patch('app.providers.lookup.sheets.SheetsLookupProvider._load_sheet_data')
    def test_lookup_no_match_strict(self, mock_load_data, provider):
        """Test no match with strict policy."""
        mock_load_data.return_value = []
        
        result = await provider.lookup_price(
            fefco="0201",
            x_mm=300,
            y_mm=200,
            z_mm=150,
            material="Микрогофрокартон Крафт",
            print="1+0",
            sla_type="стандарт",
            qty=1000
        )
        
        assert result is None
    
    @patch('app.providers.lookup.sheets.SheetsLookupProvider._load_sheet_data')
    def test_lookup_fallback_policy(self, mock_load_data):
        """Test fallback policy."""
        settings = Settings(
            lookup_source=LookupSource.SHEETS,
            lookup_policy=LookupPolicy.FALLBACK,
            sheets_id="test_sheet",
            sheets_tab="TestTab"
        )
        provider = SheetsLookupProvider(settings)
        
        mock_load_data.return_value = [
            {
                "fefco": "0201",
                "x_mm": "300",
                "y_mm": "200",
                "z_mm": "150",
                "material": "Микрогофрокартон Крафт",
                "print": "1+0",
                "sla_type": "стандарт",
                "qty_min": "2000",
                "qty_max": "5000",
                "sku": "0201-T23-300x200x150-fallback",
                "lead_time_std": "4 дн",
                "lead_time_rush": "48 ч",
                "lead_time_strg": "7–10 дн",
                "price_std": "22.00",
                "margin_std": "22.0",
                "price_rush": "25.00",
                "margin_rush": "25.0",
                "price_strg": "20.00",
                "margin_strg": "18.0",
                "terms": "Материал: Микрогофрокартон Крафт; Печать: 1+0"
            }
        ]
        
        result = await provider.lookup_price(
            fefco="0201",
            x_mm=300,
            y_mm=200,
            z_mm=150,
            material="Микрогофрокартон Крафт",
            print="1+0",
            sla_type="стандарт",
            qty=1000  # Outside the qty band, but fallback should find nearest
        )
        
        assert result is not None
        assert result.sku == "0201-T23-300x200x150-fallback"


class TestPostgresLookupProvider:
    """Test PostgreSQL lookup provider."""
    
    @pytest.fixture
    def settings(self):
        return Settings(
            lookup_source=LookupSource.POSTGRES,
            lookup_policy=LookupPolicy.STRICT,
            db_dsn="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.fixture
    def provider(self, settings):
        return PostgresLookupProvider(settings)
    
    @patch('app.providers.lookup.postgres.PostgresLookupProvider._get_pool')
    def test_lookup_exact_match(self, mock_get_pool, provider):
        """Test exact match lookup."""
        # Mock the database row
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "sku": "0201-T23-300x200x150",
            "qty_min": 500,
            "qty_max": 2000,
            "lead_time_std": "4 дн",
            "lead_time_rush": "48 ч",
            "lead_time_strg": "7–10 дн",
            "price_std": 23.40,
            "margin_std": 24.0,
            "price_rush": 26.80,
            "margin_rush": 28.0,
            "price_strg": 21.70,
            "margin_strg": 20.0,
            "terms": ["Материал: Микрогофрокартон Крафт", "Печать: 1+0"]
        }[key]
        
        # Mock the connection pool
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_get_pool.return_value = mock_pool
        
        result = await provider.lookup_price(
            fefco="0201",
            x_mm=300,
            y_mm=200,
            z_mm=150,
            material="Микрогофрокартон Крафт",
            print="1+0",
            sla_type="стандарт",
            qty=1000
        )
        
        assert result is not None
        assert result.sku == "0201-T23-300x200x150"
        assert result.prices.std.price_per_unit == 23.40
    
    @patch('app.providers.lookup.postgres.PostgresLookupProvider._get_pool')
    def test_lookup_no_match_strict(self, mock_get_pool, provider):
        """Test no match with strict policy."""
        # Mock the connection pool
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None  # No match
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_get_pool.return_value = mock_pool
        
        result = await provider.lookup_price(
            fefco="0201",
            x_mm=300,
            y_mm=200,
            z_mm=150,
            material="Микрогофрокартон Крафт",
            print="1+0",
            sla_type="стандарт",
            qty=1000
        )
        
        assert result is None