
from __future__ import annotations
from alembic import context
from logging.config import fileConfig
from flask import current_app
from extensions import db

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = None  # Autogenerate disabled by default

def run_migrations_offline():
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    with db.engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
