# OCR Bank Backend

FastAPI backend for bank receipt OCR and RAG chatbot.

## Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start PostgreSQL:**
```bash
docker compose up -d
```

5. **Run database migrations:**
```bash
alembic upgrade head
```

6. **Start the server:**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

See `.env.example` for all available configuration options.

## Project Structure

```
app/
├── main.py                 # FastAPI application
├── config.py               # Configuration settings
├── api/                    # API routes
├── models/                 # Database models
├── schemas/                # Pydantic schemas
├── services/               # Business logic
├── database/               # Database configuration
└── utils/                  # Utility functions
```
