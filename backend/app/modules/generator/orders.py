import random
from faker import Faker

from app.database.session import SessionLocal
from app.models.customer import Customer

from app.enums.order_status import OrderStatus

from .base_generator import BaseGenerator

fake = Faker()


class OrderGenerator(BaseGenerator):

    PAYMENT_STATUS = [
        "Pending",
        "Paid",
        "Partially Paid"
    ]

    def __init__(self):

        db = SessionLocal()

        self.customers = db.query(Customer).all()

        db.close()

    def generate(self, index):

        customer = random.choice(self.customers)

        total = round(
            random.uniform(500, 100000),
            2
        )

        return {

            "order_number": f"ORD{index:08d}",

            "customer_id": customer.id,

            "order_date": fake.date_between(
                start_date="-2y",
                end_date="today"
            ),

            "total_amount": total,

            "order_status": random.choice(
                list(OrderStatus)
            ).value,

            "payment_status": random.choice(
                self.PAYMENT_STATUS
            )

        }