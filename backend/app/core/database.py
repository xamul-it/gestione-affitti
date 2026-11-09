import logging
import re
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from typing import Optional
from starlette.requests import Request
from fastapi import Depends

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
logger = logging.getLogger(__name__)

# --- search_path per sessione -------------------------------------------
# search_path vive sulla connessione PostgreSQL, ma una Session la restituisce
# al pool a ogni commit/rollback e alla transazione dopo ne prende una
# qualsiasi, con il search_path lasciato dall'ultimo utilizzatore (un'altra
# richiesta, uno scheduler, un altro tenant). Quindi ogni "SET search_path"
# eseguito tramite una Session viene ricordato in session.info e riapplicato
# all'inizio di ogni transazione; una Session che non l'ha mai impostato
# parte da public invece di ereditare un tenant a caso. Eccezione: una
# Session(bind=connection) usa sempre quella connessione (scheduler, test),
# quindi il search_path impostato dal chiamante su di essa resta valido.

_SEARCH_PATH_KEY = "search_path"
_OWNER_KEY = "_search_path_owner"
_SET_SEARCH_PATH_RE = re.compile(r"^\s*SET\s+(?:(?:SESSION|LOCAL)\s+)?search_path\s+(?:TO|=)\s+(.+?)\s*;?\s*$", re.IGNORECASE)


@event.listens_for(Session, "after_begin")
def _apply_session_search_path(session, transaction, connection):
    if connection.dialect.name != "postgresql":  # es. SQLite dei test unitari
        return
    # Il proprietario e' il Connection object di questa transazione: un
    # engine.connect() estraneo che riusa la stessa connessione fisica e'
    # un altro oggetto e non riscrive session.info.
    connection.info[_OWNER_KEY] = (connection, session.info)
    search_path = session.info.get(_SEARCH_PATH_KEY)
    if search_path is None:
        if isinstance(session.bind, Connection):
            return
        search_path = "public"
    connection.exec_driver_sql(f"SET search_path TO {search_path}")


@event.listens_for(engine, "after_cursor_execute")
def _remember_session_search_path(conn, cursor, statement, parameters, context, executemany):
    owner = conn.info.get(_OWNER_KEY)
    if not owner or owner[0] is not conn:
        return
    match = _SET_SEARCH_PATH_RE.match(statement)
    if match:
        owner[1][_SEARCH_PATH_KEY] = match.group(1)


def get_tenant_schema(request: Request) -> Optional[str]:
    """
    Extract tenant schema from request.state (set by TenantMiddleware).

    This is a separate dependency that can be injected without conflicts.

    Args:
        request: The current request

    Returns:
        Tenant schema name or None
    """
    return getattr(request.state, 'tenant_schema', None)


def get_db(tenant_schema: Optional[str] = Depends(get_tenant_schema)):
    """
    Dependency to get database session with tenant-aware search_path.

    Reads tenant_schema from the get_tenant_schema dependency
    and automatically applies PostgreSQL search_path for multi-tenant isolation.

    Args:
        tenant_schema: Tenant schema name from get_tenant_schema dependency

    Yields:
        Database session with tenant context applied
    """
    db = SessionLocal()
    try:
        conn = db.connection()
        if tenant_schema:
            # Validate schema name (security)
            if tenant_schema.replace('_', '').replace('-', '').isalnum():
                # Set search_path: tenant schema first, then public for shared data
                conn.execute(text(f"SET search_path TO {tenant_schema}, public"))
                logger.debug("DB context set: search_path=%s,public", tenant_schema)
        else:
            # Reset search_path to public to avoid leaking tenant context across pooled connections
            conn.execute(text("SET search_path TO public"))
            logger.debug("DB context set: search_path=public")

        try:
            current_db = conn.execute(text("SELECT current_database()")).scalar()
            search_path = conn.execute(text("SHOW search_path")).scalar()
            logger.debug("DB info: current_database=%s search_path=%s", current_db, search_path)
        except Exception:
            logger.debug("DB info: unable to read current_database/search_path")

        yield db
    finally:
        db.close()


def get_public_db():
    """
    Dependency to get a database session scoped to the public schema.

    This bypasses tenant search_path changes and is meant for cross-tenant data
    like authentication and platform tables.
    """
    db = SessionLocal()
    try:
        conn = db.connection()
        # Ensure search_path is public even if the connection was previously tenant-scoped
        conn.execute(text("SET search_path TO public"))
        logger.debug("Public DB context set: search_path=public")
        try:
            current_db = conn.execute(text("SELECT current_database()")).scalar()
            search_path = conn.execute(text("SHOW search_path")).scalar()
            logger.debug("Public DB info: current_database=%s search_path=%s", current_db, search_path)
        except Exception:
            logger.debug("Public DB info: unable to read current_database/search_path")
        yield db
    finally:
        db.close()
