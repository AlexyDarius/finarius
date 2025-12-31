"""MetricsCalculator class for portfolio performance metrics.

This module provides the MetricsCalculator class which orchestrates
all performance metric calculations.
"""

from typing import Optional, Dict, Any
from datetime import date
import logging

from ..database import Database
from ..prices.downloader import PriceDownloader
from ..engine.engine import PortfolioEngine

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

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Portfolio performance metrics calculator.

    This class provides a unified interface for calculating various
    performance metrics including gains, returns, dividends, and risk metrics.
    """

    def __init__(
        self,
        portfolio_engine: Optional[PortfolioEngine] = None,
        db: Optional[Database] = None,
        price_downloader: Optional[PriceDownloader] = None,
    ) -> None:
        """Initialize MetricsCalculator.

        Args:
            portfolio_engine: PortfolioEngine instance. If None, creates a new instance.
            db: Database instance. If None, creates a new instance.
            price_downloader: PriceDownloader instance. If None, creates a new instance.
        """
        if portfolio_engine is None:
            if db is None:
                db = Database()
            if price_downloader is None:
                price_downloader = PriceDownloader(db=db)
            self.portfolio_engine = PortfolioEngine(db=db, price_downloader=price_downloader)
        else:
            self.portfolio_engine = portfolio_engine

        self.db = self.portfolio_engine.db
        self.price_downloader = self.portfolio_engine.price_downloader
        self._cache: Dict[str, Any] = {}

    def clear_cache(self) -> None:
        """Clear the metrics cache."""
        self._cache.clear()
        logger.debug("Metrics calculator cache cleared")

    # Realized gains methods
    def calculate_realized_gains(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
    ) -> float:
        """Calculate realized gains/losses."""
        cache_key = f"realized_{account_id}_{start_date}_{end_date}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        gains = calculate_realized_gains(account_id, start_date, end_date, self.db)
        if use_cache:
            self._cache[cache_key] = gains
        return gains

    def get_realized_gains_by_symbol(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, float]:
        """Get realized gains broken down by symbol."""
        return get_realized_gains_by_symbol(account_id, start_date, end_date, self.db)

    def get_realized_gains_history(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, float]:
        """Get realized gains history over time."""
        return get_realized_gains_history(account_id, start_date, end_date, self.db)

    # Unrealized gains methods
    def calculate_unrealized_gains(
        self,
        account_id: int,
        gains_date: date,
        use_cache: bool = True,
    ) -> float:
        """Calculate unrealized gains/losses."""
        cache_key = f"unrealized_{account_id}_{gains_date}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        gains = calculate_unrealized_gains(
            account_id, gains_date, self.db, self.price_downloader
        )
        if use_cache:
            self._cache[cache_key] = gains
        return gains

    def get_unrealized_gains_by_symbol(
        self,
        account_id: int,
        gains_date: date,
    ) -> Dict[str, float]:
        """Get unrealized gains broken down by symbol."""
        return get_unrealized_gains_by_symbol(
            account_id, gains_date, self.db, self.price_downloader
        )

    def get_unrealized_gains_history(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, float]:
        """Get unrealized gains history over time."""
        return get_unrealized_gains_history(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    # Return methods
    def calculate_total_return(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
        use_cache: bool = True,
    ) -> float:
        """Calculate total return."""
        cache_key = f"total_return_{account_id}_{start_date}_{end_date}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        total = calculate_total_return(
            account_id, start_date, end_date, self.db, self.price_downloader
        )
        if use_cache:
            self._cache[cache_key] = total
        return total

    def calculate_total_return_percentage(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate total return as percentage."""
        return calculate_total_return_percentage(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def calculate_cagr(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate CAGR."""
        return calculate_cagr(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def get_cagr_history(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, float]:
        """Get CAGR history over time."""
        return get_cagr_history(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def calculate_irr(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Optional[float]:
        """Calculate IRR."""
        return calculate_irr(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def get_irr_history(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, Optional[float]]:
        """Get IRR history over time."""
        return get_irr_history(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def calculate_twrr(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate TWRR."""
        return calculate_twrr(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def get_twrr_history(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, float]:
        """Get TWRR history over time."""
        return get_twrr_history(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    # Dividend methods
    def get_dividend_history(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> list:
        """Get dividend history."""
        return get_dividend_history(account_id, start_date, end_date, self.db)

    def calculate_dividend_yield(
        self,
        account_id: int,
        yield_date: date,
    ) -> float:
        """Calculate dividend yield."""
        return calculate_dividend_yield(
            account_id, yield_date, self.db, self.price_downloader
        )

    def calculate_dividend_income(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate total dividend income."""
        return calculate_dividend_income(account_id, start_date, end_date, self.db)

    def get_dividend_by_symbol(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[str, float]:
        """Get dividend income by symbol."""
        return get_dividend_by_symbol(account_id, start_date, end_date, self.db)

    def calculate_dividend_yield_by_symbol(
        self,
        symbol: str,
        account_id: int,
        yield_date: date,
    ) -> float:
        """Calculate dividend yield for specific symbol."""
        return calculate_dividend_yield_by_symbol(
            symbol, account_id, yield_date, self.db, self.price_downloader
        )

    # Risk metrics methods
    def calculate_sharpe_ratio(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
        risk_free_rate: float = 0.02,
    ) -> Optional[float]:
        """Calculate Sharpe ratio."""
        return calculate_sharpe_ratio(
            account_id,
            start_date,
            end_date,
            risk_free_rate,
            self.db,
            self.price_downloader,
        )

    def calculate_max_drawdown(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate maximum drawdown."""
        return calculate_max_drawdown(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def calculate_volatility(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate portfolio volatility."""
        return calculate_volatility(
            account_id, start_date, end_date, self.db, self.price_downloader
        )

    def calculate_beta(
        self,
        account_id: int,
        benchmark_symbol: str,
        start_date: date,
        end_date: date,
    ) -> Optional[float]:
        """Calculate beta vs benchmark."""
        return calculate_beta(
            account_id,
            benchmark_symbol,
            start_date,
            end_date,
            self.db,
            self.price_downloader,
        )

