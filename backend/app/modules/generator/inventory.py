import random

from app.database.session import SessionLocal
from app.models.product import Product
from app.models.warehouse import Warehouse

from .base_generator import BaseGenerator


class InventoryGenerator(BaseGenerator):

    def __init__(self):

        db = SessionLocal()

        self.products = db.query(Product).all()
        self.warehouses = db.query(Warehouse).all()

        db.close()

    def generate(self):

        product = random.choice(self.products)

        warehouse = random.choice(self.warehouses)

        quantity = random.randint(100, 1000)

        reserved = random.randint(0, quantity // 4)

        available = quantity - reserved

        return {

            "product_id": product.id,

            "warehouse_id": warehouse.id,

            "quantity": quantity,

            "reserved_quantity": reserved,

            "available_quantity": available,

            "minimum_stock": random.randint(20, 100),

            "maximum_stock": random.randint(1000, 5000)

        }