from faker import Faker
import random

fake = Faker()

class BaseGenerator:

    def random_bool(self):
        return random.choice([True, False])

    def random_price(self, minimum=10, maximum=1000):
        return round(random.uniform(minimum, maximum), 2)

    def random_quantity(self):
        return random.randint(1, 500)