from .base import Base
from .connection import engine


def create_tables():
    Base.metadata.create_all(bind=engine)