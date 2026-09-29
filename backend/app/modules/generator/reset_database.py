from app.database.session import SessionLocal

from app.models.inventory import Inventory
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.supplier import Supplier
from app.models.customer import Customer


def reset_database():

    db = SessionLocal()

    try:

        print("Deleting Inventory...")
        db.query(Inventory).delete()

        print("Deleting Products...")
        db.query(Product).delete()

        print("Deleting Warehouses...")
        db.query(Warehouse).delete()

        print("Deleting Suppliers...")
        db.query(Supplier).delete()

        print("Deleting Customers...")
        db.query(Customer).delete()

        db.commit()

        print("\n✅ Database reset completed!")

    except Exception as e:

        db.rollback()

        print(f"\n❌ Reset failed: {e}")

        raise

    finally:

        db.close()


if __name__ == "__main__":
    reset_database()