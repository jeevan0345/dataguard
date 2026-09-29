from app.database.session import SessionLocal
from app.models.supplier import Supplier

from .suppliers import SupplierGenerator


def seed_suppliers(total=30):

    db = SessionLocal()

    generator = SupplierGenerator()

    try:

        for i in range(1, total + 1):

            data = generator.generate(i)

            supplier = Supplier(**data)

            db.add(supplier)

        db.commit()

        print(f"✅ {total} suppliers inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()