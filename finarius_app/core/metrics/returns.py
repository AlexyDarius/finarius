"""Return calculation module.

This module handles calculation of various return metrics including
total return, CAGR, IRR, and TWRR.
"""

from typing import Dict, Optional, List
from datetime import date, timedelta
import logging
import math

from ..database import Database
from ..prices.downloader import PriceDownloader
from ..engine.portfolio_value import calculate_portfolio_value
from ..engine.cash_flows import get_cash_flows
from .realized_gains import calculate_realized_gains
from .unrealized_gains import calculate_unrealized_gains

logger = logging.getLogger(__name__)


def calculate_total_return(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate total return (realized + unrealized gains + dividends).

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Total return amount.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Realized gains
    realized = calculate_realized_gains(account_id, start_date, end_date, db)

    # Unrealized gains at end date
    unrealized = calculate_unrealized_gains(
        account_id, end_date, db, price_downloader
    )

    # Dividends in period
    cash_flows = get_cash_flows(account_id, start_date, end_date, db)
    dividends = sum(
        cf["amount"] for cf in cash_flows if cf["type"] == "DIVIDEND"
    )

    return realized + unrealized + dividends


def calculate_total_return_percentage(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate total return as percentage.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Total return percentage (e.g., 0.15 for 15%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Get portfolio value at start
    start_value = calculate_portfolio_value(
        account_id, start_date, db, price_downloader
    )

    if start_value == 0:
        return 0.0

    # Get total return
    total_return = calculate_total_return(
        account_id, start_date, end_date, db, price_downloader
    )

    return total_return / start_value


def calculate_cagr(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate CAGR (Compound Annual Growth Rate).

    Formula: (End Value / Start Value)^(1/years) - 1

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        CAGR as decimal (e.g., 0.10 for 10%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    start_value = calculate_portfolio_value(
        account_id, start_date, db, price_downloader
    )
    end_value = calculate_portfolio_value(
        account_id, end_date, db, price_downloader
    )

    if start_value <= 0:
        return 0.0

    # Calculate years
    days = (end_date - start_date).days
    if days <= 0:
        return 0.0

    years = days / 365.25

    if years <= 0:
        return 0.0

    # Calculate CAGR
    if end_value <= 0:
        # Negative return case
        return -1.0

    ratio = end_value / start_value
    cagr = (ratio ** (1.0 / years)) - 1.0

    return cagr


def get_cagr_history(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[date, float]:
    """Get CAGR history over time.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> CAGR from start_date to that date.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    history: Dict[date, float] = {}
    current_date = start_date

    while current_date <= end_date:
        cagr = calculate_cagr(
            account_id, start_date, current_date, db, price_downloader
        )
        history[current_date] = cagr
        current_date += timedelta(days=1)

    return history


def calculate_irr(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
    guess: float = 0.1,
) -> Optional[float]:
    """Calculate IRR (Internal Rate of Return) using Newton-Raphson method.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.
        guess: Initial guess for IRR (default: 0.1 = 10%).

    Returns:
        IRR as decimal (e.g., 0.10 for 10%), or None if calculation fails.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Get cash flows
    cash_flows = get_cash_flows(account_id, start_date, end_date, db)

    # Get portfolio value at end date
    end_value = calculate_portfolio_value(
        account_id, end_date, db, price_downloader
    )

    # Build cash flow list: negative for outflows (deposits), positive for inflows
    # Include final portfolio value as positive cash flow
    flows: List[float] = []
    dates: List[date] = []

    for cf in cash_flows:
        if cf["type"] == "DEPOSIT":
            flows.append(-cf["amount"])  # Outflow
        elif cf["type"] == "WITHDRAW":
            flows.append(cf["amount"])  # Inflow
        elif cf["type"] == "DIVIDEND":
            flows.append(cf["amount"])  # Inflow
        dates.append(cf["date"])

    # Add initial portfolio value (if any) as negative
    start_value = calculate_portfolio_value(
        account_id, start_date, db, price_downloader
    )
    if start_value > 0:
        flows.insert(0, -start_value)
        dates.insert(0, start_date)

    # Add final portfolio value as positive
    if end_value > 0:
        flows.append(end_value)
        dates.append(end_date)

    if len(flows) < 2:
        return None

    # Calculate IRR using Newton-Raphson method
    def npv(rate: float) -> float:
        """Calculate Net Present Value at given rate."""
        total = 0.0
        for i, (flow, flow_date) in enumerate(zip(flows, dates)):
            days = (flow_date - dates[0]).days
            years = days / 365.25
            total += flow / ((1.0 + rate) ** years)
        return total

    def npv_derivative(rate: float) -> float:
        """Calculate derivative of NPV at given rate."""
        total = 0.0
        for i, (flow, flow_date) in enumerate(zip(flows, dates)):
            days = (flow_date - dates[0]).days
            years = days / 365.25
            total -= (years * flow) / ((1.0 + rate) ** (years + 1))
        return total

    # Newton-Raphson iteration
    rate = guess
    max_iterations = 100
    tolerance = 1e-6

    for _ in range(max_iterations):
        npv_val = npv(rate)
        if abs(npv_val) < tolerance:
            return rate

        derivative = npv_derivative(rate)
        if abs(derivative) < tolerance:
            break

        rate = rate - npv_val / derivative

        # Prevent negative rates that are too extreme
        if rate < -0.99:
            rate = -0.99

    return None


def get_irr_history(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[date, Optional[float]]:
    """Get IRR history over time.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> IRR from start_date to that date.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    history: Dict[date, Optional[float]] = {}
    current_date = start_date

    while current_date <= end_date:
        irr = calculate_irr(
            account_id, start_date, current_date, db, price_downloader
        )
        history[current_date] = irr
        current_date += timedelta(days=1)

    return history


def calculate_twrr(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate TWRR (Time-Weighted Rate of Return).

    TWRR eliminates the effect of cash flows by calculating period returns
    and chaining them together.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        TWRR as decimal (e.g., 0.10 for 10%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Get cash flows to identify periods
    cash_flows = get_cash_flows(account_id, start_date, end_date, db)

    # Get all dates with cash flows
    cf_dates = sorted(set(cf["date"] for cf in cash_flows))
    cf_dates.append(end_date)

    # Calculate period returns
    period_returns: List[float] = []
    prev_date = start_date
    prev_value = calculate_portfolio_value(
        account_id, prev_date, db, price_downloader
    )

    for cf_date in cf_dates:
        if cf_date <= prev_date:
            continue

        # Get value at end of period (before cash flow)
        period_end_value = calculate_portfolio_value(
            account_id, cf_date, db, price_downloader
        )

        if prev_value > 0:
            period_return = (period_end_value - prev_value) / prev_value
            period_returns.append(period_return)

        prev_date = cf_date
        prev_value = period_end_value

    if not period_returns:
        return 0.0

    # Chain period returns: (1 + r1) * (1 + r2) * ... - 1
    twrr = 1.0
    for pr in period_returns:
        twrr *= (1.0 + pr)

    return twrr - 1.0


def get_twrr_history(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[date, float]:
    """Get TWRR history over time.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> TWRR from start_date to that date.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    history: Dict[date, float] = {}
    current_date = start_date

    while current_date <= end_date:
        twrr = calculate_twrr(
            account_id, start_date, current_date, db, price_downloader
        )
        history[current_date] = twrr
        current_date += timedelta(days=1)

    return history

