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
            - Networks: Stores network data with dynamic columns
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

    def add_field_column(self, field_name: str, control_type: str) -> bool:
        """Add a column to Networks table for a new field.

        Args:
            field_name: Name of the field (will be column name)
            control_type: Type of control (lineEdit, checkbox, etc.)

        Returns:
            True if column added or already exists, False on error
        """
        try:
            # Check if column already exists
            columns = [col.column_name for col in self.cursor.columns(table="Networks")]

            if field_name in columns:
                logging.debug(f"Column {field_name} already exists")
                return True

            # Determine SQL data type based on control type
            if control_type == "checkbox":
                sql_type = "YESNO"
            else:
                sql_type = "TEXT(255)"

            # Add column
            self.cursor.execute(
                f"ALTER TABLE Networks ADD COLUMN [{field_name}] {sql_type}"
            )
            self.conn.commit()
            logging.info(f"Added column {field_name} ({sql_type}) to Networks table")
            return True
        except pyodbc.Error as e:
            logging.error(f"Failed to add column {field_name}: {e}")
            return False

    def ensure_all_field_columns(self, fields: Dict[str, Dict[str, Any]]) -> bool:
        """Ensure all fields have corresponding columns in Networks table.

        Args:
            fields: Dictionary of field definitions

        Returns:
            True if all columns exist or were created successfully
        """
        try:
            for field_name, field_data in fields.items():
                control_type = field_data.get("controlType", "lineEdit")
                if not self.add_field_column(field_name, control_type):
                    return False
            return True
        except Exception as e:
            logging.error(f"Error ensuring field columns: {e}")
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

                # Insert fields and ensure columns exist
                fields = tab_data.get("fields", {})
                field_id_map = {}

                # Ensure all field columns exist in Networks table
                self.ensure_all_field_columns(fields)

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

                # Insert networks with dynamic columns
                networks = tab_data.get("networks", {})
                for cidr, field_values in networks.items():
                    # Build dynamic INSERT statement
                    columns = ["TabID", "CIDR"]
                    values = [tab_id, cidr]
                    placeholders = ["?", "?"]

                    for field_name, field_value in field_values.items():
                        if field_name in fields:
                            columns.append(f"[{field_name}]")
                            placeholders.append("?")

                            # Handle boolean values for checkboxes
                            if fields[field_name].get("controlType") == "checkbox":
                                # Convert to boolean
                                if isinstance(field_value, bool):
                                    values.append(field_value)
                                elif isinstance(field_value, str):
                                    values.append(
                                        field_value.lower() in ["true", "1", "yes"]
                                    )
                                else:
                                    values.append(bool(field_value))
                            else:
                                values.append(
                                    str(field_value) if field_value is not None else ""
                                )

                    # Execute dynamic INSERT
                    sql = f"INSERT INTO Networks ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    self.cursor.execute(sql, values)

            self.conn.commit()
            logging.info("Data saved to database successfully")
            return True
        except pyodbc.Error as e:
            logging.error(f"Save failed: {e}")
            self.conn.rollback()
            return False

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

                # Get networks for this tab with dynamic columns
                # First get the column names for Networks table
                columns = [
                    col.column_name for col in self.cursor.columns(table="Networks")
                ]

                # Filter out system columns to get field columns
                system_columns = ["NetworkID", "TabID", "CIDR"]
                field_columns = [col for col in columns if col not in system_columns]

                # Build dynamic SELECT query
                select_columns = ["CIDR"] + [f"[{col}]" for col in field_columns]
                sql = (
                    f"SELECT {', '.join(select_columns)} FROM Networks WHERE TabID = ?"
                )

                self.cursor.execute(sql, (tab_id,))
                networks = self.cursor.fetchall()

                for row in networks:
                    cidr = row[0]
                    field_values = {}

                    # Map column values to field names
                    for i, field_name in enumerate(field_columns, start=1):
                        value = row[i]

                        # Handle different field types
                        if field_name in tab_data["fields"]:
                            ctrl_type = tab_data["fields"][field_name].get(
                                "controlType", "lineEdit"
                            )

                            if ctrl_type == "checkbox":
                                # Convert to boolean
                                field_values[field_name] = bool(value)
                            else:
                                # Convert to string, handle None
                                field_values[field_name] = (
                                    str(value) if value is not None else ""
                                )
                        else:
                            # Unknown field, treat as string
                            field_values[field_name] = (
                                str(value) if value is not None else ""
                            )

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
