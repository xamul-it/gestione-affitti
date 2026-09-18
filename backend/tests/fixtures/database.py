"""
Database fixtures for testing with multi-tenancy support.

Provides fixtures for:
- In-memory SQLite database for unit tests
- PostgreSQL test database for integration tests
- Tenant-scoped database sessions
- Transaction rollback for test isolation
"""

import pytest
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base


@pytest.fixture(scope="function")
def db_engine():
    """
    Create in-memory SQLite database engine for unit tests.

    Uses StaticPool to share the same connection across all operations,
    which is necessary for SQLite in-memory databases.

    Yields:
        Engine: SQLAlchemy engine instance
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Create database session with automatic rollback.

    Each test gets a fresh session that is rolled back after the test,
    ensuring test isolation.

    Args:
        db_engine: Database engine fixture

    Yields:
        Session: SQLAlchemy session instance
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def tenant_db_session(db_session, test_tenant):
    """
    Database session with tenant context (search_path set).

    Executes all queries within the tenant's schema. Use this fixture
    when testing multi-tenant features.

    Args:
        db_session: Base database session
        test_tenant: Test tenant fixture

    Yields:
        Session: Session with tenant search_path configured
    """
    # Set PostgreSQL search_path to tenant schema
    # For SQLite (unit tests), this is a no-op
    try:
        db_session.execute(
            text(f"SET search_path TO {test_tenant.schema_name}, public")
        )
    except Exception:
        # SQLite doesn't support schemas, ignore
        pass

    yield db_session


@pytest.fixture(scope="function")
def db_session_with_rollback(db_engine):
    """
    Database session that supports nested transactions.

    Useful for testing transaction-heavy code where you need
    to verify rollback behavior.

    Args:
        db_engine: Database engine fixture

    Yields:
        Session: Session with savepoint support
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    # Enable nested transactions
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def clear_db(db_session):
    """
    Clear all tables in the database.

    Use this fixture when you need a clean database state
    in the middle of a test.

    Args:
        db_session: Database session

    Returns:
        callable: Function that clears all tables
    """
    def _clear():
        # Get all table names
        meta = Base.metadata

        # Delete all rows from all tables
        for table in reversed(meta.sorted_tables):
            db_session.execute(table.delete())

        db_session.commit()

    return _clear


@pytest.fixture
def db_query_counter(db_session):
    """
    Count database queries executed during test.

    Useful for performance testing and detecting N+1 query problems.

    Args:
        db_session: Database session

    Returns:
        QueryCounter: Object with query count
    """
    class QueryCounter:
        def __init__(self):
            self.count = 0

        def __call__(self, *args, **kwargs):
            self.count += 1

    counter = QueryCounter()

    @event.listens_for(db_session.bind, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        counter()

    return counter
