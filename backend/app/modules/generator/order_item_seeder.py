from app.database.session import SessionLocal
from app.models.order_item import OrderItem

from .order_items import OrderItemGenerator


def seed_order_items(total=500):

    db = SessionLocal()

    generator = OrderItemGenerator()

    try:

        for _ in range(total):

            item = OrderItem(
                **generator.generate()
            )

            db.add(item)

        db.commit()

        print(f"✅ {total} order items inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()