"""Hash utilities for price validation."""

import hashlib
from typing import Dict, Any

from app.core.config import Settings


def compute_price_hash(
    prices: Dict[str, Any],
    qty: int,
    qty_band: Dict[str, int],
    lead_time: Dict[str, str],
    salt: str = ""
) -> str:
    """
    Compute MD5 hash for price validation.
    
    Args:
        prices: Price information
        qty: Quantity
        qty_band: Quantity band
        lead_time: Lead time information
        salt: Optional salt for additional security
        
    Returns:
        MD5 hash string
    """
    # Create a deterministic string representation
    data = {
        "prices": prices,
        "qty": qty,
        "qty_band": qty_band,
        "lead_time": lead_time,
        "salt": salt
    }
    
    # Convert to JSON string (sorted keys for consistency)
    import json
    data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    
    # Compute MD5 hash
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()


def generate_lead_id() -> str:
    """Generate a unique lead ID."""
    import uuid
    import time
    
    # Use timestamp and UUID for uniqueness
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"web-{timestamp}-{unique_id}"