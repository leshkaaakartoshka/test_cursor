"""Base lookup provider interface."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.schemas import LookupResult


class LookupProvider(ABC):
    """Abstract base class for lookup providers."""
    
    @abstractmethod
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
        """
        Look up price information for given parameters.
        
        Args:
            fefco: FEFCO code
            x_mm: Width in mm
            y_mm: Length in mm
            z_mm: Height in mm
            material: Material type
            print: Print type
            sla_type: SLA type
            qty: Quantity
            
        Returns:
            LookupResult if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the lookup provider is healthy."""
        pass