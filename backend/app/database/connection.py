import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in environment or .env file.")

# Normalize postgres:// to postgresql:// for SQLAlchemy 1.4+ / 2.0+ compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

sql_echo = os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "yes")

engine = create_engine(
    DATABASE_URL,
    echo=sql_echo,
    pool_pre_ping=True,
)