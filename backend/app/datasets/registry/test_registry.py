from pprint import pprint

from app.datasets.registry.registry_service import DatasetRegistryService

result = DatasetRegistryService.analyze(
    "olist/olist_customers_dataset.csv"
)

print("=" * 70)
print("DATAGUARD DATASET ANALYSIS")
print("=" * 70)

pprint(result)