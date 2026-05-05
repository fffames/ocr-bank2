# Free Deployment Guide for OCR Bank

Complete guide to deploy OCR Bank for free using cloud services.

## Architecture

```
Frontend (React)  →  Backend (FastAPI)  →  Database (PostgreSQL)
   (Vercel)            (Railway)              (Supabase)
                          ↓
                     Vector Store (ChromaDB on Railway disk)
                      ↓
                  LLM APIs (Groq/Gemini - already external)
```

## Services to Use (All Free Tiers)

### Frontend
- **Vercel** - Free hosting for React frontend
  - Unlimited deployments
  - Automatic HTTPS
  - Global CDN
  - Free forever for personal projects

### Backend
- **Railway** - Free tier for FastAPI backend
  - $5 free credit/month (enough for small projects)
  - 512MB RAM
  - Persistent disk storage
  - Automatic HTTPS

### Database
- **Supabase** - Free PostgreSQL database
  - 500MB storage
  - Unlimited connections
  - Automatic backups
  - Built-in connection pooling

### Vector Store
- **ChromaDB on Railway** - Use Railway's persistent disk
  - Store ChromaDB data in `/data` directory
  - Persists across deployments

### External Services (Already Set Up)
- **Groq API** - Free LLM API
- **Google Sheets API** - Free for personal use
- **Google Drive** - Free storage for credentials

---

## Step-by-Step Deployment

### Step 1: Prepare Project for Deployment

#### 1.1 Update Frontend API URL

The frontend needs to point to your deployed backend (not localhost).

**Create frontend environment file:**
```bash
# frontend/.env.production
VITE_API_URL=https://your-backend.railway.app
```

**Update frontend API service:**

[frontend/src/services/api.ts](frontend/src/services/api.ts)
```typescript
// Replace base URL
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

#### 1.2 Update Backend for Production

**Create production config:**

[backend/app/config.py](backend/app/config.py) - Add production settings:
```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # OCR
    OCR_LANGUAGE: str = "th"
    OCR_DEVICE: str = "cpu"

    # LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")

    # VLM
    VLM_PROVIDER: str = os.getenv("VLM_PROVIDER", "lm_studio")
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1")

    # Vector Store - Use persistent directory on Railway
    CHROMADB_PERSIST_DIRECTORY: str = os.getenv("CHROMADB_PERSIST_DIRECTORY", "./data/chromadb")

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "./config/credentials.json")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")

    # File Storage
    IMAGE_STORAGE_PATH: str = os.getenv("IMAGE_STORAGE_PATH", "./backend/images")
    MAX_UPLOAD_SIZE: int = 10485760

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("PORT", 8000))

    # CORS - Allow your frontend URL
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    class Config:
        env_file = ".env"

settings = Settings()
```

**Update CORS to allow deployed frontend:**

[backend/app/main.py](backend/app/main.py)
```python
from fastapi.middleware.cors import CORSMiddleware

# Get CORS origins from environment
origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 1.3 Create Railway Configuration

**Create `railway.toml` in project root:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"

[env]
PORT = "8000"
```

**Create `.railwayignore`:**
```
__pycache__
*.pyc
venv
.env
.venv
node_modules
.git
```

#### 1.4 Update Requirements for Railway

**Create `backend/requirements.txt` (ensure all dependencies listed):**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
gspread==6.1.0
google-auth==2.23.4
google-oauth==1.0.0
pillow==10.1.0
opencv-python==4.8.1.78
pytesseract==0.3.10
chromadb==0.4.18
opencensus==0.11.0
opencensus-ext-azure==1.0.8
```

---

### Step 2: Deploy Database (Supabase)

#### 2.1 Create Supabase Project

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign in with GitHub
4. Create new project:
   - **Name:** ocr-bank-db
   - **Database Password:** (generate strong password - save it!)
   - **Region:** Southeast Asia (Singapore) for faster access from Thailand

#### 2.2 Get Database Connection String

1. In Supabase dashboard, go to **Settings** → **Database**
2. Find **Connection string** → **URI**
3. Select **Python** language
4. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```

#### 2.3 Test Connection Locally (Optional)

```bash
# Install PostgreSQL client
brew install postgresql  # macOS
# or apt-get install postgresql-client  # Linux

# Test connection
psql "postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres"
```

---

### Step 3: Deploy Backend (Railway)

#### 3.1 Create Railway Account

1. Go to https://railway.app
2. Click **Login** → **Sign up with GitHub**

#### 3.2 Create New Project

1. Click **New Project** → **Deploy from GitHub repo**
2. Select your OCR Bank repository
3. Configure deployment:
   - **Root directory:** `ocr-bank2/backend`
   - **Python version:** 3.11 or higher

#### 3.3 Set Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```bash
# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres

# OCR
OCR_LANGUAGE=th
OCR_DEVICE=cpu

# LLM (use Groq for free tier)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaxxxxxxxxxxxxx
LLM_PROVIDER=groq

# VLM (disable LM Studio for cloud deployment)
VLM_PROVIDER=groq
LOCAL_LLM_URL=

# Vector Store - Use Railway's persistent disk
CHROMADB_PERSIST_DIRECTORY=/data/chromadb

# Google Sheets (you'll need to upload credentials separately)
GOOGLE_SHEETS_SPREADSHEET_ID=1kIPkLNIRmHJv1Y1admnoLigFh0iycS-9GUIymxvJDoU

# File Storage
IMAGE_STORAGE_PATH=/data/images
MAX_UPLOAD_SIZE=10485760

# CORS - Allow your deployed frontend
CORS_ORIGINS=https://your-frontend.vercel.app,https://ocr-bank.vercel.app

# Port (Railway sets this automatically)
PORT=8000
```

#### 3.4 Add Persistent Disk for ChromaDB

1. In Railway service, go to **Storage** tab
2. Click **+ New Volume**
3. Create volume:
   - **Name:** chromadb-data
   - **Mount path:** `/data`
4. This ensures ChromaDB data persists across deployments

#### 3.5 Upload Google Sheets Credentials

Railway doesn't have file uploads, so we need a workaround:

**Option 1: Base64 encode credentials**
```bash
# Encode your credentials.json
base64 -i config/credentials.json

# Add to Railway variables
GOOGLE_SHEETS_CREDENTIALS_BASE64=[base64-string]
```

**Update backend to decode:**
```python
# In google_sheets_service.py
import base64

if os.getenv("GOOGLE_SHEETS_CREDENTIALS_BASE64"):
    # Decode from base64
    import tempfile
    decoded = base64.b64decode(os.getenv("GOOGLE_SHEETS_CREDENTIALS_BASE64"))
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json') as f:
        f.write(decoded)
        settings.google_sheets_credentials_path = f.name
```

**Option 2: Use Google Cloud Storage (recommended)**
- Upload credentials.json to Google Cloud Storage (free tier)
- Download at runtime

For now, **skip Google Sheets** or use **Option 1**.

#### 3.6 Deploy Backend

1. Click **Deploy** button in Railway
2. Wait for deployment (2-3 minutes)
3. Railway will provide a URL like: `https://ocr-bank-production.up.railway.app`
4. Test health check:
   ```bash
   curl https://your-backend.railway.app/health
   ```

#### 3.7 Run Database Migrations

Railway doesn't auto-run Alembic migrations. Two options:

**Option 1: Remote shell**
```bash
# Connect to Railway service
railway shell

# Run migrations
alembic upgrade head
```

**Option 2: Add startup script**
```python
# backend/app/main.py
@app.on_event("startup")
async def startup_event():
    # Run migrations on startup
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

---

### Step 4: Deploy Frontend (Vercel)

#### 4.1 Install Vercel CLI

```bash
npm install -g vercel
```

#### 4.2 Login to Vercel

```bash
vercel login
```

#### 4.3 Deploy Frontend

```bash
cd frontend

# First deployment
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your username
# - Link to existing project? No
# - Project name: ocr-bank-frontend
# - Directory: ./
# - Override settings? No
```

#### 4.4 Set Environment Variables in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project (ocr-bank-frontend)
3. Go to **Settings** → **Environment Variables**
4. Add variable:
   ```
   VITE_API_URL=https://your-backend.railway.app
   ```
5. Redeploy (variables apply on next deployment)

#### 4.5 Get Frontend URL

Vercel will provide:
```
https://ocr-bank-frontend.vercel.app
```

#### 4.6 Update Backend CORS

Go back to Railway and update `CORS_ORIGINS`:
```bash
CORS_ORIGINS=https://ocr-bank-frontend.vercel.app
```

---

### Step 5: Configure Custom Domain (Optional)

#### 5.1 Point Domain to Vercel

If you have a custom domain (e.g., `ocrbank.com`):

1. In Vercel dashboard, go to **Settings** → **Domains**
2. Add your domain
3. Vercel will show DNS records to add

#### 5.2 Update Backend CORS

```bash
CORS_ORIGINS=https://ocrbank.com,https://www.ocrbank.com
```

---

## Step 6: Test Deployment

### 6.1 Frontend Test

1. Open your Vercel URL
2. Should see OCR Bank homepage
3. Check browser console for errors

### 6.2 Backend Test

```bash
# Test API health
curl https://your-backend.railway.app/

# Test database connection
curl https://your-backend.railway.app/receipts/

# Test upload (small image)
curl -X POST \
  -F "files=@test.jpg" \
  https://your-backend.railway.app/upload/
```

### 6.3 End-to-End Test

1. Go to deployed frontend
2. Upload a receipt image
3. Check it appears in receipts list
4. Verify data in Supabase database

---

## Cost Breakdown (All Free!)

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| **Vercel** (Frontend) | Unlimited | $0 |
| **Railway** (Backend) | $5 credit/month | $0 |
| **Supabase** (Database) | 500MB storage | $0 |
| **Groq API** (LLM) | Free tier | $0 |
| **Google Sheets** | Personal use | $0 |
| **Total** | - | **$0/month** |

**Free tier limits:**
- Vercel: Unlimited bandwidth, 100GB bandwidth/month
- Railway: $5 credit (enough for small projects)
- Supabase: 500MB DB, 1GB file storage
- Groq: Free tier (generous limits)

---

## Troubleshooting

### Issue 1: CORS Errors

**Problem:** Frontend can't connect to backend

**Solution:**
```bash
# In Railway, update CORS_ORIGINS
CORS_ORIGINS=https://your-frontend.vercel.app

# Redeploy backend
```

### Issue 2: Database Connection Failed

**Problem:** Backend can't connect to Supabase

**Solution:**
```bash
# Check DATABASE_URL format
# Should be: postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# Check Supabase project is active
# Check password is correct
```

### Issue 3: Images Not Uploading

**Problem:** Upload fails with "file not found"

**Solution:**
```bash
# Ensure IMAGE_STORAGE_PATH uses /data (Railway persistent disk)
IMAGE_STORAGE_PATH=/data/images

# Create directory on startup
# Add to main.py:
os.makedirs(settings.image_storage_path, exist_ok=True)
```

### Issue 4: ChromaDB Data Lost on Redeploy

**Problem:** Vector store resets after each deployment

**Solution:**
```bash
# Ensure Railway volume is mounted at /data
# Use CHROMADB_PERSIST_DIRECTORY=/data/chromadb

# Verify in Railway dashboard:
# Storage → chromadb-data → Mount path: /data
```

### Issue 5: LLM API Fails

**Problem:** Groq/Gemini API calls fail

**Solution:**
```bash
# Check API keys are set in Railway variables
# Ensure LLM_PROVIDER=groq (not lm_studio)
# Check API keys are valid
```

---

## Monitoring & Maintenance

### Railway Monitoring

1. Go to Railway dashboard
2. View **Metrics** (CPU, memory, disk)
3. Check **Logs** for errors
4. Monitor **Deployments** history

### Supabase Monitoring

1. Go to Supabase dashboard
2. View **Database** → **Metrics**
3. Check storage usage
4. Monitor query performance

### Vercel Monitoring

1. Go to Vercel dashboard
2. View **Analytics** (page views, bandwidth)
3. Check **Deployments** log
4. Monitor **Functions** (API calls)

---

## Scaling Up (When Free Tier is Not Enough)

When you hit free tier limits:

### Railway ($5-20/month)
- Upgrade to paid plan
- More RAM, CPU, disk
- Better performance

### Supabase (Pro plan - $25/month)
- 8GB database storage
- More connections
- Daily backups

### Vercel (Pro - $20/month)
- Unlimited bandwidth
- Faster builds
- Team collaboration

---

## Security Checklist

✅ **Environment Variables:** Never commit API keys
✅ **CORS:** Only allow your frontend domain
✅ **Database:** Use strong password, limit connections
✅ **HTTPS:** All services use automatic HTTPS
✅ **Rate Limiting:** Add rate limiting to API endpoints
✅ **Authentication:** Add user authentication if needed
✅ **File Upload:** Limit file size, validate file types

---

## Backup Strategy

### Database Backup (Supabase)
- Automatic daily backups (free tier)
- Export manually: Supabase → Database → Backups

### Vector Store Backup (ChromaDB)
```bash
# SSH into Railway service
railway shell

# Backup ChromaDB data
cd /data/chromadb
tar -czf chromadb-backup.tar.gz *

# Download to local machine
railway download chromadb-backup.tar.gz
```

### Code Backup (GitHub)
- Code is already on GitHub
- Ensure all changes are pushed

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel
3. ✅ Test all functionality
4. ✅ Set up monitoring
5. ✅ Add error tracking (Sentry - free tier)
6. ✅ Set up analytics (Plausible - free for personal)

---

**Status:** Ready to deploy!

**Estimated Time:** 1-2 hours for first deployment

**Ongoing Cost:** $0/month (free tiers)

**Support:** Railway, Vercel, Supabase all have excellent documentation
