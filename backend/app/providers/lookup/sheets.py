"""Google Sheets lookup provider."""

import asyncio
import json
from typing import Dict, List, Optional

import httpx
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from app.core.config import Settings
from app.models.schemas import LookupResult, PriceInfo, Prices, QtyBand, LeadTime
from app.providers.lookup.base import LookupProvider


class SheetsLookupProvider(LookupProvider):
    """Google Sheets implementation of lookup provider."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.service = None
        self._cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 60  # 60 seconds
        
    async def _get_service(self):
        """Get or create Google Sheets service."""
        if self.service is None:
            # In production, you'd load credentials from a file or environment
            # For now, we'll use a mock approach
            credentials = Credentials.from_service_account_file(
                "credentials.json",  # This should be configured properly
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            self.service = build("sheets", "v4", credentials=credentials)
        return self.service
    
    async def _load_sheet_data(self) -> List[Dict]:
        """Load data from Google Sheets with caching."""
        import time
        current_time = time.time()
        
        # Check cache
        if current_time - self._cache_timestamp < self._cache_ttl and self._cache:
            return self._cache
        
        try:
            service = await self._get_service()
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.settings.sheets_id,
                range=f"{self.settings.sheets_tab}!A:Z"
            ).execute()
            
            values = result.get("values", [])
            if not values:
                return []
            
            # Convert to list of dictionaries
            headers = values[0]
            data = []
            for row in values[1:]:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                    else:
                        row_dict[header] = ""
                data.append(row_dict)
            
            # Update cache
            self._cache = data
            self._cache_timestamp = current_time
            
            return data
            
        except Exception as e:
            print(f"Error loading sheet data: {e}")
            return []
    
    def _parse_price_info(self, price_str: str, margin_str: str) -> PriceInfo:
        """Parse price and margin from string values."""
        try:
            price = float(price_str.replace(",", "."))
            margin = float(margin_str.replace(",", "."))
            return PriceInfo(price_per_unit=price, margin_pct=margin)
        except (ValueError, AttributeError):
            return PriceInfo(price_per_unit=0.0, margin_pct=0.0)
    
    def _parse_qty_band(self, qty_min_str: str, qty_max_str: str) -> QtyBand:
        """Parse quantity band from string values."""
        try:
            qty_min = int(qty_min_str)
            qty_max = int(qty_max_str)
            return QtyBand(min=qty_min, max=qty_max)
        except (ValueError, AttributeError):
            return QtyBand(min=0, max=0)
    
    def _parse_terms(self, terms_str: str) -> List[str]:
        """Parse terms from string (assuming semicolon-separated)."""
        if not terms_str:
            return []
        return [term.strip() for term in terms_str.split(";") if term.strip()]
    
    async def lookup_price(
        self,
        fefco: str,
        x_mm: int,
        y_mm: int,
        z_mm: int,
        material: str,
        print: str,
        sla_type: str,
        qty: int,
    ) -> Optional[LookupResult]:
        """Look up price information from Google Sheets."""
        data = await self._load_sheet_data()
        
        # Find exact match
        for row in data:
            if (
                row.get("fefco") == fefco
                and int(row.get("x_mm", 0)) == x_mm
                and int(row.get("y_mm", 0)) == y_mm
                and int(row.get("z_mm", 0)) == z_mm
                and row.get("material") == material
                and row.get("print") == print
                and row.get("sla_type") == sla_type
            ):
                qty_min = int(row.get("qty_min", 0))
                qty_max = int(row.get("qty_max", 0))
                
                if qty_min <= qty <= qty_max:
                    # Found exact match
                    return LookupResult(
                        sku=row.get("sku", ""),
                        qty_band=self._parse_qty_band(
                            row.get("qty_min", "0"),
                            row.get("qty_max", "0")
                        ),
                        lead_time=LeadTime(
                            std=row.get("lead_time_std", ""),
                            rush=row.get("lead_time_rush", ""),
                            strategic=row.get("lead_time_strg", "")
                        ),
                        prices=Prices(
                            std=self._parse_price_info(
                                row.get("price_std", "0"),
                                row.get("margin_std", "0")
                            ),
                            rush=self._parse_price_info(
                                row.get("price_rush", "0"),
                                row.get("margin_rush", "0")
                            ),
                            strategic=self._parse_price_info(
                                row.get("price_strg", "0"),
                                row.get("margin_strg", "0")
                            )
                        ),
                        terms=self._parse_terms(row.get("terms", ""))
                    )
        
        # If strict policy, return None
        if self.settings.lookup_policy == "strict":
            return None
        
        # Fallback policy: find nearest qty band
        best_match = None
        min_distance = float("inf")
        
        for row in data:
            if (
                row.get("fefco") == fefco
                and int(row.get("x_mm", 0)) == x_mm
                and int(row.get("y_mm", 0)) == y_mm
                and int(row.get("z_mm", 0)) == z_mm
                and row.get("material") == material
                and row.get("print") == print
                and row.get("sla_type") == sla_type
            ):
                qty_min = int(row.get("qty_min", 0))
                qty_max = int(row.get("qty_max", 0))
                
                # Calculate distance to qty band
                if qty < qty_min:
                    distance = qty_min - qty
                elif qty > qty_max:
                    distance = qty - qty_max
                else:
                    distance = 0
                
                if distance < min_distance:
                    min_distance = distance
                    best_match = row
        
        if best_match:
            return LookupResult(
                sku=best_match.get("sku", ""),
                qty_band=self._parse_qty_band(
                    best_match.get("qty_min", "0"),
                    best_match.get("qty_max", "0")
                ),
                lead_time=LeadTime(
                    std=best_match.get("lead_time_std", ""),
                    rush=best_match.get("lead_time_rush", ""),
                    strategic=best_match.get("lead_time_strg", "")
                ),
                prices=Prices(
                    std=self._parse_price_info(
                        best_match.get("price_std", "0"),
                        best_match.get("margin_std", "0")
                    ),
                    rush=self._parse_price_info(
                        best_match.get("price_rush", "0"),
                        best_match.get("margin_rush", "0")
                    ),
                    strategic=self._parse_price_info(
                        best_match.get("price_strg", "0"),
                        best_match.get("margin_strg", "0")
                    )
                ),
                terms=self._parse_terms(best_match.get("terms", ""))
            )
        
        return None
    
    async def health_check(self) -> bool:
        """Check if Google Sheets is accessible."""
        try:
            data = await self._load_sheet_data()
            return len(data) > 0
        except Exception:
            return False