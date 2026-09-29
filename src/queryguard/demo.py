"""Small reproducible SQLite demo used by local examples and smoke tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path


CUSTOMERS = [
    (1, "Asha", "Patil", "India"),
    (2, "Rohan", "Shah", "India"),
    (3, "Maya", "Wilson", "USA"),
    (4, "Liam", "Brown", "UK"),
    (5, "Sara", "Khan", "UAE"),
    (6, "Noah", "Martin", "France"),
]

TRACKS = [
    (1, "Field Notes", "Rock", 0.99),
    (2, "Green Rows", "Rock", 1.29),
    (3, "Morning Rain", "Jazz", 0.99),
    (4, "Harvest", "Folk", 1.49),
    (5, "Long Road", "Rock", 0.79),
    (6, "Blue Soil", "Jazz", 1.19),
    (7, "Night Market", "Electronic", 1.29),
    (8, "Open Sky", "Folk", 0.99),
]

INVOICES = [
    (1, 1, "2026-01-04", 120.50),
    (2, 2, "2026-01-19", 89.00),
    (3, 1, "2026-02-01", 210.25),
    (4, 3, "2026-02-08", 175.00),
    (5, 4, "2026-02-12", 95.50),
    (6, 5, "2026-03-03", 142.75),
    (7, 2, "2026-03-05", 65.25),
    (8, 6, "2026-03-17", 111.00),
]


def create_demo_database(path: Path, *, overwrite: bool = True) -> Path:
    """Create the bundled synthetic demo database and return its path."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and overwrite:
        path.unlink()
    if path.exists():
        return path

    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE Customer (
                CustomerId INTEGER PRIMARY KEY,
                FirstName TEXT NOT NULL,
                LastName TEXT NOT NULL,
                Country TEXT NOT NULL
            );
            CREATE TABLE Track (
                TrackId INTEGER PRIMARY KEY,
                Name TEXT NOT NULL,
                Genre TEXT NOT NULL,
                UnitPrice REAL NOT NULL
            );
            CREATE TABLE Invoice (
                InvoiceId INTEGER PRIMARY KEY,
                CustomerId INTEGER NOT NULL,
                InvoiceDate TEXT NOT NULL,
                Total REAL NOT NULL,
                FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
            );
            """
        )
        connection.executemany("INSERT INTO Customer VALUES (?, ?, ?, ?)", CUSTOMERS)
        connection.executemany("INSERT INTO Track VALUES (?, ?, ?, ?)", TRACKS)
        connection.executemany("INSERT INTO Invoice VALUES (?, ?, ?, ?)", INVOICES)
        connection.commit()
    finally:
        connection.close()
    return path
