from app.database.session import SessionLocal
from app.models.shipment import Shipment

from .shipments import ShipmentGenerator


def seed_shipments(total=200):

    db = SessionLocal()

    generator = ShipmentGenerator()

    try:

        for i in range(1, total + 1):

            shipment = Shipment(
                **generator.generate(i)
            )

            db.add(shipment)

        db.commit()

        print(f"✅ {total} shipments inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()