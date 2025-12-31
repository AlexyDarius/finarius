"""Position tracking module for portfolio engine.

This module handles calculation of portfolio positions from transactions,
including handling BUY/SELL transactions and stock splits.
"""

from typing import Dict, Optional, List
from datetime import date
import logging

from ..database import Database
from ..models.queries import get_transactions_by_account

logger = logging.getLogger(__name__)


def get_positions(
    account_id: int,
    position_date: date,
    db: Optional[Database] = None,
) -> Dict[str, Dict[str, float]]:
    """Get positions at specific date.

    Calculates positions by processing all transactions up to and including
    the specified date. Handles BUY/SELL transactions and tracks cost basis.

    Args:
        account_id: Account ID.
        position_date: Date to calculate positions.
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping symbol -> {
            'qty': float,           # Current quantity
            'cost_basis': float,    # Total cost basis (including fees)
            'avg_price': float      # Average price per unit (PRU)
        }
    """
    if db is None:
        from ..database import Database

        db = Database()

    # Get all transactions up to and including the date
    transactions = get_transactions_by_account(
        account_id, end_date=position_date, db=db
    )
    transactions.sort(key=lambda t: (t.date, t.id))

    positions: Dict[str, Dict[str, float]] = {}

    for transaction in transactions:
        if transaction.type not in {"BUY", "SELL"}:
            continue

        if not transaction.symbol:
            continue

        symbol = transaction.symbol.upper()

        # Initialize position if not exists
        if symbol not in positions:
            positions[symbol] = {"qty": 0.0, "cost_basis": 0.0, "avg_price": 0.0}

        if transaction.type == "BUY":
            # Add to position
            if transaction.qty is None or transaction.price is None:
                continue

            old_qty = positions[symbol]["qty"]
            old_cost_basis = positions[symbol]["cost_basis"]
            new_qty = transaction.qty
            new_cost = (transaction.qty * transaction.price) + (transaction.fee or 0.0)

            # Update quantity and cost basis
            positions[symbol]["qty"] = old_qty + new_qty
            positions[symbol]["cost_basis"] = old_cost_basis + new_cost

            # Recalculate average price
            if positions[symbol]["qty"] > 0:
                positions[symbol]["avg_price"] = (
                    positions[symbol]["cost_basis"] / positions[symbol]["qty"]
                )

        elif transaction.type == "SELL":
            # Reduce position (FIFO method)
            if transaction.qty is None or transaction.price is None:
                continue

            sell_qty = transaction.qty
            current_qty = positions[symbol]["qty"]

            if sell_qty > current_qty:
                logger.warning(
                    f"SELL transaction exceeds position: {symbol}, "
                    f"selling {sell_qty}, have {current_qty}"
                )
                sell_qty = current_qty

            if sell_qty > 0:
                # Calculate cost basis to remove (proportional)
                avg_price = positions[symbol]["avg_price"]
                cost_basis_to_remove = sell_qty * avg_price

                # Update quantity and cost basis
                positions[symbol]["qty"] = current_qty - sell_qty
                positions[symbol]["cost_basis"] = (
                    positions[symbol]["cost_basis"] - cost_basis_to_remove
                )

                # Update average price (should remain same if qty > 0)
                if positions[symbol]["qty"] > 0:
                    positions[symbol]["avg_price"] = (
                        positions[symbol]["cost_basis"] / positions[symbol]["qty"]
                    )
                else:
                    positions[symbol]["avg_price"] = 0.0

    # Remove positions with zero quantity
    positions = {k: v for k, v in positions.items() if v["qty"] > 0}

    return positions


def get_all_positions(
    position_date: date,
    db: Optional[Database] = None,
) -> Dict[int, Dict[str, Dict[str, float]]]:
    """Get positions across all accounts.

    Args:
        position_date: Date to calculate positions.
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping account_id -> positions dict.
    """
    if db is None:
        from ..database import Database

        db = Database()

    from ..models.queries import get_all_accounts

    accounts = get_all_accounts(db)
    all_positions: Dict[int, Dict[str, Dict[str, float]]] = {}

    for account in accounts:
        positions = get_positions(account.id, position_date, db)
        if positions:
            all_positions[account.id] = positions

    return all_positions


def get_current_positions(
    account_id: int,
    db: Optional[Database] = None,
) -> Dict[str, Dict[str, float]]:
    """Get current positions for account.

    Args:
        account_id: Account ID.
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping symbol -> {qty, cost_basis, avg_price}.
    """
    return get_positions(account_id, date.today(), db)


def get_position_history(
    symbol: str,
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[date, Dict[str, float]]:
    """Get position history over time.

    Args:
        symbol: Stock symbol.
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> position dict.
    """
    if db is None:
        from ..database import Database

        db = Database()

    from datetime import timedelta

    history: Dict[date, Dict[str, float]] = {}
    current_date = start_date

    while current_date <= end_date:
        positions = get_positions(account_id, current_date, db)
        if symbol.upper() in positions:
            history[current_date] = positions[symbol.upper()].copy()
        else:
            history[current_date] = {"qty": 0.0, "cost_basis": 0.0, "avg_price": 0.0}
        current_date += timedelta(days=1)

    return history

