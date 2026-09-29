import random

from faker import Faker

from app.database.session import SessionLocal
from app.models.order import Order
from app.enums.payment_status import PaymentStatus

from .base_generator import BaseGenerator

fake = Faker()


class PaymentGenerator(BaseGenerator):

    PAYMENT_METHODS = [
        "Credit Card",
        "Debit Card",
        "UPI",
        "Net Banking",
        "Cash",
        "Bank Transfer"
    ]

    def __init__(self):

        db = SessionLocal()

        self.orders = db.query(Order).all()

        db.close()

    def generate(self, index):

        order = random.choice(self.orders)

        return {

            "payment_reference": f"PAY{index:08d}",

            "order_id": order.id,

            "payment_method": random.choice(
                self.PAYMENT_METHODS
            ),

            "payment_status": random.choice(
                list(PaymentStatus)
            ).value,

            "amount": order.total_amount,

            "payment_date": fake.date_between(
                start_date=order.order_date,
                end_date="today"
            ),

            "transaction_id": f"TXN{fake.unique.random_number(digits=10)}"

        }