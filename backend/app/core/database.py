import logging
from sqlalchemy import create_engine, text
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
