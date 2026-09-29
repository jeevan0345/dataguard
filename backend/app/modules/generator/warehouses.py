from faker import Faker

from .base_generator import BaseGenerator

fake = Faker()


class WarehouseGenerator(BaseGenerator):

    def generate(self, index):

        return {

            "warehouse_code": f"WH{index:04d}",

            "warehouse_name": f"{fake.city()} Distribution Center",

            "address": fake.street_address(),

            "city": fake.city(),

            "state": fake.state(),

            "country": fake.country(),

            "postal_code": fake.postcode(),

            "manager_name": fake.name(),

            "capacity": fake.random_int(
                min=5000,
                max=50000
            ),

            "current_utilization": fake.random_int(
                min=100,
                max=4000
            )

        }