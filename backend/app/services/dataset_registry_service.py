from uuid import UUID
from sqlalchemy.orm import Session

from app.models.dataset_registry import DatasetRegistry
from app.schemas.dataset_registry import (
    DatasetRegistryCreate,
    DatasetRegistryUpdate,
)


class DatasetRegistryService:

    @staticmethod
    def _parse_id(dataset_id: str | UUID):
        if isinstance(dataset_id, UUID):
            return dataset_id
        try:
            return UUID(str(dataset_id))
        except (ValueError, AttributeError, TypeError):
            return dataset_id

    @staticmethod
    def create_dataset(
        db: Session,
        dataset: DatasetRegistryCreate
    ) -> DatasetRegistry:

        db_dataset = DatasetRegistry(**dataset.model_dump())

        db.add(db_dataset)

        db.commit()

        db.refresh(db_dataset)

        return db_dataset

    @staticmethod
    def get_all_datasets(
        db: Session
    ):

        return db.query(DatasetRegistry).all()

    @staticmethod
    def get_dataset(
        db: Session,
        dataset_id: str | UUID
    ):
        val_id = DatasetRegistryService._parse_id(dataset_id)
        return (
            db.query(DatasetRegistry)
            .filter(DatasetRegistry.id == val_id)
            .first()
        )

    @staticmethod
    def update_dataset(
        db: Session,
        dataset_id: str | UUID,
        dataset: DatasetRegistryUpdate
    ):
        val_id = DatasetRegistryService._parse_id(dataset_id)
        db_dataset = (
            db.query(DatasetRegistry)
            .filter(DatasetRegistry.id == val_id)
            .first()
        )

        if not db_dataset:
            return None

        for key, value in dataset.model_dump(exclude_unset=True).items():
            setattr(db_dataset, key, value)

        db.commit()

        db.refresh(db_dataset)

        return db_dataset

    @staticmethod
    def delete_dataset(
        db: Session,
        dataset_id: str | UUID
    ):
        val_id = DatasetRegistryService._parse_id(dataset_id)
        db_dataset = (
            db.query(DatasetRegistry)
            .filter(DatasetRegistry.id == val_id)
            .first()
        )

        if not db_dataset:
            return False

        db.delete(db_dataset)

        db.commit()

        return True