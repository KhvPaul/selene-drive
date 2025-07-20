import sys
import os

# import alembic_autogenerate_enums # noqa

from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import engine_from_config, pool, Enum

from logging.config import fileConfig

# fix import issue: https://stackoverflow.com/questions/32032940/how-to-import-the-own-model-into-myproject-alembic-env-py
sys.path.insert(0, os.getcwd())
###

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("version_locations", os.pathsep.join([
    "db/migrations/versions",
    "db/migrations/versions/create",
    "db/migrations/versions/drop",
    "db/migrations/versions/insert",
    "db/migrations/versions/update",
    "db/migrations/versions/triggers",
]))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
from db.models import Base  # noqa

target_metadata = Base.metadata  # add support SQLModel


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# def get_url():
#     user = os.getenv("POSTGRES_USER", "postgres")
#     password = os.getenv("POSTGRES_PASSWORD", "")
#     server = os.getenv("POSTGRES_SERVER", "db")
#     db = os.getenv("POSTGRES_DB", "app")
#     return f"postgresql://{user}:{password}@{server}/{db}"


def get_url() -> str:
    from config import settings

    return settings.DATABASE_ENDPOINT


# https://github.com/sqlalchemy/alembic/issues/278#issuecomment-1463537459
def render_item(type_, obj, autogen_context):
    """Apply custom rendering for Postgres enum,
    this is a "temporary" fix until this alembic issue is resolved: https://github.com/sqlalchemy/alembic/issues/278.
    """

    if type_ == "type" and isinstance(obj, Enum):
        enums = ", ".join([f"'{enum_val}'" for enum_val in obj.enums])  # noqa
        return f'sa.Enum({enums}, name="{obj.name}", create_type=False)'

    # default rendering for other objects
    return False


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_item=render_item,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    if configuration.get("sqlalchemy.url") is None:
        configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
