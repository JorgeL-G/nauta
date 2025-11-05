"""Transaction model for financial transactions"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Generic, TypeVar, List
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .enums import Currency

T = TypeVar('T')


class Transaction(BaseModel):
    """Model representing a financial transaction"""
    
    id: str = Field(..., description="transaction id")
    amount: Decimal = Field(..., description="transaction amount, must be greater than 0")
    currency: Currency = Field(..., description="transaction currency")
    transaction_date: datetime = Field(..., description="transaction date, cannot be in the future")
    category: Optional[str] = Field(None, description="transaction category name")
    created_at: datetime = Field(default_factory=datetime.now, description="transaction was created")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        str_strip_whitespace=True
    )
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, amount: Decimal) -> Decimal:
        """Validate that amount is greater than 0"""
        if not amount <= 0:
            return amount
        raise ValueError("Amount must be greater than 0")

    
    @field_validator("transaction_date")
    @classmethod
    def validate_transaction_date(cls, transaction_date: datetime) -> datetime:
        """Validate that transaction date is not in the future"""
        now = datetime.now()
        if transaction_date <= now:
            return transaction_date
        raise ValueError("Transaction date cannot be in the future")

    def to_dict(self) -> dict:
        """Convert Transaction instance to dictionary ready for MongoDB
        
        Converts Decimal amount to float and ensures created_at is set.
        
        Returns:
            Dictionary ready for MongoDB insertion
        """
        transaction_dict = self.model_dump(exclude={"id"})
        
        # Convert Decimal to float for MongoDB storage
        transaction_dict["amount"] = float(transaction_dict["amount"])
        
        return transaction_dict


class TransactionCreatedResponse(BaseModel):
    """Model for transaction created response with only id"""
    
    id: str = Field(..., description="Transaction ID")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    
    items: List[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

class TransactionStats(BaseModel):
    """Model for transaction statistics"""
    
    total_by_currency: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Total amount by currency"
    )
    count_by_category: dict[str, int] = Field(
        default_factory=dict,
        description="Number of transactions by category"
    )
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )




