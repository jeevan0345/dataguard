from app.datasets.loader.dataset_loader import DatasetLoader

rows = DatasetLoader.load_dataset(
    "olist/olist_customers_dataset.csv"
)

print("=" * 60)
print("DATASET LOADED SUCCESSFULLY (PANDAS-FREE)")
print("=" * 60)
print(f"Total rows: {len(rows)}")
if rows:
    print(f"Columns: {list(rows[0].keys())}")
    print("Sample row:", rows[0])