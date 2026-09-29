from app.datasets.loader.dataset_loader import DatasetLoader

df = DatasetLoader.load_dataset(
    "olist/olist_customers_dataset.csv"
)

print("=" * 60)
print("DATASET LOADED SUCCESSFULLY")
print("=" * 60)

print(df.head())

print()

print("Shape :", df.shape)

print()

df.info()