"""Cash flow tracking module.

This module handles tracking of cash flows including deposits, withdrawals,
and dividends from transactions.
"""

from typing import List, Dict, Optional, Any
from datetime import date
import logging

from ..database import Database
from ..models.queries import get_transactions_by_account

logger = logging.getLogger(__name__)


def get_cash_flows(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> List[Dict[str, Any]]:
    """Get all cash flows in date range.

    Includes DEPOSIT, WITHDRAW, and DIVIDEND transactions.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        List of cash flow dictionaries with keys:
        - date: Transaction date
        - type: Transaction type (DEPOSIT, WITHDRAW, DIVIDEND)
        - amount: Cash flow amount (positive for inflow, negative for outflow)
        - symbol: Symbol (for DIVIDEND) or None
        - notes: Transaction notes
    """
    if db is None:
        from ..database import Database

        db = Database()

    transactions = get_transactions_by_account(
        account_id, start_date=start_date, end_date=end_date, db=db
    )

    cash_flows: List[Dict[str, Any]] = []

    for transaction in transactions:
        if transaction.type not in {"DEPOSIT", "WITHDRAW", "DIVIDEND"}:
            continue

        amount = 0.0

        if transaction.type == "DEPOSIT":
            # Deposit: positive cash flow
            if transaction.qty is not None:
                amount = transaction.qty
            elif transaction.price is not None:
                amount = transaction.price
            else:
                logger.warning(f"DEPOSIT transaction {transaction.id} has no amount")
                continue

        elif transaction.type == "WITHDRAW":
            # Withdrawal: negative cash flow
            if transaction.qty is not None:
                amount = -transaction.qty
            elif transaction.price is not None:
                amount = -transaction.price
            else:
                logger.warning(f"WITHDRAW transaction {transaction.id} has no amount")
                continue

        elif transaction.type == "DIVIDEND":
            # Dividend: positive cash flow
            if transaction.qty is not None and transaction.price is not None:
                # qty * price = total dividend amount
                amount = transaction.qty * transaction.price
            elif transaction.qty is not None:
                amount = transaction.qty
            elif transaction.price is not None:
                amount = transaction.price
            else:
                logger.warning(f"DIVIDEND transaction {transaction.id} has no amount")
                continue

        cash_flows.append(
            {
                "date": transaction.date,
                "type": transaction.type,
                "amount": amount,
                "symbol": transaction.symbol,
                "notes": transaction.notes,
                "transaction_id": transaction.id,
            }
        )

    # Sort by date
    cash_flows.sort(key=lambda x: x["date"])

    return cash_flows


def calculate_net_cash_flow(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> float:
    """Calculate net cash flow.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Net cash flow (positive = inflow, negative = outflow).
    """
    cash_flows = get_cash_flows(account_id, start_date, end_date, db)
    return sum(cf["amount"] for cf in cash_flows)


def get_cash_balance(
    account_id: int,
    balance_date: date,
    db: Optional[Database] = None,
) -> float:
    """Get cash balance at date.

    Calculates cumulative cash flow from all transactions up to and including
    the specified date.

    Args:
        account_id: Account ID.
        balance_date: Date to calculate balance.
        db: Database instance. If None, creates a new instance.

    Returns:
        Cash balance (cumulative cash flows).
    """
    if db is None:
        from ..database import Database

        db = Database()

    # Get all cash flows up to and including the date
    # Use a very early start date to get all transactions
    from datetime import date as date_class

    earliest_date = date_class(1900, 1, 1)
    cash_flows = get_cash_flows(account_id, earliest_date, balance_date, db)

    # Also need to account for cash from SELL transactions
    transactions = get_transactions_by_account(
        account_id, end_date=balance_date, db=db
    )

    cash_balance = 0.0

    # Add cash flows from DEPOSIT, WITHDRAW, DIVIDEND
    for cf in cash_flows:
        cash_balance += cf["amount"]

    # Add cash from SELL transactions (proceeds minus fees)
    for transaction in transactions:
        if transaction.type == "SELL":
            if transaction.qty is not None and transaction.price is not None:
                proceeds = transaction.qty * transaction.price
                fee = transaction.fee or 0.0
                cash_balance += proceeds - fee

    # Subtract cash from BUY transactions (cost plus fees)
    for transaction in transactions:
        if transaction.type == "BUY":
            if transaction.qty is not None and transaction.price is not None:
                cost = transaction.qty * transaction.price
                fee = transaction.fee or 0.0
                cash_balance -= cost + fee

    return cash_balance

