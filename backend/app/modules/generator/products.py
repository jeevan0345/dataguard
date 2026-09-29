from faker import Faker
import random

from app.database.session import SessionLocal
from app.models.supplier import Supplier

from .base_generator import BaseGenerator

fake = Faker()


class ProductGenerator(BaseGenerator):

    CATEGORIES = {
        "Electronics": [
            "Laptop",
            "Keyboard",
            "Mouse",
            "SSD",
            "Monitor",
            "Router"
        ],
        "Healthcare": [
            "Thermometer",
            "Face Mask",
            "Gloves",
            "Syringe"
        ],
        "Food": [
            "Rice",
            "Coffee",
            "Sugar",
            "Milk Powder"
        ],
        "Automotive": [
            "Engine Oil",
            "Brake Pad",
            "Battery",
            "Air Filter"
        ]
    }

    BRANDS = [
        "TechPro",
        "PrimeTech",
        "VisionX",
        "SmartLife",
        "Elite",
        "PowerMax"
    ]

    def __init__(self):

        db = SessionLocal()

        self.suppliers = db.query(Supplier).all()

        db.close()

    def generate(self, index):

        category = random.choice(list(self.CATEGORIES.keys()))

        product_name = random.choice(
            self.CATEGORIES[category]
        )

        supplier = random.choice(self.suppliers)

        cost = round(random.uniform(100, 2000), 2)

        price = round(cost * random.uniform(1.2, 1.8), 2)

        return {

            "product_code": f"PROD{index:06d}",

            "product_name": product_name,

            "description": fake.sentence(),

            "category": category,

            "brand": random.choice(self.BRANDS),

            "price": price,

            "cost_price": cost,

            "reorder_level": random.randint(10, 100),

            "supplier_id": supplier.id

        }