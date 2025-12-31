"""Realized gains/losses calculation module.

This module handles calculation of realized gains and losses from SELL transactions,
tracking cost basis and calculating PnL per sale.
"""

from typing import Dict, Optional, List
from datetime import date
import logging

from ..database import Database
from ..models.queries import get_transactions_by_account
from ..engine.positions import get_positions

logger = logging.getLogger(__name__)


def calculate_realized_gains(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> float:
    """Calculate realized gains/losses for account in date range.

    Calculates total realized PnL from SELL transactions by tracking
    the cost basis of sold positions and comparing to sale proceeds.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Total realized gains (positive) or losses (negative).
    """
    if db is None:
        from ..database import Database

        db = Database()

    # Get all SELL transactions in date range
    transactions = get_transactions_by_account(
        account_id, start_date=start_date, end_date=end_date, db=db
    )

    total_realized = 0.0

    for transaction in transactions:
        if transaction.type != "SELL":
            continue

        if not transaction.symbol or transaction.qty is None or transaction.price is None:
            continue

        symbol = transaction.symbol.upper()
        sell_qty = transaction.qty
        sell_price = transaction.price
        sell_fee = transaction.fee or 0.0

        # Get positions just before this sale to get cost basis
        # Use transaction date minus 1 day to get position before sale
        from datetime import timedelta

        position_date = transaction.date - timedelta(days=1)
        positions = get_positions(account_id, position_date, db)

        if symbol not in positions:
            logger.warning(
                f"No position found for {symbol} before SELL on {transaction.date}"
            )
            continue

        position = positions[symbol]
        avg_cost = position["avg_price"]

        # Calculate cost basis for sold shares
        cost_basis = sell_qty * avg_cost

        # Calculate proceeds (sale price * qty - fees)
        proceeds = (sell_qty * sell_price) - sell_fee

        # Realized gain/loss = proceeds - cost basis
        realized = proceeds - cost_basis
        total_realized += realized

    return total_realized


def get_realized_gains_by_symbol(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[str, float]:
    """Get realized gains/losses broken down by symbol.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping symbol -> realized gain/loss.
    """
    if db is None:
        from ..database import Database

        db = Database()

    transactions = get_transactions_by_account(
        account_id, start_date=start_date, end_date=end_date, db=db
    )

    gains_by_symbol: Dict[str, float] = {}

    for transaction in transactions:
        if transaction.type != "SELL":
            continue

        if not transaction.symbol or transaction.qty is None or transaction.price is None:
            continue

        symbol = transaction.symbol.upper()

        if symbol not in gains_by_symbol:
            gains_by_symbol[symbol] = 0.0

        sell_qty = transaction.qty
        sell_price = transaction.price
        sell_fee = transaction.fee or 0.0

        from datetime import timedelta

        position_date = transaction.date - timedelta(days=1)
        positions = get_positions(account_id, position_date, db)

        if symbol in positions:
            position = positions[symbol]
            avg_cost = position["avg_price"]
            cost_basis = sell_qty * avg_cost
            proceeds = (sell_qty * sell_price) - sell_fee
            realized = proceeds - cost_basis
            gains_by_symbol[symbol] += realized

    return gains_by_symbol


def get_realized_gains_history(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[date, float]:
    """Get realized gains history over time.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> cumulative realized gains up to that date.
    """
    if db is None:
        from ..database import Database

        db = Database()

    from datetime import timedelta

    history: Dict[date, float] = {}
    cumulative = 0.0
    current_date = start_date

    while current_date <= end_date:
        # Calculate realized gains up to this date
        gains = calculate_realized_gains(account_id, start_date, current_date, db)
        history[current_date] = gains
        current_date += timedelta(days=1)

    return history

