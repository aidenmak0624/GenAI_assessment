"""
Initialize SQLite database with synthetic customer support data.
Creates tables for customers, support tickets, products, and orders.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "customer_support.db")


def create_tables(cursor: sqlite3.Cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            city TEXT,
            country TEXT,
            membership_tier TEXT DEFAULT 'Standard',
            account_created DATE NOT NULL,
            is_active BOOLEAN DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            quantity INTEGER DEFAULT 1,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Delivered',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            created_at DATETIME NOT NULL,
            resolved_at DATETIME,
            resolution_notes TEXT,
            assigned_agent TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)


def seed_data(cursor: sqlite3.Cursor):
    # --- Customers ---
    customers = [
        ("Ema", "Johnson", "ema.johnson@email.com", "+1-555-0101",
         "123 Oak Street", "New York", "USA", "Premium", "2022-03-15", 1),
        ("Liam", "Smith", "liam.smith@email.com", "+1-555-0102",
         "456 Maple Ave", "Los Angeles", "USA", "Standard", "2023-01-20", 1),
        ("Sophia", "Garcia", "sophia.garcia@email.com", "+1-555-0103",
         "789 Pine Road", "Chicago", "USA", "Gold", "2021-11-08", 1),
        ("Noah", "Williams", "noah.williams@email.com", "+1-555-0104",
         "321 Elm Blvd", "Houston", "USA", "Standard", "2023-06-12", 1),
        ("Olivia", "Brown", "olivia.brown@email.com", "+1-555-0105",
         "654 Cedar Lane", "Phoenix", "USA", "Premium", "2022-09-01", 1),
        ("James", "Davis", "james.davis@email.com", "+1-555-0106",
         "987 Birch Way", "San Francisco", "USA", "Gold", "2021-05-22", 1),
        ("Isabella", "Martinez", "isabella.martinez@email.com", "+1-555-0107",
         "147 Walnut St", "Miami", "USA", "Standard", "2024-02-14", 1),
        ("Lucas", "Anderson", "lucas.anderson@email.com", "+1-555-0108",
         "258 Spruce Dr", "Seattle", "USA", "Premium", "2022-07-30", 1),
        ("Mia", "Taylor", "mia.taylor@email.com", "+1-555-0109",
         "369 Ash Court", "Denver", "USA", "Standard", "2023-10-05", 0),
        ("Ethan", "Thomas", "ethan.thomas@email.com", "+1-555-0110",
         "480 Poplar Pl", "Boston", "USA", "Gold", "2021-08-19", 1),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO customers "
        "(first_name, last_name, email, phone, address, city, country, "
        "membership_tier, account_created, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        customers,
    )

    # --- Products ---
    products = [
        ("CloudSync Pro", "Software", 49.99, "Cloud storage and sync solution"),
        ("SecureVPN Plus", "Software", 29.99, "Enterprise VPN service"),
        ("DataGuard Backup", "Software", 39.99, "Automated data backup tool"),
        ("SmartDesk Hub", "Hardware", 199.99, "USB-C docking station"),
        ("ErgoKey Wireless", "Hardware", 79.99, "Ergonomic wireless keyboard"),
        ("UltraScreen 27", "Hardware", 349.99, "27-inch 4K monitor"),
        ("TechCare Basic", "Service", 9.99, "Basic support plan - monthly"),
        ("TechCare Premium", "Service", 24.99, "Premium support plan - monthly"),
        ("QuickSetup Service", "Service", 49.99, "One-time device setup assistance"),
        ("PrintMaster X1", "Hardware", 149.99, "Wireless all-in-one printer"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO products "
        "(product_name, category, price, description) "
        "VALUES (?, ?, ?, ?)",
        products,
    )

    # --- Orders ---
    random.seed(42)
    orders = [
        (1, 1, "2023-04-10", 1, 49.99, "Delivered"),
        (1, 4, "2023-06-15", 1, 199.99, "Delivered"),
        (1, 8, "2023-07-01", 1, 24.99, "Active"),
        (2, 2, "2023-08-20", 1, 29.99, "Delivered"),
        (2, 5, "2023-09-12", 2, 159.98, "Delivered"),
        (3, 6, "2022-12-01", 1, 349.99, "Delivered"),
        (3, 1, "2023-03-18", 1, 49.99, "Delivered"),
        (3, 7, "2023-05-01", 1, 9.99, "Active"),
        (4, 3, "2024-01-15", 1, 39.99, "Delivered"),
        (4, 10, "2024-02-20", 1, 149.99, "Delivered"),
        (5, 1, "2023-01-10", 1, 49.99, "Delivered"),
        (5, 8, "2023-01-10", 1, 24.99, "Active"),
        (5, 6, "2023-11-25", 1, 349.99, "Delivered"),
        (6, 2, "2022-06-14", 1, 29.99, "Delivered"),
        (6, 4, "2022-09-30", 1, 199.99, "Delivered"),
        (7, 9, "2024-03-01", 1, 49.99, "Completed"),
        (7, 5, "2024-03-05", 1, 79.99, "Delivered"),
        (8, 1, "2023-02-14", 1, 49.99, "Delivered"),
        (8, 3, "2023-04-22", 1, 39.99, "Delivered"),
        (9, 7, "2024-01-01", 1, 9.99, "Cancelled"),
        (10, 8, "2022-09-01", 1, 24.99, "Active"),
        (10, 6, "2022-10-15", 2, 699.98, "Delivered"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO orders "
        "(customer_id, product_id, order_date, quantity, total_amount, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        orders,
    )

    # --- Support Tickets ---
    tickets = [
        (1, "Unable to sync files", "CloudSync Pro is not syncing my files across devices. "
         "Getting error code CS-401.", "Technical", "High", "Resolved",
         "2023-05-12 09:30:00", "2023-05-12 14:45:00",
         "Reset sync token and cleared cache. Issue resolved.", "Agent Mike"),
        (1, "Billing inquiry", "I was charged twice for my TechCare Premium subscription "
         "this month.", "Billing", "Medium", "Resolved",
         "2023-08-03 11:00:00", "2023-08-04 10:30:00",
         "Duplicate charge confirmed and refunded $24.99.", "Agent Sarah"),
        (1, "SmartDesk Hub not recognized", "My new SmartDesk Hub is not being detected "
         "by my laptop.", "Technical", "High", "Resolved",
         "2023-06-20 15:20:00", "2023-06-21 09:00:00",
         "Updated USB-C drivers. Hub now recognized.", "Agent Mike"),
        (2, "VPN connection drops", "SecureVPN Plus keeps disconnecting every 10 minutes.",
         "Technical", "High", "Open",
         "2023-09-25 08:15:00", None, None, "Agent Tom"),
        (2, "Keyboard key stuck", "The 'E' key on my ErgoKey Wireless sometimes doesn't "
         "register.", "Hardware", "Low", "Open",
         "2023-10-01 13:45:00", None, None, "Agent Sarah"),
        (3, "Monitor flickering", "UltraScreen 27 flickers intermittently at 4K resolution.",
         "Hardware", "High", "Resolved",
         "2023-01-15 10:00:00", "2023-01-17 16:30:00",
         "Firmware update v2.1 applied. Flickering stopped.", "Agent Tom"),
        (3, "Request feature - dark mode", "Would love a dark mode option in CloudSync Pro.",
         "Feature Request", "Low", "Closed",
         "2023-04-02 17:30:00", "2023-04-05 09:00:00",
         "Forwarded to product team. Dark mode planned for Q3.", "Agent Mike"),
        (4, "Backup restore failed", "DataGuard Backup restore failed midway with error "
         "DG-503.", "Technical", "Critical", "Resolved",
         "2024-02-01 07:00:00", "2024-02-01 12:00:00",
         "Corrupt backup index rebuilt. Full restore completed.", "Agent Sarah"),
        (4, "Printer paper jam", "PrintMaster X1 keeps jamming on standard A4 paper.",
         "Hardware", "Medium", "Open",
         "2024-03-10 14:20:00", None, None, "Agent Tom"),
        (5, "Subscription cancellation", "I want to cancel my TechCare Premium plan.",
         "Billing", "Medium", "Resolved",
         "2023-12-01 09:00:00", "2023-12-02 11:00:00",
         "Customer retained with 20% discount offer for 3 months.", "Agent Sarah"),
        (5, "Monitor dead pixel", "Found a dead pixel on my new UltraScreen 27.",
         "Hardware", "Medium", "Open",
         "2024-01-05 16:00:00", None, None, "Agent Mike"),
        (6, "VPN slow speeds", "SecureVPN Plus gives very slow speeds on US servers.",
         "Technical", "Medium", "Resolved",
         "2022-08-10 12:30:00", "2022-08-11 15:00:00",
         "Switched to optimized server pool. Speeds improved 3x.", "Agent Tom"),
        (7, "Setup assistance needed", "Need help setting up my new ErgoKey Wireless "
         "with my Mac.", "Technical", "Low", "Resolved",
         "2024-03-06 10:00:00", "2024-03-06 10:45:00",
         "Guided through Bluetooth pairing. Connected successfully.", "Agent Mike"),
        (8, "CloudSync data loss concern", "Some files appear missing after the last "
         "CloudSync Pro update.", "Technical", "Critical", "Resolved",
         "2023-05-01 08:00:00", "2023-05-01 18:00:00",
         "Files recovered from versioning. Rolled back to previous stable release.",
         "Agent Sarah"),
        (9, "Refund request", "I want a refund for TechCare Basic as I'm closing "
         "my account.", "Billing", "Medium", "Resolved",
         "2024-01-15 11:30:00", "2024-01-16 09:00:00",
         "Prorated refund of $6.66 issued. Account marked for closure.", "Agent Tom"),
        (10, "Dual monitor setup help", "Need help configuring dual UltraScreen 27 "
         "monitors on Windows.", "Technical", "Low", "Resolved",
         "2022-11-01 14:00:00", "2022-11-01 15:30:00",
         "Configured display settings and refresh rates. Both working at 4K.",
         "Agent Mike"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO support_tickets "
        "(customer_id, subject, description, category, priority, status, "
        "created_at, resolved_at, resolution_notes, assigned_agent) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tickets,
    )


def init_database():
    """Create and populate the database. Safe to call multiple times."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_tables(cursor)
    seed_data(cursor)
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")
    return DB_PATH


if __name__ == "__main__":
    init_database()
