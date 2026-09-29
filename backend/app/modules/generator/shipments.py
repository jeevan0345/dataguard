import random

from faker import Faker

from app.database.session import SessionLocal
from app.models.order import Order
from app.enums.shipment_status import ShipmentStatus

from .base_generator import BaseGenerator

fake = Faker()


class ShipmentGenerator(BaseGenerator):

    CARRIERS = [
        "BlueDart",
        "DTDC",
        "Delhivery",
        "FedEx",
        "DHL",
        "India Post",
        "UPS"
    ]

    def __init__(self):

        db = SessionLocal()

        self.orders = db.query(Order).all()

        db.close()

        random.shuffle(self.orders)

        self.index = 0

    def generate(self, number):

        if self.index >= len(self.orders):
            raise Exception("No more orders available.")

        order = self.orders[self.index]

        self.index += 1

        shipped_date = fake.date_between(
            start_date=order.order_date,
            end_date="today"
        )

        delivered_date = fake.date_between(
            start_date=shipped_date,
            end_date="today"
        )

        return {

            "shipment_number": f"SHP{number:08d}",

            "order_id": order.id,

            "carrier": random.choice(self.CARRIERS),

            "tracking_number": f"TRK{fake.unique.random_number(digits=12)}",

            "shipment_status": random.choice(
                list(ShipmentStatus)
            ).value,

            "shipped_date": shipped_date,

            "delivered_date": delivered_date

        }