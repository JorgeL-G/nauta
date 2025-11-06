"""Pytest fixtures for testing"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from bson import ObjectId

from main import app
from database.mongodb import MongoDBConnection
from models.enums import Currency


@pytest.fixture
def mock_mongodb():
    """Mock MongoDBConnection for testing"""
    mock = MagicMock(spec=MongoDBConnection)
    mock.is_connected = True
    mock.db = MagicMock()
    mock.client = MagicMock()
    return mock


@pytest.fixture
def test_client(mock_mongodb):
    """FastAPI TestClient with mocked MongoDB"""
    # Set the mock MongoDB in app state before creating client
    app.state.mongodb = mock_mongodb
    client = TestClient(app)
    yield client
    # Cleanup
    if hasattr(app.state, 'mongodb'):
        del app.state.mongodb


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing"""
    return {
        "amount": Decimal("100.50"),
        "currency": Currency.USD,
        "transaction_date": datetime(2024, 1, 15),
        "category": "ALIMENTOS"
    }


@pytest.fixture
def sample_transaction_with_id():
    """Sample transaction with MongoDB _id"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "amount": 100.50,
        "currency": "USD",
        "transaction_date": datetime(2024, 1, 15),
        "category": "ALIMENTOS",
        "created_at": datetime(2024, 1, 15, 10, 0, 0)
    }


@pytest.fixture
def sample_transactions_list():
    """List of sample transactions for testing"""
    return [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "amount": 100.50,
            "currency": "USD",
            "transaction_date": datetime(2024, 1, 15),
            "category": "ALIMENTOS",
            "created_at": datetime(2024, 1, 15, 10, 0, 0)
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "amount": 250.75,
            "currency": "EUR",
            "transaction_date": datetime(2024, 1, 16),
            "category": "TRANSPORTE",
            "created_at": datetime(2024, 1, 16, 11, 0, 0)
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "amount": 50.00,
            "currency": "MXN",
            "transaction_date": datetime(2024, 1, 17),
            "category": "ENTRETENIMIENTO",
            "created_at": datetime(2024, 1, 17, 12, 0, 0)
        }
    ]

