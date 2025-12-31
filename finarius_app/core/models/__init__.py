"""Models module for Finarius portfolio tracking application.

This module provides ORM-like model classes for accounts, transactions, and prices,
along with query helper functions.
"""

from .account import Account
from .transaction import Transaction
from .price import Price
from .queries import (
    get_account_by_id,
    get_account_by_name,
    get_all_accounts,
    get_transaction_by_id,
    get_transactions_by_account,
    get_transactions_by_symbol,
    get_price,
    get_prices,
    get_latest_price,
)

__all__ = [
    # Models
    "Account",
    "Transaction",
    "Price",
    # Query helpers
    "get_account_by_id",
    "get_account_by_name",
    "get_all_accounts",
    "get_transaction_by_id",
    "get_transactions_by_account",
    "get_transactions_by_symbol",
    "get_price",
    "get_prices",
    "get_latest_price",
]

