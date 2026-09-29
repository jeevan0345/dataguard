from .base import Base
from .connection import engine
import app.models  # Registers all models with Base.metadata


def create_tables():
    Base.metadata.create_all(bind=engine)