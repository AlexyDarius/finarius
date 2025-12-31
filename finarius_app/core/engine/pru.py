"""PRU (Prix de Revient Unitaire / Average Cost) calculation module.

This module handles calculation of average cost per unit using FIFO method,
handling multiple purchases, partial sales, and including fees in cost basis.
"""

from typing import Dict, Optional
from datetime import date
import logging

from ..database import Database
from .positions import get_positions

logger = logging.getLogger(__name__)


def calculate_pru(
    symbol: str,
    account_id: int,
    pru_date: date,
    db: Optional[Database] = None,
) -> float:
    """Calculate PRU (Average Cost) for symbol at date.

    Uses FIFO method to calculate average cost per unit, including fees
    in the cost basis. Returns 0.0 if no position exists.

    Args:
        symbol: Stock symbol.
        account_id: Account ID.
        pru_date: Date to calculate PRU.
        db: Database instance. If None, creates a new instance.

    Returns:
        PRU value (average cost per unit). Returns 0.0 if no position.
    """
    if db is None:
        from ..database import Database

        db = Database()

    positions = get_positions(account_id, pru_date, db)
    symbol_upper = symbol.upper()

    if symbol_upper not in positions:
        return 0.0

    position = positions[symbol_upper]
    return position["avg_price"]


def get_pru_history(
    symbol: str,
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[date, float]:
    """Get PRU history over time.

    Args:
        symbol: Stock symbol.
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> PRU value.
    """
    if db is None:
        from ..database import Database

        db = Database()

    from datetime import timedelta

    history: Dict[date, float] = {}
    current_date = start_date

    while current_date <= end_date:
        pru = calculate_pru(symbol, account_id, current_date, db)
        history[current_date] = pru
        current_date += timedelta(days=1)

    return history

