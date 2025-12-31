"""Performance metrics module for Finarius.

This module provides the MetricsCalculator class and supporting functions for
calculating portfolio performance metrics including gains, returns, dividends, and risk.
"""

from .metrics import MetricsCalculator
from .realized_gains import (
    calculate_realized_gains,
    get_realized_gains_by_symbol,
    get_realized_gains_history,
)
from .unrealized_gains import (
    calculate_unrealized_gains,
    get_unrealized_gains_by_symbol,
    get_unrealized_gains_history,
)
from .returns import (
    calculate_total_return,
    calculate_total_return_percentage,
    calculate_cagr,
    get_cagr_history,
    calculate_irr,
    get_irr_history,
    calculate_twrr,
    get_twrr_history,
)
from .dividends import (
    get_dividend_history,
    calculate_dividend_yield,
    calculate_dividend_income,
    get_dividend_by_symbol,
    calculate_dividend_yield_by_symbol,
)
from .risk_metrics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_volatility,
    calculate_beta,
)

__all__ = [
    # Main class
    "MetricsCalculator",
    # Realized gains
    "calculate_realized_gains",
    "get_realized_gains_by_symbol",
    "get_realized_gains_history",
    # Unrealized gains
    "calculate_unrealized_gains",
    "get_unrealized_gains_by_symbol",
    "get_unrealized_gains_history",
    # Returns
    "calculate_total_return",
    "calculate_total_return_percentage",
    "calculate_cagr",
    "get_cagr_history",
    "calculate_irr",
    "get_irr_history",
    "calculate_twrr",
    "get_twrr_history",
    # Dividends
    "get_dividend_history",
    "calculate_dividend_yield",
    "calculate_dividend_income",
    "get_dividend_by_symbol",
    "calculate_dividend_yield_by_symbol",
    # Risk metrics
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_volatility",
    "calculate_beta",
]

