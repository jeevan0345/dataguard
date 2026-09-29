from .reset_database import reset_database

from .customer_seeder import seed_customers
from .supplier_seeder import seed_suppliers
from .warehouse_seeder import seed_warehouses
from .product_seeder import seed_products
from .inventory_seeder import seed_inventory


def seed_all():

    print("\n========================================")
    print("      DATAGUARD ENTERPRISE SEEDER")
    print("========================================\n")

    print("Step 1 : Resetting Database")
    reset_database()

    print("\nStep 2 : Generating Customers")
    seed_customers(50)

    print("\nStep 3 : Generating Suppliers")
    seed_suppliers(30)

    print("\nStep 4 : Generating Warehouses")
    seed_warehouses(20)

    print("\nStep 5 : Generating Products")
    seed_products(100)

    print("\nStep 6 : Generating Inventory")
    seed_inventory(200)

    print("\n========================================")
    print("Enterprise Dataset Generated Successfully!")
    print("========================================")


if __name__ == "__main__":
    seed_all()