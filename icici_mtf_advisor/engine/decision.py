from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from icici_mtf_advisor.domain.normalizer import PositionRecord


@dataclass
class CostBreakdown:
    mtf_interest_cost: float
    fd_opportunity_cost: float
    inflation_cost: float
    benchmark_cost: float
    transaction_cost_to_exit: float
    required_hurdle_cost: float
    expected_profit: float
    net_edge: float
    expected_return_pct_used: float


def compute_mtf_interest(funded_amount: float, days_held: int, annual_rate: float) -> float:
    if funded_amount <= 0 or days_held <= 0 or annual_rate <= 0:
        return 0.0
    daily_rate = annual_rate / 365.0
    return funded_amount * daily_rate * days_held


def compute_annual_hurdle(base_amount: float, annual_rate: float, days: int = 365) -> float:
    if base_amount <= 0 or annual_rate <= 0 or days <= 0:
        return 0.0
    return base_amount * annual_rate * (days / 365.0)


def estimate_exit_transaction_cost(market_value: float, brokerage_per_order: float, tax_and_fees_buffer_rate: float) -> float:
    percent_cost = market_value * max(tax_and_fees_buffer_rate, 0.0)
    return max(brokerage_per_order, 0.0) + percent_cost


def choose_benchmark_cost(fd_cost: float, inflation_cost: float, benchmark_mode: str) -> float:
    mode = (benchmark_mode or "").lower()
    if mode == "fd_only":
        return fd_cost
    if mode == "inflation_only":
        return inflation_cost
    return max(fd_cost, inflation_cost)


def evaluate_position(
    position: PositionRecord,
    finance_cfg: Dict,
    decision_cfg: Dict,
) -> Dict:
    annual_mtf_rate = float(finance_cfg["mtf_interest_rate_annual"])
    fd_rate = float(finance_cfg["fd_rate_annual"])
    inflation_rate = float(finance_cfg["inflation_rate_annual"])
    brokerage_per_order = float(finance_cfg.get("brokerage_per_order", 0.0))
    tax_and_fees_buffer_rate = float(finance_cfg.get("tax_and_fees_buffer_rate", 0.0))

    benchmark_mode = str(decision_cfg.get("benchmark_mode", "max_fd_or_inflation"))
    default_expected_return_pct_annual = float(decision_cfg.get("default_expected_return_pct_annual", 0.0))
    min_sell_edge_pct = float(decision_cfg.get("min_sell_edge_pct", 0.0))

    mtf_interest_cost = compute_mtf_interest(
        funded_amount=position.funded_amount,
        days_held=position.days_held,
        annual_rate=annual_mtf_rate,
    )

    fd_opportunity_cost = compute_annual_hurdle(
        base_amount=position.market_value,
        annual_rate=fd_rate,
        days=365,
    )
    inflation_cost = compute_annual_hurdle(
        base_amount=position.market_value,
        annual_rate=inflation_rate,
        days=365,
    )
    benchmark_cost = choose_benchmark_cost(
        fd_cost=fd_opportunity_cost,
        inflation_cost=inflation_cost,
        benchmark_mode=benchmark_mode,
    )

    transaction_cost_to_exit = estimate_exit_transaction_cost(
        market_value=position.market_value,
        brokerage_per_order=brokerage_per_order,
        tax_and_fees_buffer_rate=tax_and_fees_buffer_rate,
    )

    expected_profit = position.market_value * default_expected_return_pct_annual
    required_hurdle_cost = mtf_interest_cost + benchmark_cost
    net_edge = expected_profit - required_hurdle_cost

    # conservative rule:
    # sell if the expected edge does not clear exit costs plus a no-trade band
    sell_threshold = transaction_cost_to_exit + (position.market_value * min_sell_edge_pct)
    recommendation = "HOLD" if net_edge > sell_threshold else "SELL"

    costs = CostBreakdown(
        mtf_interest_cost=round(mtf_interest_cost, 2),
        fd_opportunity_cost=round(fd_opportunity_cost, 2),
        inflation_cost=round(inflation_cost, 2),
        benchmark_cost=round(benchmark_cost, 2),
        transaction_cost_to_exit=round(transaction_cost_to_exit, 2),
        required_hurdle_cost=round(required_hurdle_cost, 2),
        expected_profit=round(expected_profit, 2),
        net_edge=round(net_edge, 2),
        expected_return_pct_used=default_expected_return_pct_annual,
    )

    return {
        **position.to_dict(),
        **costs.__dict__,
        "recommendation": recommendation,
    }
