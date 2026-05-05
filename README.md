# OCR Bank

A full-stack web application for mobile bank receipt processing with OCR, review interface, database storage, Google Sheets export, and RAG-powered chatbot.

## 🚀 Quick Deploy

**Deploy to production for FREE in 30 minutes!**

See [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for step-by-step deployment instructions.

**TL;DR:**
1. Create accounts: Railway, Vercel, Supabase
2. Deploy database to Supabase
3. Deploy backend to Railway
4. Deploy frontend to Vercel
5. Test your deployed app

**Cost:** $0/month (using free tiers)

---

## Features

- **OCR Processing**: Extract text from Thai bank receipts using PaddleOCR
- **Review Interface**: View and edit OCR results before saving
- **Batch Upload**: Process multiple receipts at once
- **Database Storage**: Store receipts in PostgreSQL
- **Google Sheets Export**: Export receipt data to Google Sheets
- **RAG Chatbot**: Query receipt data using AI with semantic search
- **Analytics Dashboard**: Visualize spending patterns and insights

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- React Router (routing)
- Axios (HTTP client)
- Tailwind CSS (styling)
- Recharts (data visualization)
- React Hook Form (forms)
- Zod (validation)

### Backend
- Python 3.10+ / FastAPI
- PostgreSQL (database)
- SQLAlchemy (ORM)
- Alembic (migrations)
- PaddleOCR (Thai language OCR)
- ChromaDB (vector store for RAG)
- Google Generative AI SDK (Gemini)
- Google Sheets API (export)

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- Google Cloud account (for Gemini API and Google Sheets)

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
# Edit .env with your configuration (see below)

# Start PostgreSQL
docker compose up -d

# Run database migrations
alembic upgrade head

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

# LLM (Local: LM Studio)
LOCAL_LLM_URL=http://localhost:1234/v1

# Vector Store
CHROMADB_PERSIST_DIRECTORY=./data/chromadb

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=./config/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# File Storage
IMAGE_STORAGE_PATH=./images
MAX_UPLOAD_SIZE=10485760  # 10MB
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
│   │   │   ├── upload.py           # Upload endpoints
│   │   │   ├── receipts.py         # Receipt CRUD
│   │   │   ├── chat.py             # RAG chat (coming soon)
│   │   │   ├── export.py           # Export (coming soon)
│   │   │   └── analytics.py        # Analytics (coming soon)
│   │   ├── models/                 # Database models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business logic
│   │   │   ├── ocr_service.py      # PaddleOCR wrapper
│   │   │   ├── rag_service.py      # RAG (coming soon)
│   │   │   └── export_service.py   # Google Sheets (coming soon)
│   │   └── database/               # Database configuration
│   ├── requirements.txt
│   ├── alembic.ini
│   └── docker-compose.yml
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Upload.tsx          # Upload page (coming soon)
│   │   │   ├── Review.tsx          # Review page (coming soon)
│   │   │   ├── Receipts.tsx        # Receipt list (coming soon)
│   │   │   ├── Chat.tsx            # Chatbot (coming soon)
│   │   │   └── Analytics.tsx       # Analytics (coming soon)
│   │   ├── components/             # Reusable components
│   │   ├── services/               # API service layer
│   │   ├── types/                  # TypeScript types
│   │   └── utils/                  # Utility functions
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## 📦 Deployment

### Production Deployment

**Free Deployment Guide:**
- [QUICK_DEPLOY.md](QUICK_DEPLOY.md) - 30-minute quick deployment
- [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) - Comprehensive deployment guide

**Deployment Scripts:**
```bash
# Organize project for deployment
./scripts/organize-project.sh

# Deploy backend to Railway
./scripts/deploy-backend.sh

# Deploy frontend to Vercel
./scripts/deploy-frontend.sh

# Test deployment
./scripts/test-deployment.sh <backend-url> <frontend-url>
```

**Services Used (All Free):**
- **Frontend:** Vercel (React hosting)
- **Backend:** Railway (FastAPI hosting)
- **Database:** Supabase (PostgreSQL)

**Deployment Documentation:**
- [Deployment Guide](docs/deployment/DEPLOYMENT_GUIDE.md) - Detailed deployment instructions
- [Deployment Checklist](docs/deployment/DEPLOYMENT_CHECKLIST.md) - Pre-deployment checklist
- [Setup Guide](docs/deployment/SETUP-COMPLETE.md) - Post-deployment setup

---

## Project Structure

### Organized Structure

```
ocr-bank2/
├── backend/                    # FastAPI backend
│   ├── app/                   # Application code
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── database/         # Database config
│   │   └── main.py           # FastAPI app
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Backend tests
│   ├── config/               # Configuration files
│   ├── requirements.txt      # Python dependencies
│   └── alembic.ini           # Database migrations
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── services/        # API service layer
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # Utility functions
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite config
│
├── deployment/               # Deployment configurations
│   ├── railway/             # Railway configs
│   ├── vercel/              # Vercel configs
│   └── supabase/            # Supabase configs
│
├── docs/                     # Documentation
│   ├── guides/              # User guides
│   ├── api/                 # API documentation
│   └── deployment/          # Deployment guides
│
├── tests/                    # Test files and data
│   ├── images/              # Test images
│   └── data/                # Test data
│
├── scripts/                  # Deployment and utility scripts
│   ├── organize-project.sh  # Project organization
│   ├── deploy-backend.sh    # Backend deployment
│   ├── deploy-frontend.sh   # Frontend deployment
│   └── test-deployment.sh   # Deployment testing
│
├── docker-compose.yml        # Local development
├── railway.toml             # Railway configuration
├── README.md                # This file
├── QUICK_DEPLOY.md          # Quick deployment guide
└── DEPLOY_INSTRUCTIONS.md   # Detailed deployment guide
```

---

## Current Implementation Status

### ✅ Completed
- Backend FastAPI project structure
- PostgreSQL database setup with Docker
- Database models and Alembic migrations
- PaddleOCR service with Thai language support
- Upload and receipt API endpoints
- Frontend React + TypeScript setup with Vite
- Basic routing and navigation
- TypeScript types and API service layer
- **Deployment scripts and documentation**
- **Organized project structure**

### 🚧 In Progress
- Upload page with drag-and-drop
- Review page with image viewer
- Receipt list page

### 📋 Planned
- RAG service with LLM interface
- Chatbot interface
- Google Sheets export
- Analytics dashboard

## API Endpoints

### Upload & OCR
- `POST /api/upload/` - Upload receipt images (batch)
- `POST /api/upload/process-ocr/{id}` - Re-process OCR for receipt

### Receipts
- `GET /api/receipts/` - List receipts (with filters and pagination)
- `GET /api/receipts/{id}` - Get receipt details
- `PUT /api/receipts/{id}` - Update receipt
- `POST /api/receipts/{id}/confirm` - Mark as confirmed
- `DELETE /api/receipts/{id}` - Delete receipt
- `GET /api/receipts/stats/overview` - Get statistics

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

### PaddleOCR Issues
```bash
# PaddleOCR will download models on first run
# Make sure you have internet connection
# Models will be cached in ~/.paddleocr/

# For GPU support, install CUDA and change OCR_DEVICE=gpu in .env
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
