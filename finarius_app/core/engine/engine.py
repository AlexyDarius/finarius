"""PortfolioEngine class for portfolio reconstruction and calculations.

This module provides the PortfolioEngine class which orchestrates
portfolio calculations including positions, PRU, portfolio value, and cash flows.
"""

from typing import Optional, Dict, Any
from datetime import date
import logging

from ..database import Database
from ..prices.downloader import PriceDownloader

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

logger = logging.getLogger(__name__)


class PortfolioEngine:
    """Portfolio reconstruction and calculation engine.

    This class provides a unified interface for portfolio calculations,
    including position tracking, PRU calculation, portfolio valuation,
    and cash flow analysis.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        price_downloader: Optional[PriceDownloader] = None,
    ) -> None:
        """Initialize PortfolioEngine.

        Args:
            db: Database instance. If None, creates a new instance.
            price_downloader: PriceDownloader instance. If None, creates a new instance.
        """
        self.db = db or Database()
        self.price_downloader = price_downloader or PriceDownloader(db=self.db)
        self._cache: Dict[str, Any] = {}

    def clear_cache(self) -> None:
        """Clear the portfolio state cache."""
        self._cache.clear()
        logger.debug("Portfolio engine cache cleared")

    # Position tracking methods
    def get_positions(
        self,
        account_id: int,
        position_date: date,
        use_cache: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """Get positions at specific date.

        Args:
            account_id: Account ID.
            position_date: Date to calculate positions.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary mapping symbol -> {qty, cost_basis, avg_price}.
        """
        cache_key = f"positions_{account_id}_{position_date.isoformat()}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        positions = get_positions(account_id, position_date, self.db)
        if use_cache:
            self._cache[cache_key] = positions
        return positions

    def get_all_positions(
        self,
        position_date: date,
        use_cache: bool = True,
    ) -> Dict[int, Dict[str, Dict[str, float]]]:
        """Get positions across all accounts.

        Args:
            position_date: Date to calculate positions.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary mapping account_id -> positions dict.
        """
        cache_key = f"all_positions_{position_date.isoformat()}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        positions = get_all_positions(position_date, self.db)
        if use_cache:
            self._cache[cache_key] = positions
        return positions

    def get_current_positions(
        self,
        account_id: int,
        use_cache: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """Get current positions for account.

        Args:
            account_id: Account ID.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary mapping symbol -> {qty, cost_basis, avg_price}.
        """
        return self.get_positions(account_id, date.today(), use_cache=use_cache)

    def get_position_history(
        self,
        symbol: str,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, Dict[str, float]]:
        """Get position history over time.

        Args:
            symbol: Stock symbol.
            account_id: Account ID.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            Dictionary mapping date -> position dict.
        """
        return get_position_history(symbol, account_id, start_date, end_date, self.db)

    # PRU calculation methods
    def calculate_pru(
        self,
        symbol: str,
        account_id: int,
        pru_date: date,
        use_cache: bool = True,
    ) -> float:
        """Calculate PRU (Average Cost) for symbol at date.

        Args:
            symbol: Stock symbol.
            account_id: Account ID.
            pru_date: Date to calculate PRU.
            use_cache: Whether to use cached results.

        Returns:
            PRU value (average cost per unit).
        """
        cache_key = f"pru_{symbol}_{account_id}_{pru_date.isoformat()}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        pru = calculate_pru(symbol, account_id, pru_date, self.db)
        if use_cache:
            self._cache[cache_key] = pru
        return pru

    def get_pru_history(
        self,
        symbol: str,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> Dict[date, float]:
        """Get PRU history over time.

        Args:
            symbol: Stock symbol.
            account_id: Account ID.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            Dictionary mapping date -> PRU value.
        """
        return get_pru_history(symbol, account_id, start_date, end_date, self.db)

    # Portfolio value methods
    def calculate_portfolio_value(
        self,
        account_id: int,
        value_date: date,
        use_cache: bool = True,
    ) -> float:
        """Calculate portfolio value at date.

        Args:
            account_id: Account ID.
            value_date: Date to calculate value.
            use_cache: Whether to use cached results.

        Returns:
            Total portfolio value.
        """
        cache_key = f"portfolio_value_{account_id}_{value_date.isoformat()}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        value = calculate_portfolio_value(
            account_id, value_date, self.db, self.price_downloader
        )
        if use_cache:
            self._cache[cache_key] = value
        return value

    def calculate_portfolio_value_over_time(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
        frequency: str = "daily",
    ) -> Dict[date, float]:
        """Calculate portfolio value over time.

        Args:
            account_id: Account ID.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            frequency: Frequency of snapshots ('daily', 'weekly', 'monthly').

        Returns:
            Dictionary mapping date -> portfolio value.
        """
        return calculate_portfolio_value_over_time(
            account_id,
            start_date,
            end_date,
            frequency,
            self.db,
            self.price_downloader,
        )

    def get_portfolio_breakdown(
        self,
        account_id: int,
        breakdown_date: date,
        use_cache: bool = True,
    ) -> Dict[str, Dict[str, float]]:
        """Get portfolio breakdown by symbol.

        Args:
            account_id: Account ID.
            breakdown_date: Date for breakdown.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary mapping symbol -> {qty, cost_basis, current_value, unrealized_gain}.
        """
        cache_key = f"breakdown_{account_id}_{breakdown_date.isoformat()}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        breakdown = get_portfolio_breakdown(
            account_id, breakdown_date, self.db, self.price_downloader
        )
        if use_cache:
            self._cache[cache_key] = breakdown
        return breakdown

    # Cash flow methods
    def get_cash_flows(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> list:
        """Get all cash flows in date range.

        Args:
            account_id: Account ID.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            List of cash flow dictionaries.
        """
        return get_cash_flows(account_id, start_date, end_date, self.db)

    def calculate_net_cash_flow(
        self,
        account_id: int,
        start_date: date,
        end_date: date,
    ) -> float:
        """Calculate net cash flow.

        Args:
            account_id: Account ID.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            Net cash flow (positive = inflow, negative = outflow).
        """
        return calculate_net_cash_flow(account_id, start_date, end_date, self.db)

    def get_cash_balance(
        self,
        account_id: int,
        balance_date: date,
    ) -> float:
        """Get cash balance at date.

        Args:
            account_id: Account ID.
            balance_date: Date to calculate balance.

        Returns:
            Cash balance.
        """
        return get_cash_balance(account_id, balance_date, self.db)

