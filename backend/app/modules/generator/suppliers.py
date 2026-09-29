from faker import Faker

from .base_generator import BaseGenerator

fake = Faker()


class SupplierGenerator(BaseGenerator):

    def generate(self, index):

        return {

            "company_name": fake.company(),

            "contact_person": fake.name(),

            "email": fake.unique.company_email(),

            "phone": fake.numerify("##########"),

            "address": fake.street_address(),

            "city": fake.city(),

            "state": fake.state(),

            "country": fake.country(),

            "postal_code": fake.postcode(),

            "supplier_rating": fake.random_int(min=1, max=5),

            "gst_number": f"GST{index:08d}",

            "website": f"https://www.{fake.domain_name()}"

        }