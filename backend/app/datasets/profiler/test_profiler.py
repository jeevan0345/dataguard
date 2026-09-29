from app.datasets.loader.dataset_loader import DatasetLoader
from app.datasets.profiler.dataset_profiler import DatasetProfiler

df = DatasetLoader.load_dataset(
    "olist/olist_customers_dataset.csv"
)

profile = DatasetProfiler.profile(df)

print("=" * 60)
print("DATASET PROFILE")
print("=" * 60)

for key, value in profile.items():
    print(f"{key} : {value}")