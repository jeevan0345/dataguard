from app.datasets.loader.dataset_loader import DatasetLoader
from app.datasets.profiler.dataset_profiler import DatasetProfiler

rows = DatasetLoader.load_dataset(
    "olist/olist_customers_dataset.csv"
)

profile = DatasetProfiler.profile(rows)

print("=" * 60)
print("DATASET PROFILE (PANDAS-FREE)")
print("=" * 60)

for key, value in profile.items():
    print(f"{key} : {value}")