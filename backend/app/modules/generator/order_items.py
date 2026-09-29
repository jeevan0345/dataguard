import random

from app.database.session import SessionLocal
from app.models.order import Order
from app.models.product import Product

from .base_generator import BaseGenerator


class OrderItemGenerator(BaseGenerator):

    def __init__(self):

        db = SessionLocal()

        self.orders = db.query(Order).all()

        self.products = db.query(Product).all()

        db.close()

    def generate(self):

        order = random.choice(self.orders)

        product = random.choice(self.products)

        quantity = random.randint(1, 10)

        unit_price = product.price

        subtotal = round(
            quantity * unit_price,
            2
        )

        return {

            "order_id": order.id,

            "product_id": product.id,

            "quantity": quantity,

            "unit_price": unit_price,

            "subtotal": subtotal

        }