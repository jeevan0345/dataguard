from .customers import CustomerGenerator

generator = CustomerGenerator()

for _ in range(5):
    print(generator.generate())