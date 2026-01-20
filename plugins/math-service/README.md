# Math Service

A comprehensive Python/FastAPI microservice providing mathematical operations including calculations, statistics, matrix operations, Excel-like functions, and financial calculations. This is the **reference Python microservice** for the FlowForge platform.

## Features

### Core Capabilities

- **Expression Evaluation**: Safely evaluate mathematical expressions with variables and functions
- **Statistics**: Comprehensive statistical analysis (mean, median, mode, std, variance, percentiles, correlation, regression)
- **Matrix Operations**: Full linear algebra support (multiplication, transpose, inverse, determinant, eigenvalues, decomposition)
- **Excel-like Functions**: VLOOKUP, HLOOKUP, SUMIF, SUMIFS, COUNTIF, Pivot Tables
- **Financial Calculations**: NPV, IRR, PMT, FV, PV, Amortization, CAGR, ROI, Payback, DSCR

### Technical Features

- Full type hints with mypy validation
- Pydantic models for all request/response validation
- Structured logging with loguru
- Request ID middleware for tracing
- Comprehensive error handling
- OpenAPI/Swagger documentation
- pytest tests with >80% coverage
- Multi-stage Dockerfile (<200MB image)

## Tech Stack

- **Python**: 3.11+
- **Framework**: FastAPI with uvicorn
- **Validation**: Pydantic 2.5+
- **Math Libraries**: NumPy, SciPy, pandas, SymPy
- **Testing**: pytest, pytest-cov, pytest-asyncio
- **Type Checking**: mypy
- **Logging**: loguru

## API Endpoints

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| GET | `/live` | Liveness probe |
| GET | `/metrics` | Prometheus metrics |
| GET | `/openapi.json` | OpenAPI specification |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc documentation |

### Calculations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/math/calculate` | Evaluate mathematical expression |
| POST | `/api/v1/math/calculate/symbolic` | Symbolic math (simplify, differentiate, integrate) |
| POST | `/api/v1/math/calculate/solve` | Solve equations |
| GET | `/api/v1/math/calculate/functions` | List available functions |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/math/statistics` | Calculate multiple statistics |
| POST | `/api/v1/math/stats/describe` | Comprehensive statistical description |
| POST | `/api/v1/math/stats/correlation` | Correlation analysis |
| POST | `/api/v1/math/stats/regression` | Regression analysis (linear, polynomial, exponential, logarithmic) |
| GET | `/api/v1/math/statistics/operations` | List available operations |

### Matrix Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/math/matrix/add` | Matrix addition |
| POST | `/api/v1/math/matrix/subtract` | Matrix subtraction |
| POST | `/api/v1/math/matrix/multiply` | Matrix multiplication |
| POST | `/api/v1/math/matrix/transpose` | Matrix transpose |
| POST | `/api/v1/math/matrix/inverse` | Matrix inverse |
| POST | `/api/v1/math/matrix/determinant` | Matrix determinant |
| POST | `/api/v1/math/matrix/eigenvalues` | Eigenvalues and eigenvectors |
| POST | `/api/v1/math/matrix/lu` | LU decomposition |
| POST | `/api/v1/math/matrix/qr` | QR decomposition |
| POST | `/api/v1/math/matrix/svd` | SVD decomposition |
| POST | `/api/v1/math/matrix/solve` | Solve linear system Ax = b |
| POST | `/api/v1/math/matrix/least-squares` | Least squares solution |
| GET | `/api/v1/math/matrix/operations` | List available operations |

### Excel-like Functions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/math/excel/vlookup` | Vertical lookup |
| POST | `/api/v1/math/excel/hlookup` | Horizontal lookup |
| POST | `/api/v1/math/excel/sumif` | Conditional sum |
| POST | `/api/v1/math/excel/sumifs` | Sum with multiple conditions |
| POST | `/api/v1/math/excel/countif` | Conditional count |
| POST | `/api/v1/math/excel/pivot` | Pivot table creation |
| GET | `/api/v1/math/excel/operations` | List available operations |

### Financial Calculations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/math/finance/npv` | Net Present Value |
| POST | `/api/v1/math/finance/irr` | Internal Rate of Return |
| POST | `/api/v1/math/finance/pmt` | Payment calculation |
| POST | `/api/v1/math/finance/fv` | Future Value |
| POST | `/api/v1/math/finance/pv` | Present Value |
| POST | `/api/v1/math/finance/amortization` | Amortization schedule |
| POST | `/api/v1/math/finance/cagr` | Compound Annual Growth Rate |
| POST | `/api/v1/math/finance/roi` | Return on Investment |
| POST | `/api/v1/math/finance/payback` | Payback period |
| POST | `/api/v1/math/finance/dscr` | Debt Service Coverage Ratio |
| GET | `/api/v1/math/finance/operations` | List available operations |

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start development server with hot reload
uvicorn src.main:app --reload --port 3002

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Type checking
mypy src/

# Format code
black src/ tests/
isort src/ tests/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3002` |
| `ENVIRONMENT` | Environment | `development` |
| `LOG_LEVEL` | Logging level | `info` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `MAX_EXPRESSION_LENGTH` | Max expression length | `1000` |
| `MAX_ARRAY_SIZE` | Max array size for operations | `100000` |
| `CALCULATION_TIMEOUT` | Timeout for calculations (seconds) | `30` |

## Docker

```bash
# Build image
docker build -t flowforge/math-service .

# Run container
docker run -p 3002:3002 flowforge/math-service

# Run with environment variables
docker run -p 3002:3002 \
  -e LOG_LEVEL=debug \
  -e REDIS_HOST=redis \
  flowforge/math-service
```

## Examples

### Evaluate Expression

```bash
curl -X POST http://localhost:3002/api/v1/math/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression": "sqrt(16) + sin(pi/2) * 10"}'
```

Response:
```json
{
  "success": true,
  "data": {
    "expression": "sqrt(16) + sin(pi/2) * 10",
    "result": 14.0
  },
  "request_id": "abc123",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Calculate with Variables

```bash
curl -X POST http://localhost:3002/api/v1/math/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression": "x * y + z", "variables": {"x": 10, "y": 5, "z": 3}}'
```

### Comprehensive Statistics (describe)

```bash
curl -X POST http://localhost:3002/api/v1/math/stats/describe \
  -H "Content-Type: application/json" \
  -d '{"data": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}'
```

Response:
```json
{
  "success": true,
  "data": {
    "count": 10,
    "mean": 5.5,
    "median": 5.5,
    "std": 2.87,
    "variance": 8.25,
    "min": 1.0,
    "max": 10.0,
    "range": 9.0,
    "sum": 55.0,
    "quartiles": {
      "q1": 3.25,
      "q2": 5.5,
      "q3": 7.75,
      "iqr": 4.5
    },
    "skewness": 0.0,
    "kurtosis": -1.2,
    "outliers": {"count": 0, "values": []}
  }
}
```

### Correlation Analysis

```bash
curl -X POST http://localhost:3002/api/v1/math/stats/correlation \
  -H "Content-Type: application/json" \
  -d '{
    "x": [1, 2, 3, 4, 5],
    "y": [2, 4, 5, 4, 5],
    "method": "pearson"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "correlation": 0.775,
    "p_value": 0.123,
    "r_squared": 0.6,
    "method": "pearson",
    "n": 5,
    "strength": "strong",
    "direction": "positive",
    "significant": false
  }
}
```

### Regression Analysis

```bash
curl -X POST http://localhost:3002/api/v1/math/stats/regression \
  -H "Content-Type: application/json" \
  -d '{
    "x": [1, 2, 3, 4, 5],
    "y": [2.1, 3.9, 6.1, 7.9, 10.1],
    "model": "linear",
    "include_predictions": true
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "model": "linear",
    "coefficients": [2.0, 0.0],
    "r_squared": 0.998,
    "equation": "y = 2.0x + 0.0",
    "predictions": [2.0, 4.0, 6.0, 8.0, 10.0],
    "residuals": [0.1, -0.1, 0.1, -0.1, 0.1]
  }
}
```

### Matrix Operations

```bash
# Matrix multiplication
curl -X POST http://localhost:3002/api/v1/math/matrix/multiply \
  -H "Content-Type: application/json" \
  -d '{
    "a": [[1, 2], [3, 4]],
    "b": [[5, 6], [7, 8]]
  }'

# Solve linear system Ax = b
curl -X POST http://localhost:3002/api/v1/math/matrix/solve \
  -H "Content-Type: application/json" \
  -d '{
    "A": [[1, 1], [1, -1]],
    "b": [3, 1]
  }'
```

### Excel-like VLOOKUP

```bash
curl -X POST http://localhost:3002/api/v1/math/excel/vlookup \
  -H "Content-Type: application/json" \
  -d '{
    "lookup_value": 2,
    "table_array": [
      {"id": 1, "name": "Alice", "salary": 50000},
      {"id": 2, "name": "Bob", "salary": 45000},
      {"id": 3, "name": "Charlie", "salary": 60000}
    ],
    "lookup_column": "id",
    "return_column": "name",
    "exact_match": true
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "result": "Bob",
    "lookup_value": 2,
    "matched_row": {"id": 2, "name": "Bob", "salary": 45000}
  }
}
```

### Pivot Table

```bash
curl -X POST http://localhost:3002/api/v1/math/excel/pivot \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"region": "North", "product": "A", "sales": 100},
      {"region": "North", "product": "B", "sales": 150},
      {"region": "South", "product": "A", "sales": 200},
      {"region": "South", "product": "B", "sales": 250}
    ],
    "rows": ["region"],
    "columns": ["product"],
    "values": ["sales"],
    "aggfunc": "sum"
  }'
```

### Financial: NPV Calculation

```bash
curl -X POST http://localhost:3002/api/v1/math/finance/npv \
  -H "Content-Type: application/json" \
  -d '{
    "rate": 0.1,
    "cash_flows": [-1000, 300, 420, 680]
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "npv": 78.82,
    "rate": 0.1,
    "cash_flows": [-1000, 300, 420, 680]
  }
}
```

### Financial: Loan Payment (PMT)

```bash
curl -X POST http://localhost:3002/api/v1/math/finance/pmt \
  -H "Content-Type: application/json" \
  -d '{
    "rate": 0.05,
    "nper": 12,
    "pv": 10000
  }'
```

### Financial: Amortization Schedule

```bash
curl -X POST http://localhost:3002/api/v1/math/finance/amortization \
  -H "Content-Type: application/json" \
  -d '{
    "principal": 100000,
    "annual_rate": 0.05,
    "periods": 360
  }'
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_statistics.py

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

## Project Structure

```
math-service/
├── Dockerfile
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py           # Settings and configuration
│   ├── main.py             # FastAPI application entry point
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   └── request_id.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py         # Generic response models
│   │   ├── calculate.py
│   │   ├── statistics.py
│   │   ├── excel.py
│   │   └── finance.py
│   └── routes/
│       ├── __init__.py
│       ├── calculate.py    # Expression evaluation
│       ├── statistics.py   # Statistical analysis
│       ├── matrix.py       # Matrix operations
│       ├── excel.py        # Excel-like functions
│       ├── finance.py      # Financial calculations
│       └── health.py       # Health endpoints
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_calculate.py
    ├── test_statistics.py
    ├── test_matrix.py
    ├── test_excel.py
    ├── test_finance.py
    └── test_health.py
```

## Kong Gateway Integration

The math-service is accessible through Kong Gateway at `/api/v1/math/*`:

```bash
# Via Kong Gateway (with authentication)
curl -X POST http://localhost:8000/api/v1/math/calculate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{"expression": "2 + 2"}'
```

## License

MIT
