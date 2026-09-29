from app.database.session import SessionLocal
from app.models.customer import Customer

from .customers import CustomerGenerator


def seed_customers(total=100):

    db = SessionLocal()

    generator = CustomerGenerator()

    try:

        for i in range(1, total + 1):

            data = generator.generate(i)

            customer = Customer(**data)

            db.add(customer)

        db.commit()

        print(f"✅ {total} customers inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()