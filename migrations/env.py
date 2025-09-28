
from __future__ import with_statement
import logging
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from flask import current_app

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')
config.set_main_option('sqlalchemy.url', str(current_app.config.get('SQLALCHEMY_DATABASE_URI')))
target_metadata = current_app.extensions['migrate'].db.metadata

def run_migrations_offline():
    context.configure(url=config.get_main_option('sqlalchemy.url'),
                      target_metadata=target_metadata,
                      literal_binds=True,
                      dialect_opts={"paramstyle":"named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')
    connectable = engine_from_config(config.get_section(config.config_ini_section),
                                     prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata,
                          process_revision_directives=process_revision_directives,
                          **current_app.extensions['migrate'].configure_args)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
