from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context


# ---------------------------------------------------------
# Add backend directory to Python path
# ---------------------------------------------------------
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)


# ---------------------------------------------------------
# Import database Base
# ---------------------------------------------------------
from app.database.base import Base


# ---------------------------------------------------------
# Import all models so Alembic can detect them
# ---------------------------------------------------------
import app.models
import app.audit.models


# ---------------------------------------------------------
# Alembic Config object
# ---------------------------------------------------------
config = context.config


# ---------------------------------------------------------
# Configure Python logging
# ---------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ---------------------------------------------------------
# Metadata used by Alembic autogenerate
# ---------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------
# Offline migration
# ---------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.

    This configures the context with only a database URL
    and does not create a live database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------
# Online migration
# ---------------------------------------------------------
def run_migrations_online() -> None:
    """
    Run migrations in online mode.

    Alembic creates a database connection and applies
    migrations to the configured PostgreSQL database.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------
# Run the appropriate migration mode
# ---------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
