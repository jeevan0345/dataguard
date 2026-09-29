from app.datasets.loader.dataset_loader import DatasetLoader
from app.datasets.profiler.dataset_profiler import DatasetProfiler
from app.datasets.validator.dataset_validator import DatasetValidator


class DatasetRegistryService:

    @staticmethod
    def analyze(dataset_path: str):

        df = DatasetLoader.load_dataset(dataset_path)

        profile = DatasetProfiler.profile(df)

        validation = DatasetValidator.validate(df)

        return {

            "profile": profile,

            "validation": validation

        }