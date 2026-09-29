from app.database.session import SessionLocal
from app.models.inventory import Inventory

from .inventory import InventoryGenerator


def seed_inventory(total=200):

    db = SessionLocal()

    generator = InventoryGenerator()

    try:

        for _ in range(total):

            inventory = Inventory(
                **generator.generate()
            )

            db.add(inventory)

        db.commit()

        print(f"✅ {total} inventory records inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()