"""Price model for Finarius portfolio tracking application."""

from typing import Optional, Dict, Any
from datetime import date
import logging

from ..database import Database

logger = logging.getLogger(__name__)


class Price:
    """Price model representing market price data."""

    def __init__(
        self,
        symbol: str,
        date: date,
        close: float,
        open_price: Optional[float] = None,
        high: Optional[float] = None,
        low: Optional[float] = None,
        volume: Optional[int] = None,
        created_at: Optional[str] = None,
    ) -> None:
        """Initialize Price instance.

        Args:
            symbol: Stock symbol.
            date: Price date.
            close: Closing price.
            open_price: Opening price.
            high: High price.
            low: Low price.
            volume: Trading volume.
            created_at: Creation timestamp.
        """
        self.symbol = symbol.upper()
        # Handle both date objects and date strings
        if isinstance(date, str):
            self.date = date.fromisoformat(date)
        else:
            self.date = date
        self.close = close
        self.open = open_price
        self.high = high
        self.low = low
        self.volume = volume
        self.created_at = created_at

    def validate(self) -> None:
        """Validate price data.

        Raises:
            ValueError: If validation fails.
        """
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")
        if self.close <= 0:
            raise ValueError("Close price must be positive")
        if self.open is not None and self.open <= 0:
            raise ValueError("Open price must be positive")
        if self.high is not None and self.high <= 0:
            raise ValueError("High price must be positive")
        if self.low is not None and self.low <= 0:
            raise ValueError("Low price must be positive")
        if self.high is not None and self.low is not None and self.high < self.low:
            raise ValueError("High price cannot be less than low price")
        if self.volume is not None and self.volume < 0:
            raise ValueError("Volume cannot be negative")

    def save(self, db: Optional[Database] = None) -> "Price":
        """Save price to database.

        Args:
            db: Database instance. If None, creates a new instance.

        Returns:
            Self with updated timestamp.

        Raises:
            ValueError: If validation fails.
        """
        if db is None:
            db = Database()

        self.validate()

        # Use INSERT OR REPLACE for upsert behavior
        db.execute(
            """
            INSERT OR REPLACE INTO prices (symbol, date, close, open, high, low, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.symbol,
                self.date.isoformat(),
                self.close,
                self.open,
                self.high,
                self.low,
                self.volume,
            ),
        )
        result = db.fetchone(
            "SELECT created_at FROM prices WHERE symbol = ? AND date = ?",
            (self.symbol, self.date.isoformat()),
        )
        if result:
            self.created_at = result["created_at"]
        logger.debug(f"Saved price: {self.symbol} on {self.date}")

        return self

    def delete(self, db: Optional[Database] = None) -> None:
        """Delete price from database.

        Args:
            db: Database instance. If None, creates a new instance.
        """
        if db is None:
            db = Database()

        db.execute(
            "DELETE FROM prices WHERE symbol = ? AND date = ?",
            (self.symbol, self.date.isoformat()),
        )
        logger.debug(f"Deleted price: {self.symbol} on {self.date}")

    def update(self, **kwargs: Any) -> "Price":
        """Update price fields.

        Args:
            **kwargs: Fields to update.

        Returns:
            Self for method chaining.
        """
        if "close" in kwargs:
            self.close = kwargs["close"]
        if "open" in kwargs:
            self.open = kwargs["open"]
        if "high" in kwargs:
            self.high = kwargs["high"]
        if "low" in kwargs:
            self.low = kwargs["low"]
        if "volume" in kwargs:
            self.volume = kwargs["volume"]
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert price to dictionary.

        Returns:
            Dictionary representation of price.
        """
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat() if isinstance(self.date, date) else str(self.date),
            "close": self.close,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Price":
        """Create Price instance from dictionary.

        Args:
            data: Dictionary with price data.

        Returns:
            Price instance.
        """
        date_val = data["date"]
        if isinstance(date_val, str):
            date_val = date.fromisoformat(date_val)

        return cls(
            symbol=data["symbol"],
            date=date_val,
            close=data["close"],
            open_price=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            volume=data.get("volume"),
            created_at=data.get("created_at"),
        )

