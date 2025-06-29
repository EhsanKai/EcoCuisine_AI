import sqlite3
import os
from typing import List, Tuple, Optional


class CuisineDB:
    """Database handler for user cuisines"""
    
    def __init__(self, base_folder: str = "user_databases"):
        """Initialize the cuisine database handler
        
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
            True if created or already exists
        """
        user_folder = self.get_user_folder(user_id)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            return True
        return False
    
    def get_cuisine_db_path(self, user_id: int, cuisine_name: str) -> str:
        """Get the path to a specific cuisine's database
        
        Args:
            user_id: Telegram user ID
            cuisine_name: Name of the cuisine
            
        Returns:
            Path to the specific cuisine database file
        """
        user_folder = self.get_user_folder(user_id)
        # Sanitize cuisine name for filename (remove special characters)
        safe_name = "".join(c for c in cuisine_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        return os.path.join(user_folder, f"{safe_name}.db")
    
    def get_cuisines_db_path(self, user_id: int) -> str:
        """Get the path to user's cuisines index database
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Path to the cuisines index database file
        """
        user_folder = self.get_user_folder(user_id)
        return os.path.join(user_folder, "cuisines_index.db")
    
    def create_cuisine_index_database(self, user_id: int) -> bool:
        """Create cuisine index database for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if created successfully
        """
        # Ensure user folder exists
        self.create_user_folder(user_id)
        
        cuisines_db_path = self.get_cuisines_db_path(user_id)
        
        # Create cuisines index database (stores cuisine names and metadata)
        conn_cuisines = sqlite3.connect(cuisines_db_path)
        cursor_cuisines = conn_cuisines.cursor()
        
        cursor_cuisines.execute('''
        CREATE TABLE IF NOT EXISTS cuisines_index (
            cuisine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuisine_name TEXT NOT NULL UNIQUE,
            cuisine_filename TEXT NOT NULL,
            description TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn_cuisines.commit()
        conn_cuisines.close()
        
        return True
    
    def create_specific_cuisine_database(self, user_id: int, cuisine_name: str, description: str = None) -> Optional[int]:
        """Create a specific cuisine database
        
        Args:
            user_id: Telegram user ID
            cuisine_name: Name of the cuisine
            description: Optional description
            
        Returns:
            Cuisine ID if successful, None if cuisine already exists
        """
        # First ensure the index database exists
        self.create_cuisine_index_database(user_id)
        
        cuisines_db_path = self.get_cuisines_db_path(user_id)
        cuisine_db_path = self.get_cuisine_db_path(user_id, cuisine_name)
        
        # Check if cuisine already exists
        if os.path.exists(cuisine_db_path):
            return None
        
        # Get safe filename for database
        safe_name = "".join(c for c in cuisine_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        cuisine_filename = f"{safe_name}.db"
        
        # Add to index database
        conn_index = sqlite3.connect(cuisines_db_path)
        cursor_index = conn_index.cursor()
        
        try:
            cursor_index.execute('''
            INSERT INTO cuisines_index (cuisine_name, cuisine_filename, description)
            VALUES (?, ?, ?)
            ''', (cuisine_name, cuisine_filename, description))
            
            cuisine_id = cursor_index.lastrowid
            conn_index.commit()
        except sqlite3.IntegrityError:
            # Cuisine name already exists
            conn_index.close()
            return None
        finally:
            conn_index.close()
        
        # Create the specific cuisine database
        conn_cuisine = sqlite3.connect(cuisine_db_path)
        cursor_cuisine = conn_cuisine.cursor()
        
        cursor_cuisine.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT NOT NULL,
            amount TEXT NOT NULL,
            unit TEXT DEFAULT 'pieces',
            notes TEXT,
            category TEXT DEFAULT 'other',
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor_cuisine.execute('''
        CREATE TABLE IF NOT EXISTS cuisine_info (
            id INTEGER PRIMARY KEY,
            cuisine_name TEXT NOT NULL,
            description TEXT,
            cuisine_id INTEGER,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insert cuisine info
        cursor_cuisine.execute('''
        INSERT INTO cuisine_info (id, cuisine_name, description, cuisine_id)
        VALUES (1, ?, ?, ?)
        ''', (cuisine_name, description, cuisine_id))
        
        conn_cuisine.commit()
        conn_cuisine.close()
        
        return cuisine_id
    
    def user_has_cuisine_system(self, user_id: int) -> bool:
        """Check if user has the cuisine system set up (index database exists)
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user has cuisine system set up
        """
        cuisines_db_path = self.get_cuisines_db_path(user_id)
        return os.path.exists(cuisines_db_path)
    
    def cuisine_exists(self, user_id: int, cuisine_name: str) -> bool:
        """Check if a specific cuisine exists
        
        Args:
            user_id: Telegram user ID
            cuisine_name: Name of the cuisine
            
        Returns:
            True if cuisine exists
        """
        cuisine_db_path = self.get_cuisine_db_path(user_id, cuisine_name)
        return os.path.exists(cuisine_db_path)
    
    def get_cuisines(self, user_id: int) -> List[Tuple]:
        """Get all cuisines for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of tuples containing cuisine information
        """
        cuisines_db_path = self.get_cuisines_db_path(user_id)
        
        if not os.path.exists(cuisines_db_path):
            return []
        
        conn = sqlite3.connect(cuisines_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT cuisine_id, cuisine_name, cuisine_filename, description, created_date
        FROM cuisines_index
        ORDER BY created_date DESC
        ''')
        
        cuisines = cursor.fetchall()
        conn.close()
        
        return cuisines
    
    def add_ingredient_to_cuisine(self, user_id: int, cuisine_name: str, 
                                 ingredient_name: str, amount: str, 
                                 unit: str = 'pieces', notes: str = None, 
                                 category: str = 'other') -> bool:
        """Add an ingredient to a specific cuisine
        
        Args:
            user_id: Telegram user ID
            cuisine_name: Name of the cuisine
            ingredient_name: Name of the ingredient
            amount: Amount/quantity
            unit: Unit of measurement
            notes: Optional notes
            category: Ingredient category
            
        Returns:
            True if added successfully
        """
        cuisine_db_path = self.get_cuisine_db_path(user_id, cuisine_name)
        
        if not os.path.exists(cuisine_db_path):
            return False
        
        conn = sqlite3.connect(cuisine_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO ingredients 
        (ingredient_name, amount, unit, notes, category)
        VALUES (?, ?, ?, ?, ?)
        ''', (ingredient_name, amount, unit, notes, category))
        
        conn.commit()
        conn.close()
        return True
    
    def get_cuisine_ingredients(self, user_id: int, cuisine_name: str) -> List[Tuple]:
        """Get all ingredients for a specific cuisine
        
        Args:
            user_id: Telegram user ID
            cuisine_name: Name of the cuisine
            
        Returns:
            List of tuples containing ingredient information
        """
        cuisine_db_path = self.get_cuisine_db_path(user_id, cuisine_name)
        
        if not os.path.exists(cuisine_db_path):
            return []
        
        conn = sqlite3.connect(cuisine_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, ingredient_name, amount, unit, notes, category, added_date
        FROM ingredients
        ORDER BY added_date
        ''')
        
        ingredients = cursor.fetchall()
        conn.close()
        
        return ingredients
    
    def get_cuisine_info(self, user_id: int, cuisine_name: str) -> Optional[Tuple]:
        """Get information about a specific cuisine
        
        Args:
            user_id: Telegram user ID
            cuisine_name: Name of the cuisine
            
        Returns:
            Tuple containing cuisine information or None
        """
        cuisine_db_path = self.get_cuisine_db_path(user_id, cuisine_name)
        
        if not os.path.exists(cuisine_db_path):
            return None
        
        conn = sqlite3.connect(cuisine_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT cuisine_name, description, cuisine_id, created_date
        FROM cuisine_info
        WHERE id = 1
        ''')
        
        cuisine_info = cursor.fetchone()
        conn.close()
        
        return cuisine_info
