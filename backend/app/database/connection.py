import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in the .env file.")

engine = create_engine(
    DATABASE_URL,
    echo=True
)