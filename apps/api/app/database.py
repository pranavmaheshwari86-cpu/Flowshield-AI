from typing import Generator
import math
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from .config import settings

from sqlalchemy.pool import NullPool

# Determine dialect
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False, "timeout": 30.0} if is_sqlite else {}

engine_kwargs = {"connect_args": connect_args}
if is_sqlite:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 30

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

if is_sqlite:
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def reconcile_sqlite_schema(db_engine=engine, declarative_base=Base):
    """
    Ensures that existing SQLite database tables contain all columns defined in SQLAlchemy models.
    SQLite's create_all does not add new columns to pre-existing tables, which leads to
    'no such column' OperationalErrors when models evolve. This utility automatically
    discovers and safely alters existing tables with appropriate types and defaults.
    """
    if not str(db_engine.url).startswith("sqlite"):
        return

    import logging
    from sqlalchemy import text

    logger = logging.getLogger("flowshield.database_schema")

    with db_engine.connect() as conn:
        for table_name, table in declarative_base.metadata.tables.items():
            try:
                res = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                if not res:
                    continue
                existing_cols = {row[1] for row in res}
            except Exception as e:
                logger.debug(f"Skipping pragma check for {table_name}: {e}")
                continue

            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(db_engine.dialect)
                    default_clause = ""
                    if col.default is not None and hasattr(col.default, "arg") and not callable(col.default.arg):
                        val = col.default.arg
                        if isinstance(val, bool):
                            default_clause = f" DEFAULT {1 if val else 0}"
                        elif isinstance(val, (int, float)):
                            default_clause = f" DEFAULT {val}"
                        elif isinstance(val, str):
                            default_clause = f" DEFAULT '{val}'"
                    alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause};"
                    try:
                        conn.execute(text(alter_query))
                        conn.commit()
                        logger.info(f"Auto-reconciled schema: {table_name}.{col.name} ({col_type}{default_clause})")
                    except Exception as err:
                        logger.warning(f"Could not add column {col.name} to {table_name}: {err}")


def get_db() -> Generator[Session, None, None]:
    """Dependency for yielding database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

