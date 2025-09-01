# CPQ Backend API

FastAPI backend for CPQ (Configure, Price, Quote) system with AI-powered quote generation.

## Features

- **Structured Quote Generation**: Uses OpenAI's structured outputs API with strict JSON schema validation
- **Flexible Lookup**: Supports both Google Sheets and PostgreSQL for price lookups
- **PDF Generation**: Creates professional PDF quotes using WeasyPrint
- **Telegram Integration**: Automatically sends generated quotes to Telegram
- **Comprehensive Validation**: Pydantic models with strict validation rules
- **Error Handling**: Uniform JSON error responses with proper HTTP status codes
- **Performance Monitoring**: Built-in timing and logging for all operations

## Tech Stack

- **Runtime**: Python 3.11+, FastAPI, Uvicorn
- **AI**: OpenAI Responses API with json_schema (strict)
- **Lookup**: Google Sheets or PostgreSQL (configurable)
- **PDF**: WeasyPrint with Cyrillic font support
- **Messaging**: Telegram Bot API
- **Storage**: Local filesystem (MVP) or S3-compatible storage
- **Dev Tools**: Ruff (lint), Black (format), Pytest (tests)

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd backend

# Install dependencies
pip install -e ".[dev]"

# Or using uv (recommended)
uv pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `TG_BOT_TOKEN`: Telegram bot token
- `TG_MANAGER_CHAT_ID`: Telegram chat ID for notifications
- `LOOKUP_SOURCE`: Either "sheets" or "postgres"
- `BASE_URL`: Base URL for PDF serving (e.g., "http://localhost:8000")

### 3. Database Setup (if using PostgreSQL)

```sql
CREATE TABLE quote_catalog (
  id serial PRIMARY KEY,
  fefco text, x_mm int, y_mm int, z_mm int,
  material text, print text, sla_type text,
  qty_min int, qty_max int,
  lead_time_std text, lead_time_rush text, lead_time_strg text,
  price_std numeric(10,2), margin_std numeric(5,2),
  price_rush numeric(10,2), margin_rush numeric(5,2),
  price_strg numeric(10,2), margin_strg numeric(5,2),
  sku text, terms text[]
);

CREATE INDEX qc_keys ON quote_catalog (fefco,x_mm,y_mm,z_mm,material,print,sla_type);
CREATE INDEX qc_qty ON quote_catalog (qty_min,qty_max);
```

### 4. Google Sheets Setup (if using Sheets)

1. Create a Google Sheet with the following columns:
   - `fefco`, `x_mm`, `y_mm`, `z_mm`, `material`, `print`, `sla_type`
   - `qty_min`, `qty_max`, `sku`
   - `lead_time_std`, `lead_time_rush`, `lead_time_strg`
   - `price_std`, `margin_std`, `price_rush`, `margin_rush`, `price_strg`, `margin_strg`
   - `terms`

2. Create a service account and download credentials as `credentials.json`

### 5. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Or using the script
python -m app.main

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### `POST /api/quote`

Generate a quote based on form data.

**Request:**
```json
{
  "fefco": "0201",
  "x_mm": 300,
  "y_mm": 200,
  "z_mm": 150,
  "material": "Микрогофрокартон Крафт",
  "print": "1+0",
  "qty": 1000,
  "sla_type": "стандарт",
  "company": "ООО Ромашка",
  "contact_name": "Иван",
  "city": "Уфа",
  "phone": "+7 999 000-00-00",
  "email": "test@example.com",
  "tg_username": "@client"
}
```

**Response:**
```json
{
  "ok": true,
  "pdf_url": "http://localhost:8000/pdf/web-123.pdf",
  "lead_id": "web-123"
}
```

### `GET /pdf/{lead_id}.pdf`

Download generated PDF by lead ID.

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_quote_api.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .

# Type checking
mypy app/
```

### Project Structure

```
backend/
├── app/
│   ├── core/           # Configuration and settings
│   ├── models/         # Pydantic models and schemas
│   ├── providers/      # Data providers (lookup)
│   ├── services/       # Business logic services
│   ├── routes/         # API routes
│   ├── middleware/     # Middleware and error handling
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── pyproject.toml      # Project configuration
├── .env.example        # Environment template
└── README.md           # This file
```

## Configuration Options

### Lookup Sources

**Google Sheets:**
- `LOOKUP_SOURCE=sheets`
- `SHEETS_ID`: Google Sheets ID
- `SHEETS_TAB`: Sheet tab name
- Requires `credentials.json` file

**PostgreSQL:**
- `LOOKUP_SOURCE=postgres`
- `DB_DSN`: Database connection string

### Lookup Policies

- `LOOKUP_POLICY=strict`: Only exact matches
- `LOOKUP_POLICY=fallback`: Find nearest quantity band if no exact match

### PDF Storage

- `PDF_STORAGE=local`: Store PDFs locally
- `PDF_STORAGE=s3`: Store in S3-compatible storage

## Error Handling

The API returns uniform JSON error responses:

```json
{
  "ok": false,
  "error": "Error description"
}
```

HTTP Status Codes:
- `400`: Validation errors
- `404`: Price pack not found
- `502`: Temporary errors (AI/PDF generation)
- `500`: Internal server errors

## Performance

The system logs performance metrics for each quote generation:
- Lookup time
- LLM generation time
- PDF creation time
- Telegram sending time
- Total processing time

## Security

- All secrets are loaded from environment variables
- No sensitive data in logs (phone/email are masked)
- PDFs are stored without PII in filenames
- Rate limiting recommended for production (not implemented in MVP)

## License

MIT License