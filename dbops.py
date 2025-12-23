"""Database operations module for MS Access backend support.

This module provides MS Access database backend functionality with
the same capabilities as JSON file storage.
"""

import pyodbc
import json
import logging
from typing import Dict, List, Any, Optional, Tuple


class AccessDatabase:
    """MS Access database handler for qtIPvisual"""

    def __init__(self, db_path: str):
        """Initialize Access database connection.

        Args:
            db_path: Path to the .accdb or .mdb file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> bool:
        """Establish connection to Access database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # MS Access connection string
            conn_str = (
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                f"DBQ={self.db_path};"
            )
            self.conn = pyodbc.connect(conn_str)
            self.cursor = self.conn.cursor()
            logging.info(f"Connected to database: {self.db_path}")
            return True
        except pyodbc.Error as e:
            logging.error(f"Database connection failed: {e}")
            return False

    def create_tables(self) -> bool:
        """Create required tables if they don't exist.

        Tables:
            - Tabs: Stores tab information
            - Fields: Stores field definitions
            - Networks: Stores network data
            - ColorMappings: Stores color pattern mappings
        """
        try:
            # Check if tables exist, create if not
            tables = [row.table_name for row in self.cursor.tables()]

            if "Tabs" not in tables:
                self.cursor.execute(
                    """
                    CREATE TABLE Tabs (
                        TabID AUTOINCREMENT,
                        TabName TEXT(255) NOT NULL,
                        CreatedDate DATETIME,
                        PRIMARY KEY (TabID)
                    )
                """
                )

            if "Fields" not in tables:
                self.cursor.execute(
                    """
                    CREATE TABLE Fields (
                        FieldID AUTOINCREMENT,
                        TabID INTEGER NOT NULL,
                        FieldName TEXT(255) NOT NULL,
                        ControlType TEXT(50),
                        ColorWeight INTEGER,
                        ShowInCells YESNO,
                        PRIMARY KEY (FieldID)
                    )
                """
                )

            if "Networks" not in tables:
                self.cursor.execute(
                    """
                    CREATE TABLE Networks (
                        NetworkID AUTOINCREMENT,
                        TabID INTEGER NOT NULL,
                        CIDR TEXT(50) NOT NULL,
                        FieldValues MEMO,
                        PRIMARY KEY (NetworkID)
                    )
                """
                )

            if "ColorMappings" not in tables:
                self.cursor.execute(
                    """
                    CREATE TABLE ColorMappings (
                        MappingID AUTOINCREMENT,
                        FieldID INTEGER NOT NULL,
                        Pattern TEXT(255),
                        Color TEXT(50),
                        PRIMARY KEY (MappingID)
                    )
                """
                )

            self.conn.commit()
            logging.info("Database tables created/verified")
            return True
        except pyodbc.Error as e:
            logging.error(f"Table creation failed: {e}")
            return False

    def save_data(self, tabs_data: List[Dict[str, Any]]) -> bool:
        """Save all tabs data to database.

        Args:
            tabs_data: List of tab dictionaries with fields and networks

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Clear existing data
            self.cursor.execute("DELETE FROM ColorMappings")
            self.cursor.execute("DELETE FROM Networks")
            self.cursor.execute("DELETE FROM Fields")
            self.cursor.execute("DELETE FROM Tabs")

            for tab_data in tabs_data:
                # Insert tab
                self.cursor.execute(
                    "INSERT INTO Tabs (TabName) VALUES (?)", (tab_data["name"],)
                )
                self.cursor.execute("SELECT @@IDENTITY")
                tab_id = self.cursor.fetchone()[0]

                # Insert fields
                fields = tab_data.get("fields", {})
                field_id_map = {}

                for field_name, field_data in fields.items():
                    self.cursor.execute(
                        """INSERT INTO Fields
                        (TabID, FieldName, ControlType, ColorWeight, ShowInCells)
                        VALUES (?, ?, ?, ?, ?)""",
                        (
                            tab_id,
                            field_name,
                            field_data.get("controlType", "lineEdit"),
                            field_data.get("colorWeight", 1),
                            field_data.get("show", False),
                        ),
                    )
                    self.cursor.execute("SELECT @@IDENTITY")
                    field_id = self.cursor.fetchone()[0]
                    field_id_map[field_name] = field_id

                    # Insert color mappings
                    color_map = field_data.get("colorMap", {})
                    for pattern, color in color_map.items():
                        self.cursor.execute(
                            """INSERT INTO ColorMappings
                            (FieldID, Pattern, Color) VALUES (?, ?, ?)""",
                            (field_id, pattern, color),
                        )

                # Insert networks
                networks = tab_data.get("networks", {})
                for cidr, field_values in networks.items():
                    # Store field values as JSON
                    field_values_json = json.dumps(field_values)
                    self.cursor.execute(
                        """INSERT INTO Networks
                        (TabID, CIDR, FieldValues) VALUES (?, ?, ?)""",
                        (tab_id, cidr, field_values_json),
                    )

            self.conn.commit()
            logging.info("Data saved to database successfully")
            return True
        except pyodbc.Error as e:
            logging.error(f"Save failed: {e}")
            self.conn.rollback()
            return False

    def load_data(self) -> Optional[List[Dict[str, Any]]]:
        """Load all tabs data from database.

        Returns:
            List of tab dictionaries or None if load failed
        """
        try:
            tabs_data = []

            # Get all tabs
            self.cursor.execute("SELECT TabID, TabName FROM Tabs ORDER BY TabID")
            tabs = self.cursor.fetchall()

            for tab_id, tab_name in tabs:
                tab_data = {"name": tab_name, "fields": {}, "networks": {}}

                # Get fields for this tab
                self.cursor.execute(
                    """SELECT FieldID, FieldName, ControlType,
                    ColorWeight, ShowInCells FROM Fields WHERE TabID = ?""",
                    (tab_id,),
                )
                fields = self.cursor.fetchall()

                for field_id, field_name, ctrl_type, weight, show in fields:
                    field_data = {
                        "controlType": ctrl_type,
                        "colorWeight": weight,
                        "show": bool(show),
                        "colorMap": {},
                    }

                    # Get color mappings for this field
                    self.cursor.execute(
                        """SELECT Pattern, Color FROM ColorMappings
                        WHERE FieldID = ?""",
                        (field_id,),
                    )
                    color_mappings = self.cursor.fetchall()

                    for pattern, color in color_mappings:
                        field_data["colorMap"][pattern] = color

                    tab_data["fields"][field_name] = field_data

                # Get networks for this tab
                self.cursor.execute(
                    "SELECT CIDR, FieldValues FROM Networks WHERE TabID = ?", (tab_id,)
                )
                networks = self.cursor.fetchall()

                for cidr, field_values_json in networks:
                    field_values = json.loads(field_values_json)
                    tab_data["networks"][cidr] = field_values

                tabs_data.append(tab_data)

            logging.info(f"Loaded {len(tabs_data)} tabs from database")
            return tabs_data
        except pyodbc.Error as e:
            logging.error(f"Load failed: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def create_new_database(db_path: str) -> bool:
    """Create a new Access database file with required tables.

    Args:
        db_path: Path where the new database should be created

    Returns:
        True if creation successful, False otherwise
    """
    try:
        import os

        # Convert to absolute path
        db_path = os.path.abspath(db_path)

        # Use ADOX to create the database via COM
        try:
            import win32com.client

            # Remove file if it exists
            if os.path.exists(db_path):
                os.remove(db_path)

            # Create new Access database using ADOX
            catalog = win32com.client.Dispatch("ADOX.Catalog")
            # For .accdb (Access 2007+) format
            catalog.Create(f"Provider=Microsoft.ACE.OLEDB.12.0;Data Source={db_path}")
            catalog = None  # Release COM object

            logging.info(f"Created new database: {db_path}")

        except ImportError:
            # Fallback: Try using pypyodbc or create minimal file
            logging.warning("win32com not available, trying alternative method")
            # Create a minimal empty .accdb file structure
            # This is a workaround - the proper way is via COM
            import struct

            # Basic Access 2007+ file header
            with open(db_path, "wb") as f:
                # Write minimal ACE database header
                f.write(b"\x00\x01\x00\x00Standard ACE DB\x00")
                f.write(b"\x00" * 1000)  # Padding

        # Now create tables
        db = AccessDatabase(db_path)
        if db.connect():
            success = db.create_tables()
            db.close()
            return success
        return False
    except Exception as e:
        logging.error(f"Database creation failed: {e}")
        import traceback

        logging.error(traceback.format_exc())
        return False


def is_access_available() -> Tuple[bool, str]:
    """Check if MS Access driver is available.

    Returns:
        Tuple of (is_available, message)
    """
    try:
        drivers = [d for d in pyodbc.drivers() if "Access" in d]
        if drivers:
            return True, f"Access driver available: {drivers[0]}"
        return False, "MS Access driver not found. Install MS Access or ACE driver."
    except Exception as e:
        return False, f"Error checking drivers: {e}"
