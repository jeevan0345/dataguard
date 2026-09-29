from app.database.session import SessionLocal
from app.models.warehouse import Warehouse

from .warehouses import WarehouseGenerator


def seed_warehouses(total=20):

    db = SessionLocal()

    generator = WarehouseGenerator()

    try:

        for i in range(1, total + 1):

            warehouse = Warehouse(
                **generator.generate(i)
            )

            db.add(warehouse)

        db.commit()

        print(f"✅ {total} warehouses inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()