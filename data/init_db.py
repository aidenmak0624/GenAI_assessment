"""
Initialize SQLite database with scenario-rich synthetic customer support data.

The seeded data is intentionally designed for:
  - SQL lookups across customers, orders, and tickets
  - ambiguous-name lookups
  - no-order / no-ticket edge cases
  - hybrid tests against the public return-policy PDFs
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, time, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "customer_support.db")


def _date_days_ago(days_ago: int) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


def _timestamp_days_ago(days_ago: int, hour: int, minute: int = 0) -> str:
    value = datetime.combine(date.today() - timedelta(days=days_ago), time(hour, minute))
    return value.strftime("%Y-%m-%d %H:%M:%S")


CUSTOMERS = [
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
    ("Emma", "Carter", "emma.carter@email.com", "+1-555-0111",
     "12 King Street", "Toronto", "Canada", "Premium", "2024-05-10", 1),
    ("Emma", "Collins", "emma.collins@email.com", "+1-555-0112",
     "80 Congress Ave", "Austin", "USA", "Gold", "2024-04-18", 1),
    ("Liam", "Johnson", "liam.johnson@email.com", "+1-555-0113",
     "950 Lake Shore Dr", "Dallas", "USA", "Standard", "2024-06-02", 1),
    ("Ava", "Chen", "ava.chen@email.com", "+1-555-0114",
     "14 Front Street", "Vancouver", "Canada", "Standard", "2024-07-11", 1),
    ("Harper", "Allen", "harper.allen@email.com", "+1-555-0115",
     "51 Market St", "Portland", "USA", "Premium", "2023-12-09", 1),
    ("Zoe", "Kim", "zoe.kim@email.com", "+1-555-0116",
     "88 Midtown Way", "Atlanta", "USA", "Gold", "2024-02-01", 1),
    ("Mason", "Patel", "mason.patel@email.com", "+1-555-0117",
     "27 Hudson Lane", "New York", "USA", "Standard", "2024-03-14", 1),
    ("Amelia", "Wilson", "amelia.wilson@email.com", "+1-555-0118",
     "602 Harbor Ave", "San Diego", "USA", "Premium", "2023-11-20", 1),
    ("Daniel", "Lee", "daniel.lee@email.com", "+1-555-0119",
     "75 Wellington St", "Toronto", "Canada", "Standard", "2024-01-17", 1),
    ("Grace", "Nguyen", "grace.nguyen@email.com", "+1-555-0120",
     "18 Lake View", "Chicago", "USA", "Gold", "2023-08-30", 1),
    ("Henry", "Walker", "henry.walker@email.com", "+1-555-0121",
     "412 Desert Bloom", "Phoenix", "USA", "Premium", "2023-09-15", 1),
    ("Chloe", "Adams", "chloe.adams@email.com", "+1-555-0122",
     "730 Biscayne Dr", "Miami", "USA", "Standard", "2024-08-08", 1),
    ("Benjamin", "Scott", "benjamin.scott@email.com", "+1-555-0123",
     "210 Boylston St", "Boston", "USA", "Gold", "2023-07-07", 1),
    ("Ella", "Rivera", "ella.rivera@email.com", "+1-555-0124",
     "92 Pine Crest", "Seattle", "USA", "Premium", "2024-02-22", 1),
    ("Jack", "Turner", "jack.turner@email.com", "+1-555-0125",
     "36 Mile High Rd", "Denver", "USA", "Standard", "2023-10-18", 1),
    ("Avery", "Brooks", "avery.brooks@email.com", "+1-555-0126",
     "155 Fifth Ave", "New York", "USA", "Premium", "2023-12-04", 1),
    ("Samuel", "Reed", "samuel.reed@email.com", "+1-555-0127",
     "44 Sunset Blvd", "Los Angeles", "USA", "Gold", "2023-05-01", 1),
    ("Layla", "Flores", "layla.flores@email.com", "+1-555-0128",
     "807 Bayou Road", "Houston", "USA", "Standard", "2024-01-29", 1),
    ("Owen", "Cooper", "owen.cooper@email.com", "+1-555-0129",
     "65 Barton Springs", "Austin", "USA", "Premium", "2024-03-03", 1),
    ("Nora", "Hughes", "nora.hughes@email.com", "+1-555-0130",
     "73 Market Square", "San Jose", "USA", "Gold", "2023-06-25", 1),
    ("Elijah", "Bennett", "elijah.bennett@email.com", "+1-555-0131",
     "19 Forest Park", "Portland", "USA", "Standard", "2024-04-12", 1),
    ("Mila", "Parker", "mila.parker@email.com", "+1-555-0132",
     "245 Uptown Loop", "Charlotte", "USA", "Premium", "2024-06-01", 1),
]

PRODUCTS = [
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
    ("SkyLens Drone", "Hardware", 499.99, "Consumer camera drone"),
    ("ProBeam Projector", "Hardware", 899.99, "Portable 4K projector"),
    ("HomeHub Mini", "Hardware", 129.99, "Compact smart home dock"),
    ("Onsite Setup Visit", "Service", 119.99, "At-home installation appointment"),
    ("Device Protection Plus", "Service", 19.99, "Monthly accidental damage coverage"),
]

ORDER_SPECS = [
    ("ema.johnson@email.com", "CloudSync Pro", "2023-04-10", 1, "Delivered"),
    ("ema.johnson@email.com", "SmartDesk Hub", "2023-06-15", 1, "Delivered"),
    ("ema.johnson@email.com", "TechCare Premium", "2023-07-01", 1, "Active"),
    ("liam.smith@email.com", "SecureVPN Plus", "2023-08-20", 1, "Delivered"),
    ("liam.smith@email.com", "ErgoKey Wireless", "2023-09-12", 2, "Delivered"),
    ("sophia.garcia@email.com", "UltraScreen 27", "2022-12-01", 1, "Delivered"),
    ("sophia.garcia@email.com", "CloudSync Pro", "2023-03-18", 1, "Delivered"),
    ("sophia.garcia@email.com", "TechCare Basic", "2023-05-01", 1, "Active"),
    ("noah.williams@email.com", "DataGuard Backup", "2024-01-15", 1, "Delivered"),
    ("noah.williams@email.com", "PrintMaster X1", "2024-02-20", 1, "Delivered"),
    ("olivia.brown@email.com", "CloudSync Pro", "2023-01-10", 1, "Delivered"),
    ("olivia.brown@email.com", "TechCare Premium", "2023-01-10", 1, "Active"),
    ("olivia.brown@email.com", "UltraScreen 27", "2023-11-25", 1, "Delivered"),
    ("james.davis@email.com", "SecureVPN Plus", "2022-06-14", 1, "Delivered"),
    ("james.davis@email.com", "SmartDesk Hub", "2022-09-30", 1, "Delivered"),
    ("isabella.martinez@email.com", "QuickSetup Service", "2024-03-01", 1, "Completed"),
    ("isabella.martinez@email.com", "ErgoKey Wireless", "2024-03-05", 1, "Delivered"),
    ("lucas.anderson@email.com", "CloudSync Pro", "2023-02-14", 1, "Delivered"),
    ("lucas.anderson@email.com", "DataGuard Backup", "2023-04-22", 1, "Delivered"),
    ("mia.taylor@email.com", "TechCare Basic", "2024-01-01", 1, "Cancelled"),
    ("ethan.thomas@email.com", "TechCare Premium", "2022-09-01", 1, "Active"),
    ("ethan.thomas@email.com", "UltraScreen 27", "2022-10-15", 2, "Delivered"),
    ("emma.carter@email.com", "SmartDesk Hub", _date_days_ago(16), 1, "Delivered"),
    ("emma.carter@email.com", "CloudSync Pro", _date_days_ago(220), 1, "Delivered"),
    ("emma.collins@email.com", "SkyLens Drone", _date_days_ago(8), 1, "Delivered"),
    ("emma.collins@email.com", "TechCare Premium", _date_days_ago(120), 1, "Active"),
    ("emma.collins@email.com", "ProBeam Projector", _date_days_ago(180), 1, "Delivered"),
    ("liam.johnson@email.com", "Onsite Setup Visit", _date_days_ago(5), 1, "Completed"),
    ("liam.johnson@email.com", "SecureVPN Plus", _date_days_ago(35), 1, "Delivered"),
    ("liam.johnson@email.com", "CloudSync Pro", _date_days_ago(200), 1, "Delivered"),
    ("ava.chen@email.com", "ErgoKey Wireless", _date_days_ago(10), 1, "Delivered"),
    ("ava.chen@email.com", "CloudSync Pro", _date_days_ago(60), 1, "Delivered"),
    ("ava.chen@email.com", "TechCare Basic", _date_days_ago(150), 1, "Completed"),
    ("zoe.kim@email.com", "ProBeam Projector", _date_days_ago(2), 1, "Delivered"),
    ("zoe.kim@email.com", "SmartDesk Hub", _date_days_ago(120), 1, "Delivered"),
    ("zoe.kim@email.com", "Device Protection Plus", _date_days_ago(2), 1, "Active"),
    ("mason.patel@email.com", "ProBeam Projector", _date_days_ago(12), 1, "Delivered"),
    ("mason.patel@email.com", "DataGuard Backup", _date_days_ago(250), 1, "Delivered"),
    ("mason.patel@email.com", "SecureVPN Plus", _date_days_ago(110), 1, "Delivered"),
    ("amelia.wilson@email.com", "TechCare Basic", _date_days_ago(45), 1, "Active"),
    ("amelia.wilson@email.com", "QuickSetup Service", _date_days_ago(70), 1, "Completed"),
    ("daniel.lee@email.com", "Device Protection Plus", _date_days_ago(3), 1, "Cancelled"),
    ("daniel.lee@email.com", "HomeHub Mini", _date_days_ago(140), 1, "Delivered"),
    ("daniel.lee@email.com", "TechCare Basic", _date_days_ago(210), 1, "Cancelled"),
    ("grace.nguyen@email.com", "SkyLens Drone", _date_days_ago(40), 1, "Delivered"),
    ("grace.nguyen@email.com", "UltraScreen 27", _date_days_ago(400), 1, "Delivered"),
    ("grace.nguyen@email.com", "CloudSync Pro", _date_days_ago(510), 1, "Delivered"),
    ("henry.walker@email.com", "HomeHub Mini", _date_days_ago(14), 1, "Delivered"),
    ("henry.walker@email.com", "CloudSync Pro", _date_days_ago(75), 1, "Delivered"),
    ("henry.walker@email.com", "PrintMaster X1", _date_days_ago(240), 1, "Delivered"),
    ("chloe.adams@email.com", "CloudSync Pro", _date_days_ago(1), 1, "Delivered"),
    ("chloe.adams@email.com", "HomeHub Mini", _date_days_ago(33), 1, "Delivered"),
    ("ella.rivera@email.com", "TechCare Premium", _date_days_ago(27), 1, "Active"),
    ("ella.rivera@email.com", "HomeHub Mini", _date_days_ago(32), 1, "Delivered"),
    ("jack.turner@email.com", "SmartDesk Hub", _date_days_ago(29), 1, "Delivered"),
    ("jack.turner@email.com", "Onsite Setup Visit", _date_days_ago(29), 1, "Completed"),
    ("avery.brooks@email.com", "UltraScreen 27", _date_days_ago(46), 1, "Delivered"),
    ("avery.brooks@email.com", "SkyLens Drone", _date_days_ago(200), 1, "Delivered"),
    ("samuel.reed@email.com", "SecureVPN Plus", _date_days_ago(90), 1, "Delivered"),
    ("samuel.reed@email.com", "TechCare Premium", _date_days_ago(130), 1, "Active"),
    ("layla.flores@email.com", "PrintMaster X1", _date_days_ago(18), 1, "Delivered"),
    ("layla.flores@email.com", "QuickSetup Service", _date_days_ago(90), 1, "Completed"),
    ("owen.cooper@email.com", "Device Protection Plus", _date_days_ago(7), 1, "Active"),
    ("owen.cooper@email.com", "ErgoKey Wireless", _date_days_ago(21), 1, "Delivered"),
    ("nora.hughes@email.com", "SkyLens Drone", _date_days_ago(13), 1, "Delivered"),
    ("nora.hughes@email.com", "CloudSync Pro", _date_days_ago(300), 1, "Delivered"),
    ("elijah.bennett@email.com", "HomeHub Mini", _date_days_ago(4), 1, "Delivered"),
    ("elijah.bennett@email.com", "SecureVPN Plus", _date_days_ago(65), 1, "Delivered"),
    ("mila.parker@email.com", "QuickSetup Service", _date_days_ago(6), 1, "Completed"),
    ("mila.parker@email.com", "Device Protection Plus", _date_days_ago(45), 1, "Active"),
]

TICKET_SPECS = [
    ("ema.johnson@email.com", "Unable to sync files",
     "CloudSync Pro is not syncing my files across devices. Getting error code CS-401.",
     "Technical", "High", "Resolved",
     "2023-05-12 09:30:00", "2023-05-12 14:45:00",
     "Reset sync token and cleared cache. Issue resolved.", "Agent Mike"),
    ("ema.johnson@email.com", "Billing inquiry",
     "I was charged twice for my TechCare Premium subscription this month.",
     "Billing", "Medium", "Resolved",
     "2023-08-03 11:00:00", "2023-08-04 10:30:00",
     "Duplicate charge confirmed and refunded $24.99.", "Agent Sarah"),
    ("ema.johnson@email.com", "SmartDesk Hub not recognized",
     "My new SmartDesk Hub is not being detected by my laptop.",
     "Technical", "High", "Resolved",
     "2023-06-20 15:20:00", "2023-06-21 09:00:00",
     "Updated USB-C drivers. Hub now recognized.", "Agent Mike"),
    ("liam.smith@email.com", "VPN connection drops",
     "SecureVPN Plus keeps disconnecting every 10 minutes.",
     "Technical", "High", "Open",
     "2023-09-25 08:15:00", None, None, "Agent Tom"),
    ("liam.smith@email.com", "Keyboard key stuck",
     "The E key on my ErgoKey Wireless sometimes does not register.",
     "Hardware", "Low", "Open",
     "2023-10-01 13:45:00", None, None, "Agent Sarah"),
    ("sophia.garcia@email.com", "Monitor flickering",
     "UltraScreen 27 flickers intermittently at 4K resolution.",
     "Hardware", "High", "Resolved",
     "2023-01-15 10:00:00", "2023-01-17 16:30:00",
     "Firmware update v2.1 applied. Flickering stopped.", "Agent Tom"),
    ("sophia.garcia@email.com", "Request feature - dark mode",
     "Would love a dark mode option in CloudSync Pro.",
     "Feature Request", "Low", "Closed",
     "2023-04-02 17:30:00", "2023-04-05 09:00:00",
     "Forwarded to product team. Dark mode planned for Q3.", "Agent Mike"),
    ("noah.williams@email.com", "Backup restore failed",
     "DataGuard Backup restore failed midway with error DG-503.",
     "Technical", "Critical", "Resolved",
     "2024-02-01 07:00:00", "2024-02-01 12:00:00",
     "Corrupt backup index rebuilt. Full restore completed.", "Agent Sarah"),
    ("noah.williams@email.com", "Printer paper jam",
     "PrintMaster X1 keeps jamming on standard A4 paper.",
     "Hardware", "Medium", "Open",
     "2024-03-10 14:20:00", None, None, "Agent Tom"),
    ("olivia.brown@email.com", "Subscription cancellation",
     "I want to cancel my TechCare Premium plan.",
     "Billing", "Medium", "Resolved",
     "2023-12-01 09:00:00", "2023-12-02 11:00:00",
     "Customer retained with 20% discount offer for 3 months.", "Agent Sarah"),
    ("olivia.brown@email.com", "Monitor dead pixel",
     "Found a dead pixel on my new UltraScreen 27.",
     "Hardware", "Medium", "Open",
     "2024-01-05 16:00:00", None, None, "Agent Mike"),
    ("james.davis@email.com", "VPN slow speeds",
     "SecureVPN Plus gives very slow speeds on US servers.",
     "Technical", "Medium", "Resolved",
     "2022-08-10 12:30:00", "2022-08-11 15:00:00",
     "Switched to optimized server pool. Speeds improved 3x.", "Agent Tom"),
    ("isabella.martinez@email.com", "Setup assistance needed",
     "Need help setting up my new ErgoKey Wireless with my Mac.",
     "Technical", "Low", "Resolved",
     "2024-03-06 10:00:00", "2024-03-06 10:45:00",
     "Guided through Bluetooth pairing. Connected successfully.", "Agent Mike"),
    ("lucas.anderson@email.com", "CloudSync data loss concern",
     "Some files appear missing after the last CloudSync Pro update.",
     "Technical", "Critical", "Resolved",
     "2023-05-01 08:00:00", "2023-05-01 18:00:00",
     "Files recovered from versioning. Rolled back to previous stable release.", "Agent Sarah"),
    ("mia.taylor@email.com", "Refund request",
     "I want a refund for TechCare Basic as I am closing my account.",
     "Billing", "Medium", "Resolved",
     "2024-01-15 11:30:00", "2024-01-16 09:00:00",
     "Prorated refund of $6.66 issued. Account marked for closure.", "Agent Tom"),
    ("ethan.thomas@email.com", "Dual monitor setup help",
     "Need help configuring dual UltraScreen 27 monitors on Windows.",
     "Technical", "Low", "Resolved",
     "2022-11-01 14:00:00", "2022-11-01 15:30:00",
     "Configured display settings and refresh rates. Both working at 4K.", "Agent Mike"),
    ("emma.carter@email.com", "Return window clarification",
     "I think my SmartDesk Hub is just outside the standard return window. Can support confirm?",
     "Billing", "Medium", "Open",
     _timestamp_days_ago(7, 10, 15), None, None, "Agent Sarah"),
    ("emma.collins@email.com", "Drone battery concern",
     "The SkyLens Drone battery drains too quickly after only a few flights.",
     "Hardware", "High", "Open",
     _timestamp_days_ago(3, 14, 0), None, None, "Agent Tom"),
    ("liam.johnson@email.com", "Setup visit refund question",
     "Can a completed Onsite Setup Visit still be refunded if I was not satisfied?",
     "Billing", "Medium", "Open",
     _timestamp_days_ago(2, 9, 30), None, None, "Agent Sarah"),
    ("ava.chen@email.com", "Keyboard return label request",
     "Please send return instructions for my recent ErgoKey Wireless order.",
     "Billing", "Low", "Resolved",
     _timestamp_days_ago(1, 11, 0), _timestamp_days_ago(1, 15, 10),
     "Provided prepaid shipping instructions and return steps.", "Agent Mike"),
    ("harper.allen@email.com", "Billing address update",
     "Please update the billing address on my profile before my next renewal.",
     "Billing", "Low", "Closed",
     _timestamp_days_ago(40, 13, 0), _timestamp_days_ago(39, 9, 30),
     "Address verified and updated.", "Agent Tom"),
    ("mason.patel@email.com", "Projector restocking fee question",
     "Will there be a restocking fee if I return the ProBeam Projector?",
     "Billing", "Medium", "Open",
     _timestamp_days_ago(6, 10, 45), None, None, "Agent Sarah"),
    ("daniel.lee@email.com", "Cancellation confirmation",
     "Please confirm that my Device Protection Plus cancellation went through.",
     "Billing", "Low", "Resolved",
     _timestamp_days_ago(2, 8, 10), _timestamp_days_ago(2, 12, 40),
     "Cancellation confirmed and no further charges scheduled.", "Agent Mike"),
    ("grace.nguyen@email.com", "Drone missing propeller",
     "My SkyLens Drone arrived missing a propeller and cannot be used safely.",
     "Hardware", "High", "Resolved",
     _timestamp_days_ago(30, 16, 15), _timestamp_days_ago(29, 10, 0),
     "Replacement parts shipped overnight.", "Agent Tom"),
    ("chloe.adams@email.com", "First-time setup question",
     "I just bought CloudSync Pro and need help getting started.",
     "Technical", "Low", "Open",
     _timestamp_days_ago(1, 9, 0), None, None, "Agent Mike"),
    ("nora.hughes@email.com", "Multiple damaged deliveries",
     "My recent hardware order arrived damaged and I need immediate help.",
     "Hardware", "Critical", "Open",
     _timestamp_days_ago(2, 7, 20), None, None, "Agent Sarah"),
    ("samuel.reed@email.com", "Privacy data export request",
     "How can I request access to all personal data tied to my account?",
     "Billing", "Low", "Resolved",
     _timestamp_days_ago(15, 10, 0), _timestamp_days_ago(14, 14, 30),
     "Sent the privacy-request workflow and expected response timeline.", "Agent Mike"),
    ("owen.cooper@email.com", "Protection plan billing question",
     "I need clarification on the first charge for Device Protection Plus.",
     "Billing", "Medium", "Open",
     _timestamp_days_ago(5, 12, 20), None, None, "Agent Tom"),
    ("elijah.bennett@email.com", "HomeHub Mini arrival damage",
     "My HomeHub Mini arrived with a cracked side panel.",
     "Hardware", "High", "Open",
     _timestamp_days_ago(3, 11, 25), None, None, "Agent Sarah"),
    ("mila.parker@email.com", "Service invoice dispute",
     "The invoice for my setup service looks higher than expected.",
     "Billing", "Medium", "Open",
     _timestamp_days_ago(4, 15, 5), None, None, "Agent Mike"),
]


def create_tables(cursor: sqlite3.Cursor) -> None:
    cursor.executescript(
        """
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
        """
    )


def seed_data(cursor: sqlite3.Cursor) -> None:
    cursor.executemany(
        "INSERT INTO customers "
        "(first_name, last_name, email, phone, address, city, country, "
        "membership_tier, account_created, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        CUSTOMERS,
    )

    cursor.executemany(
        "INSERT INTO products "
        "(product_name, category, price, description) "
        "VALUES (?, ?, ?, ?)",
        PRODUCTS,
    )

    cursor.execute("SELECT customer_id, email FROM customers")
    customer_ids = {email: customer_id for customer_id, email in cursor.fetchall()}

    cursor.execute("SELECT product_id, product_name, price FROM products")
    product_lookup = {
        product_name: {"product_id": product_id, "price": price}
        for product_id, product_name, price in cursor.fetchall()
    }

    orders = []
    for email, product_name, order_date, quantity, status in ORDER_SPECS:
        product = product_lookup[product_name]
        orders.append(
            (
                customer_ids[email],
                product["product_id"],
                order_date,
                quantity,
                round(product["price"] * quantity, 2),
                status,
            )
        )

    cursor.executemany(
        "INSERT INTO orders "
        "(customer_id, product_id, order_date, quantity, total_amount, status) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        orders,
    )

    tickets = []
    for (
        email,
        subject,
        description,
        category,
        priority,
        status,
        created_at,
        resolved_at,
        resolution_notes,
        assigned_agent,
    ) in TICKET_SPECS:
        tickets.append(
            (
                customer_ids[email],
                subject,
                description,
                category,
                priority,
                status,
                created_at,
                resolved_at,
                resolution_notes,
                assigned_agent,
            )
        )

    cursor.executemany(
        "INSERT INTO support_tickets "
        "(customer_id, subject, description, category, priority, status, "
        "created_at, resolved_at, resolution_notes, assigned_agent) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        tickets,
    )


def init_database(reset: bool = True) -> str:
    """Create and populate the database with a fresh deterministic seed."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

    if reset:
        for path in (DB_PATH, f"{DB_PATH}-journal"):
            if os.path.exists(path):
                os.remove(path)

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        create_tables(cursor)
        seed_data(cursor)
        conn.commit()
    finally:
        conn.close()

    print(f"Database initialized at {DB_PATH}")
    return DB_PATH


if __name__ == "__main__":
    init_database()
