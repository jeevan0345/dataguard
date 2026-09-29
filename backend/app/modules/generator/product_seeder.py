from app.database.session import SessionLocal
from app.models.product import Product

from .products import ProductGenerator


def seed_products(total=100):

    db = SessionLocal()

    generator = ProductGenerator()

    try:

        for i in range(1, total + 1):

            product = Product(
                **generator.generate(i)
            )

            db.add(product)

        db.commit()

        print(f"✅ {total} products inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()