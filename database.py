import os
import csv
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data.db")
CSV_PATH = os.path.join(BASE_DIR, "Datasets", "used_cars_data.csv")


def _read_only_authorizer(action, arg1, arg2, database_name, trigger_name):
    allowed_actions = {
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_FUNCTION,
    }
    return sqlite3.SQLITE_OK if action in allowed_actions else sqlite3.SQLITE_DENY


def initialize_database():
    if os.path.exists(DATABASE_PATH):
        return

    columns = [
        "s_no", "name", "location", "year", "kilometers_driven",
        "fuel_type", "transmission", "owner_type", "mileage", "engine",
        "power", "seats", "new_price", "price",
    ]

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = []
        for row in reader:
            rows.append((
                int(row["S.No."]),
                row["Name"],
                row["Location"],
                int(row["Year"]),
                int(row["Kilometers_Driven"]),
                row["Fuel_Type"],
                row["Transmission"],
                row["Owner_Type"],
                row["Mileage"],
                row["Engine"],
                row["Power"],
                int(row["Seats"]) if row["Seats"] else None,
                row["New_Price"] or None,
                float(row["Price"]) if row["Price"] else None,
            ))

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute("""
            CREATE TABLE used_cars (
                s_no INTEGER,
                name TEXT,
                location TEXT,
                year INTEGER,
                kilometers_driven INTEGER,
                fuel_type TEXT,
                transmission TEXT,
                owner_type TEXT,
                mileage TEXT,
                engine TEXT,
                power TEXT,
                seats INTEGER,
                new_price TEXT,
                price REAL
            )
        """)
        placeholders = ", ".join("?" for _ in columns)
        quoted_columns = ", ".join(columns)
        connection.executemany(
            f"INSERT INTO used_cars ({quoted_columns}) VALUES ({placeholders})",
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def execute_sql_query(sql):
    """Execute a read-only SQLite query and return rows as dictionaries."""
    normalized_sql = sql.strip().lower()
    if not normalized_sql.startswith(("select", "with")):
        raise ValueError("Only SELECT and WITH queries are allowed.")
    if ";" in sql.rstrip().rstrip(";"):
        raise ValueError("Only one SQL statement is allowed.")

    initialize_database()
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.set_authorizer(_read_only_authorizer)

    try:
        cursor = connection.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_database_schema():
    """Return table and column metadata for SQL generation."""
    initialize_database()
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        tables = {}
        table_rows = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (table_name,) in table_rows:
            columns = connection.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
            tables[table_name] = [
                {"name": column[1], "type": column[2] or "TEXT"}
                for column in columns
            ]
        return tables
    finally:
        connection.close()
