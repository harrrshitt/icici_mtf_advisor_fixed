from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None

    text = str(value).strip()
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%d-%b-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


@dataclass
class PositionRecord:
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    market_value: float
    funded_amount: float
    buy_date: Optional[date]
    days_held: int
    raw_position: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["buy_date"] = self.buy_date.isoformat() if self.buy_date else None
        return payload


def infer_buy_date_from_trades(symbol: str, trades: Iterable[Dict[str, Any]]) -> Optional[date]:
    candidates: List[date] = []

    for trade in trades:
        trade_symbol = str(trade.get("stock_code", trade.get("symbol", ""))).upper()
        if trade_symbol != symbol.upper():
            continue

        action = str(trade.get("action", trade.get("transaction_type", trade.get("buy_sell", "")))).upper()
        if "BUY" not in action:
            continue

        parsed = _parse_date(
            trade.get("trade_date")
            or trade.get("order_date")
            or trade.get("date")
            or trade.get("trade_datetime")
        )
        if parsed:
            candidates.append(parsed)

    if not candidates:
        return None
    return min(candidates)


def normalize_position(raw_position: Dict[str, Any], trades: Iterable[Dict[str, Any]], today: Optional[date] = None) -> PositionRecord:
    today = today or date.today()

    symbol = str(raw_position.get("stock_code", raw_position.get("symbol", ""))).upper()
    quantity = _safe_float(raw_position.get("quantity", raw_position.get("net_quantity", 0)))
    average_price = _safe_float(raw_position.get("average_price", raw_position.get("avg_price", 0)))
    current_price = _safe_float(raw_position.get("ltp", raw_position.get("current_price", average_price)))
    market_value = _safe_float(raw_position.get("market_value", current_price * quantity))
    funded_amount = _safe_float(raw_position.get("funded_amount", raw_position.get("funded_value", 0)))

    buy_date = infer_buy_date_from_trades(symbol=symbol, trades=trades)
    days_held = max((today - buy_date).days, 0) if buy_date else 0

    return PositionRecord(
        symbol=symbol,
        quantity=quantity,
        average_price=average_price,
        current_price=current_price,
        market_value=market_value,
        funded_amount=funded_amount,
        buy_date=buy_date,
        days_held=days_held,
        raw_position=raw_position,
    )
