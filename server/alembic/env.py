from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import os
import sys

# Ensure server module is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.sqlalchemy_models import Base
from config.db_url import escape_alembic_config_url, resolve_alembic_database_url
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def _alembic_database_url(fallback=None):
    """Resolve DATABASE_URL for Alembic. Production never falls back to sqlite."""
    return resolve_alembic_database_url(
        env_url=os.getenv("DATABASE_URL"),
        fallback=fallback,
        environment=os.getenv("ENVIRONMENT"),
    )


def _set_sqlalchemy_url_on_config(url: str) -> None:
    """Write the URL into Alembic Config without ConfigParser interpolation errors."""
    config.set_main_option("sqlalchemy.url", escape_alembic_config_url(url))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = _alembic_database_url(config.get_main_option("sqlalchemy.url"))
    _set_sqlalchemy_url_on_config(url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    section = config.get_section(config.config_ini_section, {}) or {}
    database_url = _alembic_database_url(section.get("sqlalchemy.url"))
    if database_url:
        _set_sqlalchemy_url_on_config(database_url)
        # engine_from_config reads this dict as-is (no ConfigParser unescape).
        section["sqlalchemy.url"] = database_url
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
