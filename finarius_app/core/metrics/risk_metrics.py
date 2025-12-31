"""Risk metrics calculation module.

This module handles calculation of risk-related metrics including
Sharpe ratio, maximum drawdown, volatility, and beta.
"""

from typing import Dict, Optional, List
from datetime import date, timedelta
import logging
import math

from ..database import Database
from ..prices.downloader import PriceDownloader
from ..engine.portfolio_value import calculate_portfolio_value_over_time
from ..models.queries import get_prices
from .returns import calculate_total_return_percentage

logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(
    account_id: int,
    start_date: date,
    end_date: date,
    risk_free_rate: float = 0.02,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Optional[float]:
    """Calculate Sharpe ratio.

    Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Volatility

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        risk_free_rate: Risk-free rate as decimal (default: 0.02 = 2%).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Sharpe ratio, or None if calculation fails.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    from ..metrics.returns import calculate_total_return_percentage

    # Calculate portfolio return
    portfolio_return = calculate_total_return_percentage(
        account_id, start_date, end_date, db, price_downloader
    )

    # Calculate portfolio volatility
    volatility = calculate_volatility(
        account_id, start_date, end_date, db, price_downloader
    )

    if volatility == 0:
        return None

    # Calculate excess return
    excess_return = portfolio_return - risk_free_rate

    # Annualize if needed
    days = (end_date - start_date).days
    if days > 0:
        years = days / 365.25
        if years > 0:
            excess_return = excess_return / years
            volatility = volatility * math.sqrt(365.25 / days) if days < 365 else volatility

    return excess_return / volatility


def calculate_max_drawdown(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate maximum drawdown.

    Maximum drawdown is the largest peak-to-trough decline in portfolio value.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Maximum drawdown as decimal (e.g., 0.20 for 20%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Get portfolio values over time
    values = calculate_portfolio_value_over_time(
        account_id, start_date, end_date, "daily", db, price_downloader
    )

    if len(values) < 2:
        return 0.0

    # Calculate drawdowns
    sorted_dates = sorted(values.keys())
    peak = values[sorted_dates[0]]
    max_drawdown = 0.0

    for d in sorted_dates:
        value = values[d]
        if value > peak:
            peak = value
        else:
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    return max_drawdown


def calculate_volatility(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate portfolio volatility (standard deviation of returns).

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Volatility as decimal (e.g., 0.15 for 15%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Get portfolio values over time
    values = calculate_portfolio_value_over_time(
        account_id, start_date, end_date, "daily", db, price_downloader
    )

    if len(values) < 2:
        return 0.0

    # Calculate daily returns
    sorted_dates = sorted(values.keys())
    returns: List[float] = []

    for i in range(1, len(sorted_dates)):
        prev_value = values[sorted_dates[i - 1]]
        curr_value = values[sorted_dates[i]]

        if prev_value > 0:
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)

    if len(returns) < 2:
        return 0.0

    # Calculate standard deviation
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    volatility = math.sqrt(variance)

    # Annualize (assuming daily returns)
    volatility = volatility * math.sqrt(252)  # 252 trading days per year

    return volatility


def calculate_beta(
    account_id: int,
    benchmark_symbol: str,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Optional[float]:
    """Calculate beta vs benchmark.

    Beta measures portfolio sensitivity to benchmark movements.

    Args:
        account_id: Account ID.
        benchmark_symbol: Benchmark symbol (e.g., 'SPY' for S&P 500).
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Beta value, or None if calculation fails.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    # Get portfolio values over time
    portfolio_values = calculate_portfolio_value_over_time(
        account_id, start_date, end_date, "daily", db, price_downloader
    )

    # Get benchmark prices
    benchmark_prices = get_prices(benchmark_symbol, start_date, end_date, db)

    if len(benchmark_prices) < 2 or len(portfolio_values) < 2:
        return None

    # Build aligned price series
    portfolio_returns: List[float] = []
    benchmark_returns: List[float] = []

    sorted_portfolio_dates = sorted(portfolio_values.keys())
    benchmark_dict = {p.date: p.close for p in benchmark_prices}

    for i in range(1, len(sorted_portfolio_dates)):
        date_key = sorted_portfolio_dates[i]
        prev_date = sorted_portfolio_dates[i - 1]

        if date_key not in benchmark_dict or prev_date not in benchmark_dict:
            continue

        portfolio_prev = portfolio_values[prev_date]
        portfolio_curr = portfolio_values[date_key]
        benchmark_prev = benchmark_dict[prev_date]
        benchmark_curr = benchmark_dict[date_key]

        if portfolio_prev > 0 and benchmark_prev > 0:
            portfolio_ret = (portfolio_curr - portfolio_prev) / portfolio_prev
            benchmark_ret = (benchmark_curr - benchmark_prev) / benchmark_prev
            portfolio_returns.append(portfolio_ret)
            benchmark_returns.append(benchmark_ret)

    if len(portfolio_returns) < 2:
        return None

    # Calculate covariance and variance
    portfolio_mean = sum(portfolio_returns) / len(portfolio_returns)
    benchmark_mean = sum(benchmark_returns) / len(benchmark_returns)

    covariance = sum(
        (portfolio_returns[i] - portfolio_mean) * (benchmark_returns[i] - benchmark_mean)
        for i in range(len(portfolio_returns))
    ) / (len(portfolio_returns) - 1)

    benchmark_variance = sum(
        (r - benchmark_mean) ** 2 for r in benchmark_returns
    ) / (len(benchmark_returns) - 1)

    if benchmark_variance == 0:
        return None

    beta = covariance / benchmark_variance
    return beta

