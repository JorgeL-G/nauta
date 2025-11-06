"""Tests for Transaction model"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import ValidationError

from models.transaction import Transaction
from models.enums import Currency


class TestTransactionAmountValidation:
    """Tests for amount validation"""
    
    def test_amount_positive_is_valid(self):
        """Test that amount > 0 is valid"""
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=datetime.now() - timedelta(days=1)
        )
        assert transaction.amount == Decimal("100.50")
    
    def test_amount_zero_raises_error(self):
        """Test that amount = 0 raises ValueError"""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                amount=Decimal("0"),
                currency=Currency.USD,
                transaction_date=datetime.now() - timedelta(days=1)
            )
        assert "Amount must be greater than 0" in str(exc_info.value)
    
    def test_amount_negative_raises_error(self):
        """Test that amount < 0 raises ValueError"""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                amount=Decimal("-10.50"),
                currency=Currency.USD,
                transaction_date=datetime.now() - timedelta(days=1)
            )
        assert "Amount must be greater than 0" in str(exc_info.value)
    
    def test_amount_decimal_type(self):
        """Test that amount can be Decimal"""
        transaction = Transaction(
            amount=Decimal("99.99"),
            currency=Currency.EUR,
            transaction_date=datetime.now() - timedelta(days=1)
        )
        assert isinstance(transaction.amount, Decimal)
        assert transaction.amount == Decimal("99.99")


class TestTransactionDateValidation:
    """Tests for transaction_date validation"""
    
    def test_past_date_is_valid(self):
        """Test that past date is valid"""
        past_date = datetime.now() - timedelta(days=10)
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=past_date
        )
        assert transaction.transaction_date == past_date
    
    def test_current_date_is_valid(self):
        """Test that current date is valid"""
        current_date = datetime.now()
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=current_date
        )
        assert transaction.transaction_date == current_date
    
    def test_future_date_raises_error(self):
        """Test that future date raises ValueError"""
        future_date = datetime.now() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                amount=Decimal("100.50"),
                currency=Currency.USD,
                transaction_date=future_date
            )
        assert "Transaction date cannot be in the future" in str(exc_info.value)


class TestTransactionCurrencyValidation:
    """Tests for currency validation"""
    
    def test_valid_currency_is_accepted(self):
        """Test that valid currency from enum is accepted"""
        for currency in Currency:
            transaction = Transaction(
                amount=Decimal("100.50"),
                currency=currency,
                transaction_date=datetime.now() - timedelta(days=1)
            )
            assert transaction.currency == currency
    
    def test_invalid_currency_raises_error(self):
        """Test that invalid currency raises error"""
        with pytest.raises(ValidationError):
            Transaction(
                amount=Decimal("100.50"),
                currency="INVALID",
                transaction_date=datetime.now() - timedelta(days=1)
            )


class TestTransactionIdField:
    """Tests for optional id field"""
    
    def test_transaction_without_id_is_valid(self):
        """Test that transaction without id is valid"""
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=datetime.now() - timedelta(days=1)
        )
        assert transaction.id is None
    
    def test_transaction_with_id_is_valid(self):
        """Test that transaction with id is valid"""
        transaction = Transaction(
            id="507f1f77bcf86cd799439011",
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=datetime.now() - timedelta(days=1)
        )
        assert transaction.id == "507f1f77bcf86cd799439011"


class TestTransactionToDict:
    """Tests for to_dict method"""
    
    def test_to_dict_excludes_id(self):
        """Test that to_dict excludes id from dictionary"""
        transaction = Transaction(
            id="507f1f77bcf86cd799439011",
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=datetime.now() - timedelta(days=1),
            category="ALIMENTOS"
        )
        result = transaction.to_dict()
        assert "id" not in result
    
    def test_to_dict_converts_decimal_to_float(self):
        """Test that to_dict converts Decimal to float"""
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=datetime.now() - timedelta(days=1)
        )
        result = transaction.to_dict()
        assert isinstance(result["amount"], float)
        assert result["amount"] == 100.50
    
    def test_to_dict_includes_all_other_fields(self):
        """Test that to_dict includes all other fields"""
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            transaction_date=datetime(2024, 1, 15),
            category="ALIMENTOS"
        )
        result = transaction.to_dict()
        assert "amount" in result
        assert "currency" in result
        assert "transaction_date" in result
        assert "category" in result
        assert "created_at" in result

