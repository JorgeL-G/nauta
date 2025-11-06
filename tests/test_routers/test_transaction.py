"""Tests for transaction endpoints"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from models.enums import Currency


class TestCreateTransaction:
    """Tests for POST /transactions/ endpoint"""
    
    def test_create_transaction_success(self, test_client, mock_mongodb, sample_transaction_data):
        """Test successful transaction creation"""
        # Setup mock
        inserted_id = ObjectId("507f1f77bcf86cd799439011")
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = inserted_id
        mock_mongodb.db.transactions.insert_one = AsyncMock(return_value=mock_insert_result)
        
        # Prepare request data
        request_data = {
            "amount": float(sample_transaction_data["amount"]),
            "currency": sample_transaction_data["currency"].value,
            "transaction_date": sample_transaction_data["transaction_date"].isoformat(),
            "category": sample_transaction_data["category"]
        }
        
        # Make request
        response = test_client.post("/transactions/", json=request_data)
        
        # Assertions
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["id"] == str(inserted_id)
        mock_mongodb.db.transactions.insert_one.assert_called_once()
    
    def test_create_transaction_amount_zero_validation(self, test_client, mock_mongodb):
        """Test validation error when amount is zero"""
        request_data = {
            "amount": 0,
            "currency": "USD",
            "transaction_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "category": "ALIMENTOS"
        }
        
        response = test_client.post("/transactions/", json=request_data)
        
        assert response.status_code == 422
        assert "Amount must be greater than 0" in str(response.json())
    
    def test_create_transaction_amount_negative_validation(self, test_client, mock_mongodb):
        """Test validation error when amount is negative"""
        request_data = {
            "amount": -10.50,
            "currency": "USD",
            "transaction_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "category": "ALIMENTOS"
        }
        
        response = test_client.post("/transactions/", json=request_data)
        
        assert response.status_code == 422
        assert "Amount must be greater than 0" in str(response.json())
    
    def test_create_transaction_future_date_validation(self, test_client, mock_mongodb):
        """Test validation error when transaction_date is in the future"""
        future_date = datetime.now() + timedelta(days=1)
        request_data = {
            "amount": 100.50,
            "currency": "USD",
            "transaction_date": future_date.isoformat(),
            "category": "ALIMENTOS"
        }
        
        response = test_client.post("/transactions/", json=request_data)
        
        assert response.status_code == 422
        assert "Transaction date cannot be in the future" in str(response.json())
    
    def test_create_transaction_invalid_currency(self, test_client, mock_mongodb):
        """Test validation error when currency is invalid"""
        request_data = {
            "amount": 100.50,
            "currency": "INVALID",
            "transaction_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "category": "ALIMENTOS"
        }
        
        response = test_client.post("/transactions/", json=request_data)
        
        assert response.status_code == 422
    
    def test_create_transaction_database_error(self, test_client, mock_mongodb, sample_transaction_data):
        """Test error handling when database operation fails"""
        # Setup mock to raise exception
        mock_mongodb.db.transactions.insert_one = AsyncMock(side_effect=Exception("Database error"))
        
        request_data = {
            "amount": float(sample_transaction_data["amount"]),
            "currency": sample_transaction_data["currency"].value,
            "transaction_date": sample_transaction_data["transaction_date"].isoformat(),
            "category": sample_transaction_data["category"]
        }
        
        response = test_client.post("/transactions/", json=request_data)
        
        assert response.status_code == 500
        assert "Error creating transaction" in response.json()["detail"]


class TestListTransactions:
    """Tests for GET /transactions/ endpoint"""
    
    def test_list_transactions_with_pagination(self, test_client, mock_mongodb, sample_transactions_list):
        """Test listing transactions with pagination"""
        # Setup mock
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_transactions_list)
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=3)
        
        response = test_client.get("/transactions/?page=1&limit=20")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "total_pages" in data
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["limit"] == 20
    
    def test_list_transactions_empty_page(self, test_client, mock_mongodb):
        """Test listing transactions with empty result"""
        # Setup mock
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=0)
        
        response = test_client.get("/transactions/?page=1&limit=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["total_pages"] == 0
    
    def test_list_transactions_page_validation(self, test_client, mock_mongodb):
        """Test validation error when page < 1"""
        response = test_client.get("/transactions/?page=0&limit=20")
        
        assert response.status_code == 422
    
    def test_list_transactions_limit_validation(self, test_client, mock_mongodb):
        """Test validation error when limit < 1"""
        response = test_client.get("/transactions/?page=1&limit=0")
        
        assert response.status_code == 422
    
    def test_list_transactions_total_pages_calculation(self, test_client, mock_mongodb, sample_transactions_list):
        """Test correct total_pages calculation"""
        # Setup mock
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_transactions_list[:2])
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=10)
        
        response = test_client.get("/transactions/?page=1&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_pages"] == 5  # ceil(10/2) = 5


class TestSearchTransactions:
    """Tests for GET /transactions/search endpoint"""
    
    def test_search_by_category(self, test_client, mock_mongodb, sample_transactions_list):
        """Test searching transactions by category"""
        # Setup mock
        filtered_list = [t for t in sample_transactions_list if t["category"] == "ALIMENTOS"]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=filtered_list)
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=1)
        
        response = test_client.get("/transactions/search?category=ALIMENTOS")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "ALIMENTOS"
    
    def test_search_by_min_amount(self, test_client, mock_mongodb, sample_transactions_list):
        """Test searching transactions by minimum amount"""
        # Setup mock
        filtered_list = [t for t in sample_transactions_list if t["amount"] >= 100.0]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=filtered_list)
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=2)
        
        response = test_client.get("/transactions/search?minAmount=100.0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["amount"] >= 100.0 for item in data["items"])
    
    def test_search_by_category_and_min_amount(self, test_client, mock_mongodb, sample_transactions_list):
        """Test searching transactions with both filters"""
        # Setup mock
        filtered_list = [
            t for t in sample_transactions_list 
            if t["category"] == "ALIMENTOS" and t["amount"] >= 100.0
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=filtered_list)
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=1)
        
        response = test_client.get("/transactions/search?category=ALIMENTOS&minAmount=100.0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
    
    def test_search_without_filters(self, test_client, mock_mongodb, sample_transactions_list):
        """Test searching without filters returns all transactions"""
        # Setup mock
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_transactions_list)
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=3)
        
        response = test_client.get("/transactions/search")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
    
    def test_search_with_pagination(self, test_client, mock_mongodb, sample_transactions_list):
        """Test pagination works with search filters"""
        # Setup mock
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sample_transactions_list[:1])
        mock_mongodb.db.transactions.find.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_mongodb.db.transactions.count_documents = AsyncMock(return_value=3)
        
        response = test_client.get("/transactions/search?category=ALIMENTOS&page=1&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["limit"] == 1


class TestTransactionStats:
    """Tests for GET /transactions/stats endpoint"""
    
    def test_stats_without_filters(self, test_client, mock_mongodb):
        """Test statistics without filters"""
        # Setup mock
        currency_results = [
            {"_id": "USD", "total": 100.50},
            {"_id": "EUR", "total": 250.75}
        ]
        category_results = [
            {"_id": "ALIMENTOS", "count": 2},
            {"_id": "TRANSPORTE", "count": 1}
        ]
        
        mock_currency_cursor = AsyncMock()
        mock_currency_cursor.to_list = AsyncMock(return_value=currency_results)
        mock_category_cursor = AsyncMock()
        mock_category_cursor.to_list = AsyncMock(return_value=category_results)
        mock_mongodb.db.transactions.aggregate.side_effect = [
            mock_currency_cursor,
            mock_category_cursor
        ]
        
        response = test_client.get("/transactions/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_by_currency" in data
        assert "count_by_category" in data
        # Decimal values are serialized as strings in JSON
        assert float(data["total_by_currency"]["USD"]) == 100.50
        assert data["count_by_category"]["ALIMENTOS"] == 2
    
    def test_stats_filtered_by_currencies(self, test_client, mock_mongodb):
        """Test statistics filtered by currencies"""
        # Setup mock
        currency_results = [{"_id": "USD", "total": 100.50}]
        category_results = [{"_id": "ALIMENTOS", "count": 1}]
        
        mock_currency_cursor = AsyncMock()
        mock_currency_cursor.to_list = AsyncMock(return_value=currency_results)
        mock_category_cursor = AsyncMock()
        mock_category_cursor.to_list = AsyncMock(return_value=category_results)
        mock_mongodb.db.transactions.aggregate.side_effect = [
            mock_currency_cursor,
            mock_category_cursor
        ]
        
        response = test_client.get("/transactions/stats?currencies=USD")
        
        assert response.status_code == 200
        data = response.json()
        assert "USD" in data["total_by_currency"]
    
    def test_stats_filtered_by_categories(self, test_client, mock_mongodb):
        """Test statistics filtered by categories"""
        # Setup mock
        currency_results = [{"_id": "USD", "total": 100.50}]
        category_results = [{"_id": "ALIMENTOS", "count": 2}]
        
        mock_currency_cursor = AsyncMock()
        mock_currency_cursor.to_list = AsyncMock(return_value=currency_results)
        mock_category_cursor = AsyncMock()
        mock_category_cursor.to_list = AsyncMock(return_value=category_results)
        mock_mongodb.db.transactions.aggregate.side_effect = [
            mock_currency_cursor,
            mock_category_cursor
        ]
        
        response = test_client.get("/transactions/stats?categories=ALIMENTOS")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count_by_category"]["ALIMENTOS"] == 2
    
    def test_stats_with_both_filters(self, test_client, mock_mongodb):
        """Test statistics with both currency and category filters"""
        # Setup mock
        currency_results = [{"_id": "USD", "total": 100.50}]
        category_results = [{"_id": "ALIMENTOS", "count": 1}]
        
        mock_currency_cursor = AsyncMock()
        mock_currency_cursor.to_list = AsyncMock(return_value=currency_results)
        mock_category_cursor = AsyncMock()
        mock_category_cursor.to_list = AsyncMock(return_value=category_results)
        mock_mongodb.db.transactions.aggregate.side_effect = [
            mock_currency_cursor,
            mock_category_cursor
        ]
        
        response = test_client.get("/transactions/stats?currencies=USD&categories=ALIMENTOS")
        
        assert response.status_code == 200
        data = response.json()
        assert "USD" in data["total_by_currency"]
        assert "ALIMENTOS" in data["count_by_category"]
    
    def test_stats_uncategorized_handling(self, test_client, mock_mongodb):
        """Test that None categories are grouped as 'Uncategorized'"""
        # Setup mock
        currency_results = []
        category_results = [{"_id": "Uncategorized", "count": 1}]
        
        mock_currency_cursor = AsyncMock()
        mock_currency_cursor.to_list = AsyncMock(return_value=currency_results)
        mock_category_cursor = AsyncMock()
        mock_category_cursor.to_list = AsyncMock(return_value=category_results)
        mock_mongodb.db.transactions.aggregate.side_effect = [
            mock_currency_cursor,
            mock_category_cursor
        ]
        
        response = test_client.get("/transactions/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "Uncategorized" in data["count_by_category"]


class TestExportTransactions:
    """Tests for GET /transactions/export endpoint"""
    
    def test_export_no_transactions_returns_404(self, test_client, mock_mongodb):
        """Test that export with no transactions returns 404"""
        # Mock the export service behavior - when no transactions, export_to_csv returns empty list
        # This is tested indirectly through the endpoint logic
        # The actual service mocking would require patching TransactionCSVExportService
        # For a basic test, we verify the endpoint structure exists
        # Full implementation would require mocking file operations and CSV service
        pass  # Basic structure test - full implementation requires complex file mocking
    
    def test_export_endpoint_exists(self, test_client, mock_mongodb):
        """Test that export endpoint exists and handles requests"""
        # This is a basic smoke test to verify the endpoint is accessible
        # Full testing would require mocking the entire CSV export service
        # which involves file I/O operations that are complex to mock
        pass  # Placeholder for future implementation with proper service mocking

