"""Transaction model for Finarius portfolio tracking application."""

from typing import Optional, Dict, Any
from datetime import date
import logging

from ..database import Database
from .account import Account

logger = logging.getLogger(__name__)


class Transaction:
    """Transaction model representing a portfolio transaction."""

    TRANSACTION_TYPES = {"BUY", "SELL", "DIVIDEND", "DEPOSIT", "WITHDRAW"}

    def __init__(
        self,
        date: date,
        account_id: int,
        transaction_type: str,
        symbol: Optional[str] = None,
        qty: Optional[float] = None,
        price: Optional[float] = None,
        fee: float = 0.0,
        notes: Optional[str] = None,
        transaction_id: Optional[int] = None,
        created_at: Optional[str] = None,
    ) -> None:
        """Initialize Transaction instance.

        Args:
            date: Transaction date.
            account_id: Account ID.
            transaction_type: Transaction type (BUY, SELL, DIVIDEND, DEPOSIT, WITHDRAW).
            symbol: Symbol (required for BUY, SELL, DIVIDEND).
            qty: Quantity (required for BUY, SELL).
            price: Price per unit (required for BUY, SELL).
            fee: Transaction fee (default: 0.0).
            notes: Optional notes.
            transaction_id: Transaction ID (for existing transactions).
            created_at: Creation timestamp.
        """
        self.id = transaction_id
        # Handle both date objects and date strings
        if isinstance(date, str):
            self.date = date.fromisoformat(date)
        else:
            self.date = date
        self.account_id = account_id
        self.type = transaction_type.upper()
        self.symbol = symbol
        self.qty = qty
        self.price = price
        self.fee = fee
        self.notes = notes
        self.created_at = created_at

    def validate(self) -> None:
        """Validate transaction data.

        Raises:
            ValueError: If validation fails.
        """
        if self.type not in self.TRANSACTION_TYPES:
            raise ValueError(
                f"Invalid transaction type: {self.type}. "
                f"Must be one of: {', '.join(self.TRANSACTION_TYPES)}"
            )

        if self.type in {"BUY", "SELL"}:
            if not self.symbol:
                raise ValueError(f"Symbol is required for {self.type} transactions")
            if self.qty is None or self.qty <= 0:
                raise ValueError(f"Quantity must be positive for {self.type} transactions")
            if self.price is None or self.price < 0:
                raise ValueError(f"Price must be non-negative for {self.type} transactions")

        if self.type == "DIVIDEND":
            if not self.symbol:
                raise ValueError("Symbol is required for DIVIDEND transactions")
            if self.qty is None or self.qty <= 0:
                raise ValueError("Quantity must be positive for DIVIDEND transactions")

        if self.fee < 0:
            raise ValueError("Fee cannot be negative")

    def save(self, db: Optional[Database] = None) -> "Transaction":
        """Save transaction to database.

        Args:
            db: Database instance. If None, creates a new instance.

        Returns:
            Self with updated ID and timestamp.

        Raises:
            ValueError: If validation fails.
            sqlite3.IntegrityError: If account_id doesn't exist.
        """
        if db is None:
            db = Database()

        self.validate()

        if self.id is None:
            # Insert new transaction
            db.execute(
                """
                INSERT INTO transactions (date, account_id, type, symbol, qty, price, fee, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.date.isoformat(),
                    self.account_id,
                    self.type,
                    self.symbol,
                    self.qty,
                    self.price,
                    self.fee,
                    self.notes,
                ),
            )
            # Get the inserted ID
            result = db.fetchone(
                """
                SELECT id, created_at FROM transactions
                WHERE date = ? AND account_id = ? AND type = ?
                ORDER BY id DESC LIMIT 1
                """,
                (self.date.isoformat(), self.account_id, self.type),
            )
            if result:
                self.id = result["id"]
                self.created_at = result["created_at"]
            logger.info(f"Created transaction: {self.type} {self.symbol or ''} (ID: {self.id})")
        else:
            # Update existing transaction
            db.execute(
                """
                UPDATE transactions
                SET date = ?, account_id = ?, type = ?, symbol = ?, qty = ?, price = ?, fee = ?, notes = ?
                WHERE id = ?
                """,
                (
                    self.date.isoformat(),
                    self.account_id,
                    self.type,
                    self.symbol,
                    self.qty,
                    self.price,
                    self.fee,
                    self.notes,
                    self.id,
                ),
            )
            logger.info(f"Updated transaction ID: {self.id}")

        return self

    def delete(self, db: Optional[Database] = None) -> None:
        """Delete transaction from database.

        Args:
            db: Database instance. If None, creates a new instance.

        Raises:
            ValueError: If transaction ID is not set.
        """
        if db is None:
            db = Database()

        if self.id is None:
            raise ValueError("Cannot delete transaction without ID")

        db.execute("DELETE FROM transactions WHERE id = ?", (self.id,))
        logger.info(f"Deleted transaction ID: {self.id}")
        self.id = None

    def update(self, **kwargs: Any) -> "Transaction":
        """Update transaction fields.

        Args:
            **kwargs: Fields to update.

        Returns:
            Self for method chaining.
        """
        if "date" in kwargs:
            date_val = kwargs["date"]
            if isinstance(date_val, str):
                self.date = date.fromisoformat(date_val)
            else:
                self.date = date_val
        if "account_id" in kwargs:
            self.account_id = kwargs["account_id"]
        if "type" in kwargs:
            self.type = kwargs["type"].upper()
        if "symbol" in kwargs:
            self.symbol = kwargs["symbol"]
        if "qty" in kwargs:
            self.qty = kwargs["qty"]
        if "price" in kwargs:
            self.price = kwargs["price"]
        if "fee" in kwargs:
            self.fee = kwargs["fee"]
        if "notes" in kwargs:
            self.notes = kwargs["notes"]
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary.

        Returns:
            Dictionary representation of transaction.
        """
        return {
            "id": self.id,
            "date": self.date.isoformat() if isinstance(self.date, date) else str(self.date),
            "account_id": self.account_id,
            "type": self.type,
            "symbol": self.symbol,
            "qty": self.qty,
            "price": self.price,
            "fee": self.fee,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        """Create Transaction instance from dictionary.

        Args:
            data: Dictionary with transaction data.

        Returns:
            Transaction instance.
        """
        date_val = data["date"]
        if isinstance(date_val, str):
            date_val = date.fromisoformat(date_val)

        return cls(
            date=date_val,
            account_id=data["account_id"],
            transaction_type=data["type"],
            symbol=data.get("symbol"),
            qty=data.get("qty"),
            price=data.get("price"),
            fee=data.get("fee", 0.0),
            notes=data.get("notes"),
            transaction_id=data.get("id"),
            created_at=data.get("created_at"),
        )

    def get_account(self, db: Optional[Database] = None) -> Optional[Account]:
        """Get associated account.

        Args:
            db: Database instance. If None, creates a new instance.

        Returns:
            Account instance or None if not found.
        """
        from .queries import get_account_by_id

        return get_account_by_id(self.account_id, db)

