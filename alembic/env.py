from __future__ import with_statement
import os
from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

# Allow database url override via APP_DB_PATH
if os.environ.get('APP_DB_PATH'):
    config.set_main_option('sqlalchemy.url', f"sqlite:///{os.environ['APP_DB_PATH']}")

target_metadata = None

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
