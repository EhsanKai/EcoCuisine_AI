import sqlite3
import os
from typing import List, Tuple, Optional


class RefrigeratorDB:
    """Database handler for user refrigerators"""

    def __init__(self, base_folder: str = "user_databases"):
        """Initialize the database handler

        Args:
            base_folder: Base folder to store user databases
        """
        self.base_folder = base_folder
        # Create the base database folder if it doesn't exist
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)

    def get_user_folder(self, user_id: int) -> str:
        """Get the user's personal folder path

        Args:
            user_id: Telegram user ID

        Returns:
            Path to the user's personal folder
        """
        return os.path.join(self.base_folder, f"user_{user_id}")

    def create_user_folder(self, user_id: int) -> bool:
        """Create a user's personal folder if it doesn't exist

        Args:
            user_id: Telegram user ID

        Returns:
            True if created, False if already exists
        """
        user_folder = self.get_user_folder(user_id)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            return True
        return False

    def get_db_path(self, user_id: int) -> str:
        """Get the database path for a specific user

        Args:
            user_id: Telegram user ID

        Returns:
            Path to the user's refrigerator database file
        """
        user_folder = self.get_user_folder(user_id)
        return os.path.join(user_folder, "refrigerator.db")

    def create_user_refrigerator(self, user_id: int) -> bool:
        """Create a new refrigerator database for a user

        Args:
            user_id: Telegram user ID

        Returns:
            True if created successfully, False if already exists
        """
        # Ensure user folder exists
        self.create_user_folder(user_id)

        db_path = self.get_db_path(user_id)

        # Check if database already exists
        if os.path.exists(db_path):
            return False

        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create refrigerator table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS refrigerator_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit TEXT DEFAULT 'pieces',
            expiry_date TEXT,
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Create user info table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS user_info (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        conn.commit()
        conn.close()
        return True

    def user_has_refrigerator(self, user_id: int) -> bool:
        """Check if user already has a refrigerator database

        Args:
            user_id: Telegram user ID

        Returns:
            True if user has a refrigerator, False otherwise
        """
        db_path = self.get_db_path(user_id)
        return os.path.exists(db_path)

    def get_refrigerator_items(self, user_id: int) -> List[Tuple]:
        """Get all items from user's refrigerator

        Args:
            user_id: Telegram user ID

        Returns:
            List of tuples containing item information
        """
        db_path = self.get_db_path(user_id)

        if not os.path.exists(db_path):
            return []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        SELECT id, item_name, quantity, unit, expiry_date, added_date
        FROM refrigerator_items
        ORDER BY added_date DESC
        """
        )

        items = cursor.fetchall()
        conn.close()

        return items

    def add_item_to_refrigerator(
        self,
        user_id: int,
        item_name: str,
        quantity: int = 1,
        unit: str = "pieces",
        expiry_date: Optional[str] = None,
    ) -> bool:
        """Add an item to user's refrigerator

        Args:
            user_id: Telegram user ID
            item_name: Name of the item
            quantity: Quantity of the item
            unit: Unit of measurement
            expiry_date: Expiry date (optional)

        Returns:
            True if added successfully, False otherwise
        """
        db_path = self.get_db_path(user_id)

        if not os.path.exists(db_path):
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT INTO refrigerator_items (item_name, quantity, unit, expiry_date)
        VALUES (?, ?, ?, ?)
        """,
            (item_name, quantity, unit, expiry_date),
        )

        conn.commit()
        conn.close()
        return True

    def remove_item_from_refrigerator(self, user_id: int, item_id: int) -> bool:
        """Remove an item from user's refrigerator

        Args:
            user_id: Telegram user ID
            item_id: ID of the item to remove

        Returns:
            True if removed successfully, False otherwise
        """
        db_path = self.get_db_path(user_id)

        if not os.path.exists(db_path):
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM refrigerator_items WHERE id = ?", (item_id,))

        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()

        return affected_rows > 0

    def save_user_info(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ):
        """Save user information to database

        Args:
            user_id: Telegram user ID
            username: Username
            first_name: First name
            last_name: Last name
        """
        db_path = self.get_db_path(user_id)

        if not os.path.exists(db_path):
            return

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
        INSERT OR REPLACE INTO user_info (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        """,
            (user_id, username, first_name, last_name),
        )

        conn.commit()
        conn.close()
