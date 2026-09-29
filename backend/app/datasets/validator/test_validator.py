from app.datasets.loader.dataset_loader import DatasetLoader
from app.datasets.validator.dataset_validator import DatasetValidator

df = DatasetLoader.load_dataset(
    "olist/olist_customers_dataset.csv"
)

result = DatasetValidator.validate(df)

print("=" * 60)
print("DATASET VALIDATION REPORT")
print("=" * 60)

for key, value in result.items():
    print(f"{key} : {value}")