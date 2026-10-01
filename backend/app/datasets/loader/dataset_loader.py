"""
Dataset loader re-export for app.datasets module.
Standardizes on the pandas-free app.etl.extractor.dataset_loader.DatasetLoader.
"""
from app.etl.extractor.dataset_loader import DatasetLoader

__all__ = ["DatasetLoader"]
