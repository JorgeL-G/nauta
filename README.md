# nauta-backend-api

Backend API developed with FastAPI and MongoDB.

## Requirements

- Python 3.11
- Anaconda or Miniconda
- MongoDB (local or remote instance)

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

- `GET /` - Welcome message
- `GET /health` - API status check
- `GET /db/status` - MongoDB connection status

## Project Structure

```
nauta/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration using Pydantic Settings
├── database/
│   └── mongodb.py          # MongoDB connection class
├── routers/
│   ├── health.py           # Health check endpoints
│   └── database.py         # Database status endpoints
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
