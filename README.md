# nauta-backend-api

Backend API developed with FastAPI and MongoDB.

## Requirements

- Python 3.11
- Anaconda or Miniconda
- MongoDB (local or remote instance)

## Curso de Kotlin
https://platzi.com/r/jorge.leon28700/

## Environment Setup

### Step 1: Create and activate the virtual environment with Anaconda

```bash
conda create -n nauta-backend-api python=3.11 -y
conda activate nauta-backend-api
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure environment variables (optional)

Create a `.env` file in the root directory with the following variables:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=nauta
LOG_LEVEL=INFO
```

If not provided, the application will use default values:
- `MONGODB_URI`: `mongodb://localhost:27017`
- `MONGODB_DB_NAME`: `nauta`
- `LOG_LEVEL`: `INFO`

## Running the Application

```bash
uvicorn main:app --reload
```

The application will be available at: `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Interactive documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative documentation (ReDoc): `http://localhost:8000/redoc`

## Endpoints

### General
- `GET /` - Welcome message
- `GET /health` - API status check
- `GET /db/status` - MongoDB connection status

### Transactions
- `POST /transactions/` - Create a new transaction
- `GET /transactions/` - List all transactions with pagination
  - Query parameters: `page` (default: 1), `limit` (default: 20)
- `GET /transactions/search` - Search transactions with filters
  - Query parameters: `category`, `minAmount`, `page`, `limit`
- `GET /transactions/stats` - Get transaction statistics
  - Query parameters: `currencies` (list), `categories` (list)
- `GET /transactions/export` - Export all transactions to CSV files in a ZIP archive
  - Returns a ZIP file containing one or more CSV files (max 1,000,000 rows per CSV)

## Project Structure

```
nauta/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration using Pydantic Settings
├── database/
│   └── mongodb.py          # MongoDB connection class
├── models/
│   ├── transaction.py      # Transaction models and schemas
│   └── enums.py            # Enum definitions (Currency, etc.)
├── routers/
│   ├── health.py           # Health check endpoints
│   ├── database.py         # Database status endpoints
│   └── transaction.py      # Transaction endpoints
├── services/
│   └── csv_export.py       # CSV export service for transactions
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (optional)
```

## Features

- FastAPI with async support
- MongoDB integration with Motor (async driver)
- Automatic connection management using lifespan events
- Logging configuration
- Environment-based configuration using Pydantic Settings
- RESTful API with automatic documentation
- Transaction management (CRUD operations)
- Transaction search and filtering
- Transaction statistics and analytics
- CSV export functionality with automatic splitting for large datasets
  - Optimized for large datasets with streaming support
  - Automatic file splitting when exceeding 1,000,000 rows per CSV
  - ZIP archive generation for multiple CSV files


