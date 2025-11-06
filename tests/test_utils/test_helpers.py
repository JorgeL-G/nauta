"""Tests for helper functions"""
import pytest
from datetime import datetime
from bson import ObjectId

from routers.transaction import convert_docs_to_dict, build_paginated_response


class TestConvertDocsToDict:
    """Tests for convert_docs_to_dict function"""
    
    def test_converts_objectid_to_string(self):
        """Test that ObjectId is converted to string"""
        doc_id = ObjectId("507f1f77bcf86cd799439011")
        docs = [{"_id": doc_id, "amount": 100.50}]
        result = convert_docs_to_dict(docs)
        assert isinstance(result[0]["_id"], str)
        assert result[0]["_id"] == str(doc_id)
    
    def test_handles_empty_list(self):
        """Test that empty list is handled correctly"""
        result = convert_docs_to_dict([])
        assert result == []
    
    def test_preserves_other_fields(self):
        """Test that other fields are preserved"""
        doc_id = ObjectId("507f1f77bcf86cd799439011")
        docs = [{
            "_id": doc_id,
            "amount": 100.50,
            "currency": "USD",
            "category": "ALIMENTOS",
            "transaction_date": datetime(2024, 1, 15)
        }]
        result = convert_docs_to_dict(docs)
        assert result[0]["amount"] == 100.50
        assert result[0]["currency"] == "USD"
        assert result[0]["category"] == "ALIMENTOS"
        assert result[0]["transaction_date"] == datetime(2024, 1, 15)
    
    def test_handles_multiple_documents(self):
        """Test that multiple documents are converted correctly"""
        doc1_id = ObjectId("507f1f77bcf86cd799439011")
        doc2_id = ObjectId("507f1f77bcf86cd799439012")
        docs = [
            {"_id": doc1_id, "amount": 100.50},
            {"_id": doc2_id, "amount": 200.75}
        ]
        result = convert_docs_to_dict(docs)
        assert len(result) == 2
        assert result[0]["_id"] == str(doc1_id)
        assert result[1]["_id"] == str(doc2_id)


class TestBuildPaginatedResponse:
    """Tests for build_paginated_response function"""
    
    def test_calculates_total_pages_correctly(self):
        """Test that total_pages is calculated correctly"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = build_paginated_response(items, total=10, page=1, limit=3)
        assert response.total_pages == 4  # ceil(10/3) = 4
    
    def test_handles_zero_total(self):
        """Test that zero total returns zero total_pages"""
        response = build_paginated_response([], total=0, page=1, limit=20)
        assert response.total_pages == 0
    
    def test_response_structure_is_correct(self):
        """Test that response structure is correct"""
        items = [{"id": 1}, {"id": 2}]
        response = build_paginated_response(items, total=10, page=1, limit=2)
        assert response.items == items
        assert response.total == 10
        assert response.page == 1
        assert response.limit == 2
        assert response.total_pages == 5
    
    def test_handles_exact_division(self):
        """Test that exact division works correctly"""
        items = [{"id": i} for i in range(1, 21)]
        response = build_paginated_response(items, total=20, page=1, limit=20)
        assert response.total_pages == 1
    
    def test_handles_remainder_division(self):
        """Test that remainder division rounds up correctly"""
        items = [{"id": 1}, {"id": 2}]
        response = build_paginated_response(items, total=11, page=1, limit=2)
        assert response.total_pages == 6  # ceil(11/2) = 6

