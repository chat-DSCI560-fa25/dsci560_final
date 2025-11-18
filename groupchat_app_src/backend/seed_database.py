"""
Seed script to populate database with sample STEM center inventory data.
Run this after setting up the database to get started quickly.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from db import SessionLocal, init_db, InventoryItem, Supplier, InventoryTransaction, User
from auth import get_password_hash


async def seed_database():
    """
    Populate database with realistic STEM center inventory data.
    """
    print("🌱 Seeding database with sample data...\n")
    
    # Initialize database
    await init_db()
    
    async with SessionLocal() as session:
        # Create admin user if not exists
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123")
        )
        session.add(admin)
        
        teacher1 = User(
            username="teacher1",
            password_hash=get_password_hash("password123")
        )
        session.add(teacher1)
        
        try:
            await session.commit()
            print("✅ Created admin and teacher1 users")
        except:
            await session.rollback()
            print("ℹ️  Users already exist")
        
        # Sample Inventory Items
        inventory_items = [
            # Stationery
            InventoryItem(
                name="Pencils",
                category="Stationery",
                description="Standard HB pencils for general use",
                quantity=150.0,
                unit="pieces",
                min_quantity=50.0,
                location="Storage Room A"
            ),
            InventoryItem(
                name="Markers",
                category="Stationery",
                description="Dry-erase markers for whiteboards",
                quantity=8.0,
                unit="boxes",
                min_quantity=15.0,  # Low stock!
                location="Storage Room A"
            ),
            InventoryItem(
                name="Notebooks",
                category="Stationery",
                description="Lined composition notebooks",
                quantity=45.0,
                unit="units",
                min_quantity=20.0,
                location="Storage Room A"
            ),
            
            # Lab Equipment
            InventoryItem(
                name="Beakers (250ml)",
                category="Lab Equipment",
                description="Glass beakers for chemistry experiments",
                quantity=25.0,
                unit="pieces",
                min_quantity=30.0,  # Low stock!
                location="Chemistry Lab Cabinet"
            ),
            InventoryItem(
                name="Test Tubes",
                category="Lab Equipment",
                description="Borosilicate glass test tubes",
                quantity=100.0,
                unit="pieces",
                min_quantity=50.0,
                location="Chemistry Lab Cabinet"
            ),
            InventoryItem(
                name="Microscopes",
                category="Lab Equipment",
                description="Student-grade compound microscopes",
                quantity=12.0,
                unit="units",
                min_quantity=15.0,  # Low stock!
                location="Biology Lab"
            ),
            InventoryItem(
                name="Safety Goggles",
                category="Lab Equipment",
                description="Protective eyewear for lab work",
                quantity=35.0,
                unit="pairs",
                min_quantity=40.0,  # Low stock!
                location="Lab Entrance"
            ),
            InventoryItem(
                name="Chemistry Sets",
                category="Lab Equipment",
                description="Complete chemistry experiment kits",
                quantity=8.0,
                unit="sets",
                min_quantity=5.0,
                location="Chemistry Lab"
            ),
            
            # Electronics
            InventoryItem(
                name="Arduino Uno Kits",
                category="Electronics",
                description="Arduino microcontroller starter kits",
                quantity=15.0,
                unit="kits",
                min_quantity=10.0,
                location="Robotics Lab"
            ),
            InventoryItem(
                name="Raspberry Pi 4",
                category="Electronics",
                description="Single-board computers for projects",
                quantity=10.0,
                unit="units",
                min_quantity=8.0,
                location="Computer Lab"
            ),
            InventoryItem(
                name="Breadboards",
                category="Electronics",
                description="Solderless breadboards for prototyping",
                quantity=30.0,
                unit="pieces",
                min_quantity=15.0,
                location="Robotics Lab"
            ),
            InventoryItem(
                name="LED Assortment",
                category="Electronics",
                description="Various colored LEDs",
                quantity=200.0,
                unit="pieces",
                min_quantity=100.0,
                location="Electronics Storage"
            ),
            InventoryItem(
                name="Jumper Wires",
                category="Electronics",
                description="Male-to-male jumper wires",
                quantity=5.0,
                unit="packs",
                min_quantity=10.0,  # Low stock!
                location="Electronics Storage"
            ),
            
            # Tools
            InventoryItem(
                name="Screwdriver Sets",
                category="Tools",
                description="Multi-bit screwdriver sets",
                quantity=8.0,
                unit="sets",
                min_quantity=5.0,
                location="Tool Cabinet"
            ),
            InventoryItem(
                name="Multimeters",
                category="Tools",
                description="Digital multimeters for electrical testing",
                quantity=12.0,
                unit="units",
                min_quantity=10.0,
                location="Electronics Lab"
            ),
            InventoryItem(
                name="Hot Glue Guns",
                category="Tools",
                description="Hot glue guns with glue sticks",
                quantity=6.0,
                unit="units",
                min_quantity=4.0,
                location="Makerspace"
            ),
        ]
        
        print("📦 Adding inventory items...")
        for item in inventory_items:
            session.add(item)
        
        await session.commit()
        print(f"✅ Added {len(inventory_items)} inventory items\n")
        
        # Refresh items to get their IDs
        for item in inventory_items:
            await session.refresh(item)
        
        # Add initial transactions
        print("📝 Creating transaction history...")
        for item in inventory_items:
            trans = InventoryTransaction(
                item_id=item.id,
                transaction_type="add",
                quantity_change=item.quantity,
                quantity_after=item.quantity,
                user_id=None,
                reason="Initial inventory setup"
            )
            session.add(trans)
        
        await session.commit()
        print("✅ Transaction history created\n")
        
        # Sample Suppliers
        suppliers = [
            Supplier(
                name="School Supply Co",
                item_name="Pencils",
                contact_info="orders@schoolsupply.com",
                order_url="https://schoolsupply.com/products/pencils",
                price_per_unit=0.25,
                lead_time_days=3,
                notes="Bulk discounts available for orders over 500"
            ),
            Supplier(
                name="Lab Pro Direct",
                item_name="Beakers",
                contact_info="sales@labpro.com",
                order_url="https://labpro.com/glassware/beakers-250ml",
                price_per_unit=4.99,
                lead_time_days=5,
                notes="Borosilicate glass, autoclavable"
            ),
            Supplier(
                name="Lab Pro Direct",
                item_name="Test Tubes",
                contact_info="sales@labpro.com",
                order_url="https://labpro.com/glassware/test-tubes",
                price_per_unit=0.75,
                lead_time_days=5,
                notes="Sold in packs of 50"
            ),
            Supplier(
                name="Lab Pro Direct",
                item_name="Safety Goggles",
                contact_info="sales@labpro.com",
                order_url="https://labpro.com/safety/goggles",
                price_per_unit=3.50,
                lead_time_days=5,
                notes="ANSI Z87.1 certified"
            ),
            Supplier(
                name="TechEd Supplies",
                item_name="Arduino",
                contact_info="info@techedsupplies.com",
                order_url="https://techedsupplies.com/arduino-uno-starter",
                price_per_unit=35.99,
                lead_time_days=7,
                notes="Includes USB cable and starter components"
            ),
            Supplier(
                name="Amazon Business",
                item_name="Arduino",
                contact_info="business@amazon.com",
                order_url="https://amazon.com/business/arduino-kits",
                price_per_unit=32.99,
                lead_time_days=2,
                notes="Prime shipping available"
            ),
            Supplier(
                name="TechEd Supplies",
                item_name="Raspberry Pi",
                contact_info="info@techedsupplies.com",
                order_url="https://techedsupplies.com/raspberry-pi-4",
                price_per_unit=55.00,
                lead_time_days=7,
                notes="8GB RAM model"
            ),
            Supplier(
                name="EduMart",
                item_name="Markers",
                contact_info="orders@edumart.com",
                order_url="https://edumart.com/markers-dry-erase",
                price_per_unit=8.99,
                lead_time_days=3,
                notes="12-pack assorted colors"
            ),
            Supplier(
                name="Science Direct",
                item_name="Microscopes",
                contact_info="sales@sciencedirect.com",
                order_url="https://sciencedirect.com/microscopes/student",
                price_per_unit=149.99,
                lead_time_days=10,
                notes="40x-1000x magnification, LED illumination"
            ),
            Supplier(
                name="Maker Supply Hub",
                item_name="Jumper Wires",
                contact_info="hello@makersupply.com",
                order_url="https://makersupply.com/jumper-wires",
                price_per_unit=5.99,
                lead_time_days=4,
                notes="Pack of 100 wires, 20cm length"
            ),
        ]
        
        print("🏪 Adding suppliers...")
        for supplier in suppliers:
            session.add(supplier)
        
        await session.commit()
        print(f"✅ Added {len(suppliers)} suppliers\n")
        
        # Summary
        print("=" * 60)
        print("✨ Database seeding complete!")
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   • {len(inventory_items)} inventory items added")
        print(f"   • {len(suppliers)} suppliers added")
        print(f"   • 2 users created (admin, teacher1)")
        print()
        print("🔑 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("   Username: teacher1")
        print("   Password: password123")
        print()
        
        # Low stock alerts
        low_stock = [item for item in inventory_items if item.quantity <= item.min_quantity]
        if low_stock:
            print("⚠️  Low stock items (to test alerts):")
            for item in low_stock:
                print(f"   • {item.name}: {item.quantity} {item.unit} (min: {item.min_quantity})")
        
        print("\n🚀 Ready to test! Try these queries:")
        print("   • 'How many pencils do we have?'")
        print("   • 'We're running low on markers'")
        print("   • 'Can you order more beakers?'")
        print("   • 'Show me all inventory'")
        print("   • 'What items need restocking?'")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
