from app.database.session import SessionLocal
from app.models.employee import Employee

from .employees import EmployeeGenerator


def seed_employees(total=100):

    db = SessionLocal()

    generator = EmployeeGenerator()

    try:

        for i in range(1, total + 1):

            employee = Employee(
                **generator.generate(i)
            )

            db.add(employee)

        db.commit()

        print(f"✅ {total} employees inserted successfully!")

    except Exception as e:

        db.rollback()

        print(f"❌ Error: {e}")

        raise

    finally:

        db.close()