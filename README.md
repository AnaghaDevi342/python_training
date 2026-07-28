# Dockerized Data Pipeline API

A FastAPI-based API that processes employee CSV data, stores it in PostgreSQL, performs analytics using Pandas, and caches results using Redis.

## Tech Stack

- FastAPI
- PostgreSQL
- Redis
- Pandas
- SQLAlchemy
- Docker & Docker Compose
- Pytest

## Features

- Upload employee CSV data
- Data cleaning and preprocessing
- Store records in PostgreSQL
- Employee search and filtering
- Department analytics
- Hiring trends analysis
- Redis caching (5-minute TTL)
- Health monitoring endpoint

## Project Structure

```text
dockerized-data-pipeline-api
│
├── app
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── cache.py
│
├── data
│   └── employees.csv
│
├── tests
│   └── test_api.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

## Setup

Build and run the application:

```bash
docker compose up --build
```

Swagger UI:

```text
http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|----------|----------|-------------|
| GET | `/` | API status |
| POST | `/data/upload` | Upload employee CSV |
| GET | `/data` | Get employees with pagination/filtering |
| GET | `/data/{employee_id}` | Get employee by ID |
| GET | `/analytics/summary` | Department summary analytics |
| GET | `/analytics/trends` | Hiring trends analytics |
| GET | `/health` | Health check |

## Data Processing

The uploaded CSV is processed using Pandas:

- Remove duplicate records
- Handle missing values
- Convert dates and numeric fields
- Validate employee data
- Store cleaned records in PostgreSQL

## Caching

Redis is used to cache analytics results:

```text
TTL = 300 seconds (5 minutes)
```

## Testing

Run tests using:

```bash
pytest
```