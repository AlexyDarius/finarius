"""Account model for Finarius portfolio tracking application."""

from typing import Optional, Dict, Any
import logging

from ..database import Database

logger = logging.getLogger(__name__)


class Account:
    """Account model representing a portfolio account."""

    def __init__(
        self,
        name: str,
        currency: str = "USD",
        account_id: Optional[int] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        """Initialize Account instance.

        Args:
            name: Account name (must be unique).
            currency: Currency code (default: 'USD').
            account_id: Account ID (for existing accounts).
            created_at: Creation timestamp.
            updated_at: Last update timestamp.
        """
        self.id = account_id
        self.name = name
        self.currency = currency
        self.created_at = created_at
        self.updated_at = updated_at

    def validate(self) -> None:
        """Validate account data.

        Raises:
            ValueError: If validation fails.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Account name cannot be empty")
        if not self.currency or not self.currency.strip():
            raise ValueError("Currency cannot be empty")
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code (e.g., USD, EUR)")

    def save(self, db: Optional[Database] = None) -> "Account":
        """Save account to database.

        Args:
            db: Database instance. If None, creates a new instance.

        Returns:
            Self with updated ID and timestamps.

        Raises:
            ValueError: If validation fails.
            sqlite3.IntegrityError: If name already exists.
        """
        if db is None:
            db = Database()

        self.validate()

        if self.id is None:
            # Insert new account
            db.execute(
                """
                INSERT INTO accounts (name, currency)
                VALUES (?, ?)
                """,
                (self.name, self.currency),
            )
            # Get the inserted ID
            result = db.fetchone(
                "SELECT id, created_at, updated_at FROM accounts WHERE name = ?",
                (self.name,),
            )
            if result:
                self.id = result["id"]
                self.created_at = result["created_at"]
                self.updated_at = result["updated_at"]
            logger.info(f"Created account: {self.name} (ID: {self.id})")
        else:
            # Update existing account
            db.execute(
                """
                UPDATE accounts
                SET name = ?, currency = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (self.name, self.currency, self.id),
            )
            result = db.fetchone("SELECT updated_at FROM accounts WHERE id = ?", (self.id,))
            if result:
                self.updated_at = result["updated_at"]
            logger.info(f"Updated account: {self.name} (ID: {self.id})")

        return self

    def delete(self, db: Optional[Database] = None) -> None:
        """Delete account from database.

        Args:
            db: Database instance. If None, creates a new instance.

        Raises:
            ValueError: If account ID is not set.
        """
        if db is None:
            db = Database()

        if self.id is None:
            raise ValueError("Cannot delete account without ID")

        db.execute("DELETE FROM accounts WHERE id = ?", (self.id,))
        logger.info(f"Deleted account: {self.name} (ID: {self.id})")
        self.id = None

    def update(self, **kwargs: Any) -> "Account":
        """Update account fields.

        Args:
            **kwargs: Fields to update (name, currency).

        Returns:
            Self for method chaining.
        """
        if "name" in kwargs:
            self.name = kwargs["name"]
        if "currency" in kwargs:
            self.currency = kwargs["currency"]
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert account to dictionary.

        Returns:
            Dictionary representation of account.
        """
        return {
            "id": self.id,
            "name": self.name,
            "currency": self.currency,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        """Create Account instance from dictionary.

        Args:
            data: Dictionary with account data.

        Returns:
            Account instance.
        """
        return cls(
            name=data["name"],
            currency=data.get("currency", "USD"),
            account_id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

