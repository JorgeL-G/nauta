"""CSV export service for transactions"""
import csv
import logging
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional
from database.mongodb import MongoDBConnection

logger = logging.getLogger(__name__)

# Constante para el máximo de filas por CSV
MAX_ROWS_PER_CSV = 1_000_000
# Tamaño de batch para procesar desde MongoDB
BATCH_SIZE = 10000
# Frecuencia de logging de progreso (cada N registros)
LOG_PROGRESS_EVERY = 100000


class TransactionCSVExportService:
    """Service for exporting transactions to CSV files"""
    
    def __init__(self, mongodb_connection: MongoDBConnection):
        """Initialize the CSV export service
        
        Args:
            mongodb_connection: MongoDB connection instance
        """
        self.mongodb = mongodb_connection
        self.temp_dir = None
    
    def _get_csv_headers(self) -> List[str]:
        """Get CSV headers for transaction export
        
        Returns:
            List of column headers
        """
        return ["id", "amount", "currency", "transaction_date", "category", "created_at"]
    
    def _generate_csv_filename(self, part_number: int) -> str:
        """Generate filename for CSV part
        
        Args:
            part_number: Part number (1-indexed)
            
        Returns:
            Filename string
        """
        return f"transactions_part_{part_number}.csv"
    
    def _convert_transaction_to_row(self, transaction: dict) -> List[str]:
        """Convert a MongoDB transaction document to CSV row
        
        Args:
            transaction: MongoDB document dictionary
            
        Returns:
            List of string values for CSV row
        """
        # Convert _id to string
        transaction_id = str(transaction.get("_id", ""))
        
        # Convert amount (float in MongoDB) to string with precision
        amount = transaction.get("amount", 0)
        if isinstance(amount, float):
            amount_str = str(Decimal(str(amount)))
        else:
            amount_str = str(amount)
        
        # Currency
        currency = transaction.get("currency", "")
        
        # Format transaction_date (datetime object)
        transaction_date = transaction.get("transaction_date")
        if isinstance(transaction_date, datetime):
            transaction_date_str = transaction_date.isoformat()
        else:
            transaction_date_str = str(transaction_date) if transaction_date else ""
        
        # Category (can be None)
        category = transaction.get("category", "")
        category_str = category if category is not None else ""
        
        # Format created_at (datetime object)
        created_at = transaction.get("created_at")
        if isinstance(created_at, datetime):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = str(created_at) if created_at else ""
        
        return [
            transaction_id,
            amount_str,
            currency,
            transaction_date_str,
            category_str,
            created_at_str
        ]
    
    async def export_to_csv(self) -> List[str]:
        """Export all transactions to CSV files
        
        Divides into multiple files if exceeding MAX_ROWS_PER_CSV.
        Uses streaming to handle large datasets efficiently.
        
        Returns:
            List of file paths to generated CSV files
            
        Raises:
            Exception: If export fails
        """
        # Create temporary directory for CSV files
        self.temp_dir = tempfile.mkdtemp(prefix="transactions_export_")
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
        try:
            # Get total count of transactions
            total_count = await self.mongodb.db.transactions.count_documents({})
            logger.info(f"Total transactions to export: {total_count}")
            
            if total_count == 0:
                logger.warning("No transactions found to export")
                return []
            
            # Calculate number of files needed
            num_files = (total_count + MAX_ROWS_PER_CSV - 1) // MAX_ROWS_PER_CSV
            logger.info(f"Will create {num_files} CSV file(s) (max {MAX_ROWS_PER_CSV} rows per file)")
            
            # Get cursor with batch size for efficient processing
            cursor = self.mongodb.db.transactions.find({}).batch_size(BATCH_SIZE)
            
            file_paths = []
            current_file_num = 1
            current_row_count = 0
            total_processed = 0
            current_file = None
            csv_writer = None
            
            try:
                # Process transactions in batches
                async for transaction in cursor:
                    # If we need a new file, close current and create new one
                    if current_row_count == 0:
                        if current_file:
                            current_file.close()
                        
                        filename = self._generate_csv_filename(current_file_num)
                        file_path = Path(self.temp_dir) / filename
                        
                        current_file = open(file_path, 'w', newline='', encoding='utf-8')
                        csv_writer = csv.writer(current_file)
                        
                        # Write headers
                        csv_writer.writerow(self._get_csv_headers())
                        file_paths.append(str(file_path))
                        
                        logger.info(f"Created file {current_file_num}/{num_files}: {filename}")
                    
                    # Convert transaction to row and write
                    row = self._convert_transaction_to_row(transaction)
                    csv_writer.writerow(row)
                    
                    current_row_count += 1
                    total_processed += 1
                    
                    # Log progress periodically
                    if total_processed % LOG_PROGRESS_EVERY == 0:
                        logger.info(f"Progress: {total_processed}/{total_count} transactions processed")
                    
                    # Check if we've reached the max rows for current file
                    if current_row_count >= MAX_ROWS_PER_CSV:
                        current_file.close()
                        current_file = None
                        csv_writer = None
                        logger.info(f"Completed file {current_file_num} with {current_row_count} rows")
                        current_file_num += 1
                        current_row_count = 0
                
                # Close last file if open
                if current_file:
                    current_file.close()
                    logger.info(f"Completed file {current_file_num} with {current_row_count} rows")
                
                logger.info(f"Export completed: {total_processed} transactions exported to {len(file_paths)} file(s)")
                
                return file_paths
                
            except Exception as e:
                # Close file if open on error
                if current_file:
                    current_file.close()
                logger.error(f"Error during CSV export: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Failed to export transactions to CSV: {e}")
            raise
    
    def get_temp_dir(self) -> Optional[str]:
        """Get the temporary directory path used for CSV files
        
        Returns:
            Path to temporary directory or None if not created
        """
        return self.temp_dir
    
    def cleanup_temp_files(self):
        """Clean up temporary files and directory
        
        This should be called after files have been used/transferred.
        """
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
                self.temp_dir = None
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory: {e}")

