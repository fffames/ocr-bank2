# OCR Bank

A full-stack web application for mobile bank receipt processing with OCR, review interface, database storage, Google Sheets export, and RAG-powered chatbot.

## Features

### Core Features
- **OCR Processing**: Extract text from Thai bank receipts using Tesseract OCR
- **Template-Based OCR**: Customizable zone-based OCR templates for different receipt formats
- **Review Interface**: View and edit OCR results with zone overlay visualization
- **Batch Upload**: Process multiple receipts at once with drag-and-drop
- **Transaction Classification**: Auto-classify transactions as income/expense
- **Database Storage**: Store receipts in PostgreSQL with full CRUD operations

### Advanced Features
- **RAG Chatbot**: Query receipt data using AI with semantic search (ChromaDB + Gemini)
- **Analytics Dashboard**: Visualize spending patterns and insights with interactive charts
- **Export Options**: Export to Google Sheets or Excel files
- **User Authentication**: JWT-based auth with login/register
- **Admin Panel**: User management and system oversight
- **Income Tracking**: Track and categorize income sources
- **Salary Management**: Manage salary records
- **Auto-Cleanup**: Automatically delete receipt images after confirmation

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- React Router v6 (routing)
- Axios + React Query (data fetching)
- Tailwind CSS (styling)
- Recharts (data visualization)
- React Hook Form + Zod (forms & validation)
- Lucide React (icons)
- React Dropzone (file uploads)

### Backend
- Python 3.10+ / FastAPI
- PostgreSQL (database)
- SQLAlchemy (ORM)
- Alembic (migrations)
- Tesseract OCR (OCR engine)
- ChromaDB (vector store for RAG)
- Google Generative AI SDK (Gemini)
- Groq (alternative LLM provider)
- Openpyxl (Excel export)
- JWT + Passlib (authentication)

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- Google Cloud account (for Gemini API)
- Groq account (for alternative LLM)

### 1. Clone the Repository

```bash
cd ocr-bank2
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Start PostgreSQL
docker compose up -d

# Run database migrations
alembic upgrade head

# Create admin user (optional)
python change_admin.py

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# The default configuration should work for local development

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

## Configuration

### Backend Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://ocr_bank_user:ocr_bank_password@localhost:5432/ocr_bank

# OCR
OCR_LANGUAGE=th  # Thai language
OCR_DEVICE=cpu   # or gpu if available

# LLM (Primary: Gemini)
GEMINI_API_KEY=your_gemini_api_key
LLM_PROVIDER=gemini

# LLM (Alternative: Groq)
GROQ_API_KEY=your_groq_api_key

# Vector Store
CHROMADB_PERSIST_DIRECTORY=./data/chromadb

# Google Sheets (optional)
GOOGLE_SHEETS_CREDENTIALS_PATH=./config/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# File Storage
IMAGE_STORAGE_PATH=./images
MAX_UPLOAD_SIZE=10485760  # 10MB

# Authentication
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Auto-cleanup
AUTO_DELETE_IMAGES=true  # Delete images after confirmation
```

### Frontend Environment Variables (.env)

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

## Project Structure

```
ocr-bank2/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Configuration
│   │   ├── api/                    # API routes
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── upload.py           # Upload & OCR endpoints
│   │   │   ├── receipts.py         # Receipt CRUD
│   │   │   ├── chat.py             # RAG chatbot
│   │   │   ├── export.py           # Export endpoints
│   │   │   ├── analytics.py        # Analytics endpoints
│   │   │   ├── admin.py            # Admin panel
│   │   │   ├── income.py           # Income tracking
│   │   │   ├── salary.py           # Salary management
│   │   │   ├── templates.py        # OCR templates
│   │   │   ├── ocr_corrections.py  # OCR corrections
│   │   │   ├── cleanup.py          # Auto-cleanup
│   │   │   └── user_settings.py    # User preferences
│   │   ├── models/                 # Database models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business logic
│   │   │   ├── ocr_service.py      # PaddleOCR wrapper
│   │   │   ├── template_ocr_service.py  # Template-based OCR
│   │   │   ├── template_manager.py      # Template management
│   │   │   ├── zone_extractor.py        # Zone extraction
│   │   │   ├── rag_service.py           # RAG implementation
│   │   │   ├── vector_store.py          # Vector store operations
│   │   │   ├── vlm_service.py           # Vision-language model
│   │   │   ├── gemini_vlm_service.py    # Gemini VLM
│   │   │   ├── transaction_classifier.py  # Transaction classification
│   │   │   ├── text_cleaning_service.py  # Text cleaning
│   │   │   ├── auth_service.py          # Authentication
│   │   │   └── excel_export_service.py  # Excel export
│   │   └── database/               # Database configuration
│   ├── requirements.txt
│   ├── alembic.ini
│   └── docker-compose.yml
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Page components
│   │   │   ├── Login.tsx           # Login page
│   │   │   ├── Register.tsx        # Registration page
│   │   │   ├── Dashboard.tsx       # Dashboard (layout)
│   │   │   ├── Upload.tsx          # Upload page
│   │   │   ├── Review.tsx          # Review page with zone overlay
│   │   │   ├── ReceiptsList.tsx    # Receipt list with filters
│   │   │   ├── Chat.tsx            # RAG chatbot
│   │   │   ├── Analytics.tsx       # Analytics dashboard
│   │   │   ├── Export.tsx          # Export page
│   │   │   ├── Settings.tsx        # User settings
│   │   │   └── Admin.tsx           # Admin panel
│   │   ├── components/             # Reusable components
│   │   │   ├── ProtectedRoute.tsx  # Auth wrapper
│   │   │   ├── ZoneOverlay.tsx     # Zone visualization
│   │   │   └── ErrorBoundary.tsx   # Error handling
│   │   ├── services/               # API service layer
│   │   │   ├── api.ts              # Base API client
│   │   │   ├── authService.ts      # Auth API
│   │   │   ├── receiptService.ts   # Receipt API
│   │   │   ├── analyticsService.ts # Analytics API
│   │   │   ├── exportService.ts    # Export API
│   │   │   └── userService.ts      # User API
│   │   ├── types/                  # TypeScript types
│   │   └── utils/                  # Utility functions
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get access token
- `GET /api/auth/me` - Get current user info
- `PUT /api/auth/me` - Update current user

### Upload & OCR
- `POST /api/upload/` - Upload receipt images (batch)
- `POST /api/upload/process-ocr/{id}` - Re-process OCR for receipt
- `POST /api/upload/process-with-template` - Process with template
- `POST /api/upload/crop-and-process` - Crop zone and process

### Receipts
- `GET /api/receipts/` - List receipts (with filters and pagination)
- `GET /api/receipts/{id}` - Get receipt details
- `PUT /api/receipts/{id}` - Update receipt
- `POST /api/receipts/{id}/confirm` - Mark as confirmed
- `DELETE /api/receipts/{id}` - Delete receipt
- `GET /api/receipts/stats/overview` - Get statistics

### Templates
- `POST /api/templates/` - Create template
- `GET /api/templates/` - List templates
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template
- `POST /api/templates/{id}/apply` - Apply template to image

### Chat & RAG
- `POST /api/chat/query` - Query receipt data with RAG
- `POST /api/chat/reset` - Reset chat context

### Analytics
- `GET /api/analytics/overview` - Get overview statistics
- `GET /api/analytics/spending-by-category` - Spending by category
- `GET /api/analytics/monthly-trends` - Monthly spending trends

### Export
- `POST /api/export/excel` - Export to Excel
- `POST /api/export/google-sheets` - Export to Google Sheets

### Admin
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}/role` - Update user role
- `DELETE /api/admin/users/{id}` - Delete user

### Income & Salary
- `GET /api/income/` - List income records
- `POST /api/income/` - Create income record
- `GET /api/salary/` - List salary records
- `POST /api/salary/` - Create salary record

## Development

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm run lint
```

### Database Migrations

**Create a new migration:**
```bash
cd backend
alembic revision --autogenerate -m "description"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL container is running
docker compose ps

# Restart PostgreSQL
docker compose restart

# View logs
docker compose logs postgres
```

### Tesseract OCR Issues
```bash
# Make sure Tesseract OCR is installed on your system
# macOS: brew install tesseract
# Ubuntu: sudo apt install tesseract-ocr
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# For Thai language support, install Thai language pack
# macOS: brew install tesseract-lang
# Ubuntu: sudo apt install tesseract-ocr-tha
```

### Frontend Build Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## License

This project is for educational purposes.

## Contributing

This is a student project. Feel free to fork and modify for your own use.
