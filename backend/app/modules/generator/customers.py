from faker import Faker

from .base_generator import BaseGenerator

fake = Faker()


class CustomerGenerator(BaseGenerator):

    def generate(self, index):

        return {

            "customer_code": f"CUST{index:06d}",

            "first_name": fake.first_name(),

            "last_name": fake.last_name(),

            "email": fake.unique.safe_email(),

            "phone": fake.numerify("##########"),

            "address": fake.street_address(),

            "city": fake.city(),

            "state": fake.state(),

            "country": fake.country(),

            "postal_code": fake.postcode(),

            "loyalty_points": fake.random_int(0, 10000)

        }