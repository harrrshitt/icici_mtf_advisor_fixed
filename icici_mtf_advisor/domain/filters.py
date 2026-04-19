from __future__ import annotations

from typing import Any, Dict


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def is_mtf_position(pos: Dict[str, Any]) -> bool:
    """
    Heuristic because raw Breeze fields may vary by account/product payload.
    Adjust this after you inspect a real response from your account.
    """
    product_type = str(pos.get("product_type", "")).upper()
    margin = str(pos.get("margin", "")).upper()
    borrowed_qty = _safe_float(pos.get("borrowed_qty", 0))

    return (
        product_type == "MTF"
        or margin == "MTF"
        or borrowed_qty > 0
    )
