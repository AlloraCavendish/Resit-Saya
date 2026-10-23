# Purpose: Administrative CLI for system bootstrapping, demo seeding, and manual retention purging.
# Security: Enforces Argon2 password hashing on admin creation and verifies input requirements.

import argparse
import getpass
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models.category import Category
from app.models.receipt import Receipt
from app.models.user import User
from app.security.passwords import hash_password
from app.services.audit import log_audit_event
from app.services.purge import purge_expired_deleted_receipts
from app.services.receipt_service import seed_default_categories


def create_admin():
    parser = argparse.ArgumentParser(description="Create an initial administrator account.")
    parser.add_argument("--username", help="Administrator username")
    parser.add_argument("--email", help="Administrator email")
    parser.add_argument("--password", help="Administrator password (optional, prompted if omitted)")
    args = parser.parse_args(sys.argv[2:])

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    username = args.username or input("Enter administrator username: ").strip()
    if not username:
        print("Error: Username is required.")
        sys.exit(1)

    email = args.email or input("Enter administrator email: ").strip()
    if not email:
        print("Error: Email is required.")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass("Enter administrator password (min 10 chars): ")
        password_confirm = getpass.getpass("Confirm administrator password: ")
        if password != password_confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)

    if len(password) < 10:
        print("Error: Password must be at least 10 characters long.")
        sys.exit(1)

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(
            (User.username == username.lower()) | (User.email == email.lower())
        ).first()
        if existing:
            print(f"Error: User with username '{username}' or email '{email}' already exists.")
            sys.exit(1)

        admin_user = User(
            username=username.lower(),
            email=email.lower(),
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
            must_change_password=False,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        seed_default_categories(db, admin_user.id)
        log_audit_event(
            db=db,
            event="user_created",
            user_id=admin_user.id,
            detail=f"Admin account '{admin_user.username}' created via CLI",
        )
        print(f"Administrator account '{admin_user.username}' created successfully (ID: {admin_user.id}).")
    finally:
        db.close()


def purge_deleted():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        print("Executing manual retention purge...")
        count = purge_expired_deleted_receipts(db)
        print(f"Purge completed successfully. Permanently deleted {count} expired receipts and files.")
    finally:
        db.close()


def seed_demo():
    """Create a demo user account populated with ~30 sample receipts across 3 months."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        demo_username = "demo"
        demo_email = "demo@example.com"
        demo_pass = "demopassword123"

        user = db.query(User).filter(User.username == demo_username).first()
        if not user:
            user = User(
                username=demo_username,
                email=demo_email,
                password_hash=hash_password(demo_pass),
                role="user",
                is_active=True,
                must_change_password=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created demo user: {demo_username} (password: {demo_pass})")
        else:
            print(f"Demo user '{demo_username}' already exists. Refreshing sample receipts...")

        seed_default_categories(db, user.id)
        categories = db.query(Category).filter(Category.user_id == user.id).all()
        cat_by_name = {c.name: c.id for c in categories}

        # Clear previous receipts for demo user to ensure clean seed
        db.query(Receipt).filter(Receipt.user_id == user.id).delete()
        db.commit()

        # Generate ~30 sample expenses across today, last month, and two months ago
        today = date.today()

        sample_data = [
            # Food & Drinks
            ("Kopitiam Ah Kow", "Food & Drinks", 1450, 1450, None, "Kaya toast and kopi C peng", 2),
            ("Nasi Kandar Pelita", "Food & Drinks", 2200, 4400, "Amir", "Mamak dinner, split with Amir", 5),
            ("Starbucks Reserve The Gardens", "Food & Drinks", 2650, 2650, None, "Cold brew with oat milk", 8),
            ("Restoran Rebung Chef Ismail", "Food & Drinks", 5500, 16500, "Colleagues (3 pax)", "Team lunch", 14),
            ("FamilyMart KL Sentral", "Food & Drinks", 1280, 1280, None, "Oden and matcha soft serve", 18),
            ("Din Tai Fung Pavilion", "Food & Drinks", 4200, 12600, "Sarah, Ken", "Dim sum dinner split equally", 25),
            ("Village Park Restaurant", "Food & Drinks", 1600, 1600, None, "Nasi lemak ayam goreng", 34),
            ("McDonald's Bangsar", "Food & Drinks", 1850, 1850, None, "Spicy chicken McValue meal", 42),
            ("Kyochon 1991 One Utama", "Food & Drinks", 3200, 6400, "Hafiz", "Korean fried chicken", 55),
            ("Sushi Zanmai Mid Valley", "Food & Drinks", 3800, 7600, "Adib", "Weekend sushi lunch", 70),

            # Groceries
            ("Village Grocer Bangsar", "Groceries", 8740, 8740, None, "Weekly fresh produce and milk", 3),
            ("Jaya Grocer Starling", "Groceries", 6520, 6520, None, "Baking supplies & fruits", 19),
            ("Lotus's Kepong", "Groceries", 14250, 14250, None, "Monthly household essentials", 38),
            ("Qra Arcoris Mont Kiara", "Groceries", 5120, 5120, None, "Artisan bread and cheese", 62),

            # Transport
            ("Grab Ride to KLCC", "Transport", 2400, 2400, None, "Meeting in city centre", 1),
            ("MRT RapidKL Monthly Pass", "Transport", 5000, 5000, None, "My50 public transport pass", 10),
            ("Petronas Fuel Jalan Maarof", "Transport", 6000, 6000, None, "RON95 full tank", 21),
            ("Touch 'n Go RFID Reload", "Transport", 5000, 5000, None, "Highway toll e-wallet reload", 36),
            ("Shell Fuel Damansara", "Transport", 6500, 6500, None, "Full tank petrol", 50),
            ("Grab Ride KLIA to Home", "Transport", 7500, 7500, None, "Airport ride after return", 78),

            # Shopping
            ("Uniqlo Mid Valley", "Shopping", 14900, 14900, None, "AIRism shirts and work trousers", 7),
            ("Decathlon Petaling Jaya", "Shopping", 8900, 8900, None, "Running shoes & water bottle", 29),
            ("Shopee Online Order", "Shopping", 4350, 4350, None, "USB-C charging cables", 48),
            ("Muji Pavilion", "Shopping", 6200, 6200, None, "Notebooks and acrylic organizers", 65),

            # Bills & Utilities
            ("Tenaga Nasional Berhad", "Bills & Utilities", 16850, 16850, None, "Electricity bill September", 6),
            ("TM Unifi 300Mbps Fibre", "Bills & Utilities", 13900, 13900, None, "Home broadband monthly fee", 12),
            ("Air Selangor", "Bills & Utilities", 1820, 1820, None, "Water utility bill", 24),
            ("Tenaga Nasional Berhad", "Bills & Utilities", 17530, 17530, None, "Electricity bill August", 39),

            # Health
            ("Caring Pharmacy Bangsar", "Health", 3850, 3850, None, "Vitamins and first aid supplies", 16),
            ("Klinik Mediviron Consultation", "Health", 8000, 8000, None, "General checkup & medication", 45),

            # Entertainment
            ("GSC Cinemas Mid Valley", "Entertainment", 2400, 4800, "Danial", "Movie tickets (2 pax)", 11),
            ("Netflix Standard Subscription", "Entertainment", 4490, 4490, None, "Monthly streaming sub", 27),
            ("Board Game Cafe TTDI", "Entertainment", 3000, 9000, "Zul, Chong", "Table fee and snack share", 58),

            # Education & Books
            ("Kinokuniya KLCC", "Education", 9500, 9500, None, "Software engineering books", 15),
            ("Popular Bookstore Sunway", "Education", 3200, 3200, None, "Stationery and pens", 46),
        ]

        now = datetime.now(timezone.utc)
        for merchant, cat_name, my_share, total, shared_with, notes, days_ago in sample_data:
            r_date = today - timedelta(days=days_ago)
            cat_id = cat_by_name.get(cat_name)
            receipt = Receipt(
                user_id=user.id,
                category_id=cat_id,
                merchant=merchant,
                receipt_date=r_date,
                my_share_sen=my_share,
                receipt_total_sen=total,
                currency="MYR",
                shared_with=shared_with,
                notes=notes,
                created_at=now - timedelta(days=days_ago),
            )
            db.add(receipt)

        db.commit()
        print(f"Seeded {len(sample_data)} realistic sample receipts for demo user '{demo_username}'!")
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli [create-admin | seed-demo | purge-deleted]")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command in ("--help", "-h", "help"):
        print("Usage: python -m app.cli [create-admin | seed-demo | purge-deleted]")
        sys.exit(0)
    elif command == "create-admin":
        create_admin()
    elif command == "seed-demo":
        seed_demo()
    elif command == "purge-deleted":
        purge_deleted()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create-admin, seed-demo, purge-deleted")
        sys.exit(1)


if __name__ == "__main__":
    main()
