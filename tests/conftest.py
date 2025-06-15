import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base
from app.main import app, get_db
from app import database_models

# Define the test database URL and a single engine for all tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# A sessionmaker to create sessions for our tests
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    """
    The main fixture for tests needing a database session.
    - Creates all tables before each test.
    - Provides a session wrapped in a transaction.
    - Rolls back the transaction and drops all tables after each test.
    This guarantees 100% isolation.
    """
    # Create tables at the start of every test
    Base.metadata.create_all(bind=engine)
    
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    
    # Drop tables at the end of every test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """
    A fixture to provide a TestClient to the integration tests.
    It handles the dependency override for the database session.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]