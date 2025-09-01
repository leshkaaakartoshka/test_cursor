"""PostgreSQL lookup provider."""

import asyncio
from typing import Optional

import asyncpg
from asyncpg import Pool

from app.core.config import Settings
from app.models.schemas import LookupResult, PriceInfo, Prices, QtyBand, LeadTime
from app.providers.lookup.base import LookupProvider


class PostgresLookupProvider(LookupProvider):
    """PostgreSQL implementation of lookup provider."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pool: Optional[Pool] = None
    
    async def _get_pool(self) -> Pool:
        """Get or create connection pool."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                self.settings.db_dsn,
                min_size=1,
                max_size=10,
                command_timeout=30
            )
        return self.pool
    
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
        """Look up price information from PostgreSQL."""
        pool = await self._get_pool()
        
        # Exact match query
        query = """
        SELECT * FROM quote_catalog
        WHERE fefco = $1 AND x_mm = $2 AND y_mm = $3 AND z_mm = $4
          AND material = $5 AND print = $6 AND sla_type = $7
          AND $8 BETWEEN qty_min AND qty_max
        LIMIT 1;
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                query, fefco, x_mm, y_mm, z_mm, material, print, sla_type, qty
            )
            
            if row:
                return LookupResult(
                    sku=row["sku"],
                    qty_band=QtyBand(min=row["qty_min"], max=row["qty_max"]),
                    lead_time=LeadTime(
                        std=row["lead_time_std"],
                        rush=row["lead_time_rush"],
                        strategic=row["lead_time_strg"]
                    ),
                    prices=Prices(
                        std=PriceInfo(
                            price_per_unit=float(row["price_std"]),
                            margin_pct=float(row["margin_std"])
                        ),
                        rush=PriceInfo(
                            price_per_unit=float(row["price_rush"]),
                            margin_pct=float(row["margin_rush"])
                        ),
                        strategic=PriceInfo(
                            price_per_unit=float(row["price_strg"]),
                            margin_pct=float(row["margin_strg"])
                        )
                    ),
                    terms=row["terms"] or []
                )
        
        # If strict policy, return None
        if self.settings.lookup_policy == "strict":
            return None
        
        # Fallback policy: find nearest qty band
        fallback_query = """
        SELECT * FROM quote_catalog
        WHERE fefco = $1 AND x_mm = $2 AND y_mm = $3 AND z_mm = $4
          AND material = $5 AND print = $6 AND sla_type = $7
        ORDER BY 
          CASE 
            WHEN $8 BETWEEN qty_min AND qty_max THEN 0
            WHEN $8 < qty_min THEN qty_min - $8
            ELSE $8 - qty_max
          END
        LIMIT 1;
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                fallback_query, fefco, x_mm, y_mm, z_mm, material, print, sla_type, qty
            )
            
            if row:
                return LookupResult(
                    sku=row["sku"],
                    qty_band=QtyBand(min=row["qty_min"], max=row["qty_max"]),
                    lead_time=LeadTime(
                        std=row["lead_time_std"],
                        rush=row["lead_time_rush"],
                        strategic=row["lead_time_strg"]
                    ),
                    prices=Prices(
                        std=PriceInfo(
                            price_per_unit=float(row["price_std"]),
                            margin_pct=float(row["margin_std"])
                        ),
                        rush=PriceInfo(
                            price_per_unit=float(row["price_rush"]),
                            margin_pct=float(row["margin_rush"])
                        ),
                        strategic=PriceInfo(
                            price_per_unit=float(row["price_strg"]),
                            margin_pct=float(row["margin_strg"])
                        )
                    ),
                    terms=row["terms"] or []
                )
        
        return None
    
    async def health_check(self) -> bool:
        """Check if PostgreSQL is accessible."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()