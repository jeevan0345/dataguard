from faker import Faker
import random

from .base_generator import BaseGenerator

fake = Faker()


class EmployeeGenerator(BaseGenerator):

    DEPARTMENTS = [
        "IT",
        "Finance",
        "Human Resources",
        "Sales",
        "Marketing",
        "Operations",
        "Logistics",
        "Procurement",
        "Customer Support",
        "Administration"
    ]

    DESIGNATIONS = {
        "IT": ["Software Engineer", "Senior Engineer", "Team Lead"],
        "Finance": ["Accountant", "Financial Analyst", "Finance Manager"],
        "Human Resources": ["HR Executive", "HR Manager"],
        "Sales": ["Sales Executive", "Sales Manager"],
        "Marketing": ["Marketing Executive", "Marketing Manager"],
        "Operations": ["Operations Executive", "Operations Manager"],
        "Logistics": ["Logistics Executive", "Logistics Manager"],
        "Procurement": ["Procurement Officer", "Procurement Manager"],
        "Customer Support": ["Support Executive", "Support Manager"],
        "Administration": ["Administrator", "Office Manager"]
    }

    MANAGERS = [
        "John Smith",
        "Emma Johnson",
        "Michael Brown",
        "Sophia Davis",
        "William Wilson",
        "Olivia Taylor",
        "Daniel Anderson"
    ]

    def generate(self, index):

        department = random.choice(self.DEPARTMENTS)

        designation = random.choice(
            self.DESIGNATIONS[department]
        )

        return {

            "employee_code": f"EMP{index:06d}",

            "first_name": fake.first_name(),

            "last_name": fake.last_name(),

            "email": fake.unique.safe_email(),

            "phone": fake.numerify("##########"),

            "department": department,

            "designation": designation,

            "salary": round(
                random.uniform(30000, 180000),
                2
            ),

            "hire_date": fake.date_between(
                start_date="-10y",
                end_date="today"
            ),

            "manager_name": random.choice(
                self.MANAGERS
            )

        }