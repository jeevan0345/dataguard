from app.database.session import SessionLocal
from app.models.order import Order

from .orders import OrderGenerator


def seed_orders(total=200):

    db = SessionLocal()

    generator = OrderGenerator()

    try:

        for i in range(1, total + 1):

            order = Order(
                **generator.generate(i)
            )

            db.add(order)

        db.commit()

        print(f"✅ {total} orders inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()