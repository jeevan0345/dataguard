from app.database.session import SessionLocal
from app.models.payment import Payment

from .payments import PaymentGenerator


def seed_payments(total=200):

    db = SessionLocal()

    generator = PaymentGenerator()

    try:

        for i in range(1, total + 1):

            payment = Payment(
                **generator.generate(i)
            )

            db.add(payment)

        db.commit()

        print(f"✅ {total} payments inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()