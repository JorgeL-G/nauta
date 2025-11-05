import logging
import math
import zipfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, List, Any, Iterator
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import StreamingResponse
from database.mongodb import MongoDBConnection
from models.transaction import (
    Transaction,
    TransactionCreatedResponse,
    TransactionStats,
    PaginatedResponse
)
from models.enums import Currency
from services.csv_export import TransactionCSVExportService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_mongodb_connection(request: Request) -> MongoDBConnection:
    """Get MongoDB connection from app state and verify it's connected
    
    Args:
        request: FastAPI Request object
        
    Returns:
        MongoDBConnection instance
        
    Raises:
        HTTPException: If database is not connected
    """
    mongodb: MongoDBConnection = request.app.state.mongodb
    
    if not mongodb.is_connected:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    return mongodb


def convert_docs_to_dict(docs: List[dict]) -> List[dict]:
    """Convert MongoDB documents ObjectId to string for serialization
    
    Args:
        docs: List of MongoDB documents
        
    Returns:
        List of documents with _id converted to string
    """
    converted = []
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        converted.append(doc)
    return converted


def build_paginated_response(items: List[Any], total: int, page: int, limit: int) -> PaginatedResponse[Any]:
    """Build a paginated response with calculated total pages
    
    Args:
        items: List of items for the current page
        total: Total number of items
        page: Current page number
        limit: Number of items per page
        
    Returns:
        PaginatedResponse with all pagination metadata
    """
    total_pages = math.ceil(total / limit) if total > 0 else 0
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


def generate_zip_stream(file_paths: List[str], export_service: TransactionCSVExportService) -> Iterator[bytes]:
    """Generator to stream ZIP file content containing CSV files
    
    Args:
        file_paths: List of paths to CSV files to include in ZIP
        export_service: TransactionCSVExportService instance for cleanup
        
    Yields:
        Bytes chunks of the ZIP file content
    """
    temp_dir = Path(export_service.get_temp_dir())
    zip_path = temp_dir / "transactions_export.zip"
    
    try:
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for csv_file_path in file_paths:
                file_path = Path(csv_file_path)
                # Add file to ZIP with just the filename (not full path)
                zipf.write(file_path, arcname=file_path.name)
                logger.info(f"Added {file_path.name} to ZIP archive")
        
        # Stream ZIP file content
        with open(zip_path, 'rb') as f:
            while True:
                chunk = f.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                yield chunk
                    
    finally:
        # Clean up after sending
        export_service.cleanup_temp_files()


@router.post("/", response_model=TransactionCreatedResponse, status_code=201)
async def create_transaction(request: Request, transaction: Transaction):
    """Create a new transaction"""
    logger.info(f"Creating new transaction: {transaction}")
    
    mongodb = get_mongodb_connection(request)
    
    try:        
        # Insert into MongoDB
        result = await mongodb.db.transactions.insert_one(transaction.to_dict())
        
        # Return only the id
        response = TransactionCreatedResponse(id=str(result.inserted_id))
        
        logger.info(f"Transaction created successfully with ID: {response.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {str(e)}")


@router.get("/", response_model=PaginatedResponse[Any])
async def list_transactions(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, description="Number of items per page")
):
    """List all transactions with pagination"""
    logger.info(f"Listing transactions - page: {page}, limit: {limit}")
    
    mongodb = get_mongodb_connection(request)
    
    try:
        # Calculate skip value
        skip = (page - 1) * limit
        
        # Get total count
        total = await mongodb.db.transactions.count_documents({})
        
        # Get transactions with pagination
        cursor = mongodb.db.transactions.find({}).skip(skip).limit(limit)
        transactions_docs = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for serialization
        transactions = convert_docs_to_dict(transactions_docs)
        
        logger.info(f"Retrieved {len(transactions)} transactions out of {total} total")
        
        return build_paginated_response(transactions, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing transactions: {str(e)}")


@router.get("/search", response_model=PaginatedResponse[Any])
async def search_transactions(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    minAmount: Optional[float] = Query(None, ge=0, description="Filter by minimum amount"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    limit: int = Query(20, ge=1, description="Number of items per page")
):
    """Search transactions filtered by category and minimum amount"""
    logger.info(f"Searching transactions - category: {category}, minAmount: {minAmount}, page: {page}, limit: {limit}")
    
    mongodb = get_mongodb_connection(request)
    
    try:
        # Build filter efficiently - prioritize category filter to use category_1 index
        filter_query = {}
        
        if category is not None:
            filter_query["category"] = category
        
        if minAmount is not None:
            filter_query["amount"] = {"$gte": minAmount}
        
        # Calculate skip value
        skip = (page - 1) * limit
        
        # Get total count with filter
        total = await mongodb.db.transactions.count_documents(filter_query)
        
        # Get transactions with filter and pagination
        cursor = mongodb.db.transactions.find(filter_query).skip(skip).limit(limit)
        transactions_docs = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for serialization
        transactions = convert_docs_to_dict(transactions_docs)
        
        logger.info(f"Retrieved {len(transactions)} transactions out of {total} total matching filters")
        
        return build_paginated_response(transactions, total, page, limit)
        
    except Exception as e:
        logger.error(f"Error searching transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching transactions: {str(e)}")


@router.get("/stats", response_model=TransactionStats)
async def get_transaction_stats(
    request: Request,
    currencies: Optional[List[Currency]] = Query(None, description="Filter by currencies"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories")
):
    """Get transaction statistics (total by currency and count by category)"""
    logger.info(f"Getting transaction stats - currencies: {currencies}, categories: {categories}")
    
    mongodb = get_mongodb_connection(request)
    
    try:
        # Build match filter
        match_filter = {}
        if currencies:
            # Convert Currency enum to string values
            currency_values = [c.value for c in currencies]
            match_filter["currency"] = {"$in": currency_values}
        
        if categories:
            match_filter["category"] = {"$in": categories}
        
        # Pipeline for total by currency
        currency_pipeline = []
        if match_filter:
            currency_pipeline.append({"$match": match_filter})
        currency_pipeline.extend([
            {
                "$group": {
                    "_id": "$currency",
                    "total": {"$sum": "$amount"}
                }
            }
        ])
        
        # Pipeline for count by category
        category_pipeline = []
        if match_filter:
            category_pipeline.append({"$match": match_filter})
        category_pipeline.extend([
            {
                "$group": {
                    "_id": {"$ifNull": ["$category", "Uncategorized"]},
                    "count": {"$sum": 1}
                }
            }
        ])
        
        # Execute aggregations
        currency_cursor = mongodb.db.transactions.aggregate(currency_pipeline)
        category_cursor = mongodb.db.transactions.aggregate(category_pipeline)
        
        currency_results = await currency_cursor.to_list(length=None)
        category_results = await category_cursor.to_list(length=None)
        
        # Build response dictionaries
        total_by_currency = {
            result["_id"]: Decimal(str(result["total"]))
            for result in currency_results
        }
        
        count_by_category = {
            result["_id"]: result["count"]
            for result in category_results
        }
        
        logger.info(f"Stats calculated - currencies: {len(total_by_currency)}, categories: {len(count_by_category)}")
        
        return TransactionStats(
            total_by_currency=total_by_currency,
            count_by_category=count_by_category
        )
        
    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting transaction stats: {str(e)}")


@router.get("/export")
async def export_transactions(request: Request):
    """Export all transactions to CSV file(s) in a ZIP archive
    
    Always returns a ZIP file containing one or more CSV files.
    If the dataset exceeds 1,000,000 rows, it will be split into multiple
    CSV files, each containing a maximum of 1,000,000 rows.
    """
    logger.info("Starting transaction export")
    
    mongodb = get_mongodb_connection(request)
    export_service = TransactionCSVExportService(mongodb)
    
    try:
        # Export transactions to CSV files
        file_paths = await export_service.export_to_csv()
        
        if not file_paths:
            raise HTTPException(status_code=404, detail="No transactions found to export")
        
        logger.info(f"Returning ZIP file with {len(file_paths)} CSV file(s)")
        return StreamingResponse(
            generate_zip_stream(file_paths, export_service),
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="transactions_export.zip"'
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error exporting transactions: {e}")
        # Ensure cleanup on error
        export_service.cleanup_temp_files()
        raise HTTPException(status_code=500, detail=f"Error exporting transactions: {str(e)}")

