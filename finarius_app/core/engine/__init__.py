"""Portfolio reconstruction engine for Finarius.

This module provides the PortfolioEngine class and supporting functions for
portfolio calculations including positions, PRU, portfolio value, and cash flows.
"""

from .engine import PortfolioEngine
from .positions import (
    get_positions,
    get_all_positions,
    get_current_positions,
    get_position_history,
)
from .pru import calculate_pru, get_pru_history
from .portfolio_value import (
    calculate_portfolio_value,
    calculate_portfolio_value_over_time,
    get_portfolio_breakdown,
)
from .cash_flows import (
    get_cash_flows,
    calculate_net_cash_flow,
    get_cash_balance,
)

__all__ = [
    # Main class
    "PortfolioEngine",
    # Position tracking
    "get_positions",
    "get_all_positions",
    "get_current_positions",
    "get_position_history",
    # PRU calculation
    "calculate_pru",
    "get_pru_history",
    # Portfolio value
    "calculate_portfolio_value",
    "calculate_portfolio_value_over_time",
    "get_portfolio_breakdown",
    # Cash flows
    "get_cash_flows",
    "calculate_net_cash_flow",
    "get_cash_balance",
]
