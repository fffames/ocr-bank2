# OCR Bank - Complete Deployment Guide

This guide provides step-by-step instructions for deploying OCR Bank to production for **FREE** using modern cloud platforms.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Folder Organization](#folder-organization)
4. [Deployment Steps](#deployment-steps)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

**Deployment Time:** 30-45 minutes
**Monthly Cost:** $0 (using free tiers)
**Architecture:** React (Vercel) + FastAPI (Railway) + PostgreSQL (Supabase)

### 30-Minute Quick Deploy

```bash
# 1. Prepare accounts (5 min)
# - GitHub, Railway, Vercel, Supabase

# 2. Deploy database (5 min)
# Create Supabase project

# 3. Deploy backend (10 min)
# Deploy to Railway with environment variables

# 4. Deploy frontend (10 min)
# Deploy to Vercel with API URL

# 5. Test (5 min)
# Verify all services working
```

---

## 📦 Prerequisites

### Required Accounts

1. **GitHub** - Code hosting
   - Sign up: https://github.com/signup

2. **Railway** - Backend hosting
   - Sign up: https://railway.app
   - Login with GitHub

3. **Vercel** - Frontend hosting
   - Sign up: https://vercel.com
   - Login with GitHub

4. **Supabase** - Database hosting
   - Sign up: https://supabase.com
   - Login with GitHub

### Required API Keys

1. **Groq API** (Free LLM)
   - Get key: https://console.groq.com
   - Free tier available

2. **Gemini API** (Google AI)
   - Get key: https://ai.google.dev
   - Free tier available

3. **Google Sheets API** (Optional)
   - Credentials JSON file
   - Spreadsheet ID

### Required Tools

```bash
# Install Vercel CLI
npm install -g vercel

# Install Railway CLI (optional)
npm install -g railway

# Verify installations
vercel --version
railway --version
```

---

## 📁 Folder Organization

### Current Structure Analysis

The project has some temporary files and test files that should be better organized:

```
ocr-bank2/
├── backend/              # ✅ Well-organized
│   ├── app/             # Application code
│   ├── tests/           # Test files
│   ├── config/          # Configuration files
│   └── *.py             # Loose utility scripts (to be organized)
├── frontend/            # ✅ Well-organized
│   ├── src/
│   ├── dist/
│   └── package.json
├── docs/                # ✅ Documentation
├── *.md                 # ❌ Loose markdown files (to be organized)
├── *.jpg, *.png         # ❌ Loose test images (to be organized)
└── docker-compose.yml   # ✅ Docker config
```

### Recommended Organization

```
ocr-bank2/
├── backend/
│   ├── app/                    # Main application
│   ├── tests/                  # All test files
│   ├── scripts/                # Utility scripts (new)
│   ├── config/                 # Configuration files
│   ├── data/                   # Local data storage
│   ├── images/                 # Uploaded images
│   ├── logs/                   # Application logs
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── dist/
│   └── package.json
├── deployment/                 # Deployment configs (new)
│   ├── railway/
│   ├── vercel/
│   └── supabase/
├── docs/                       # All documentation
│   ├── guides/
│   ├── api/
│   └── deployment/
├── tests/                      # Test images and data (new)
│   ├── images/
│   └── data/
├── scripts/                    # Deployment scripts (new)
├── README.md                   # Main README
├── docker-compose.yml
├── railway.toml
└── .gitignore
```

---

## 🚀 Deployment Steps

### Step 1: Organize Project Folders

Let me organize the project structure first:

```bash
# Create organized folder structure
mkdir -p deployment/railway deployment/vercel deployment/supabase
mkdir -p tests/images tests/data
mkdir -p scripts
mkdir -p docs/guides docs/api docs/deployment

# Move test images to tests/images/
mv *.jpg *.png *.JPG *.PNG tests/images/ 2>/dev/null

# Move utility scripts to backend/scripts/
mkdir -p backend/scripts
mv backend/*.py tests/ backend/scripts/ 2>/dev/null

# Move deployment docs to docs/deployment/
mv DEPLOYMENT*.md DEPLOY_INSTRUCTIONS.md docs/deployment/ 2>/dev/null
mv API-ENDPOINTS.md docs/api/ 2>/dev/null
```

### Step 2: Deploy Database (Supabase)

#### 2.1 Create Supabase Project

1. Go to https://supabase.com
2. Click **"Start your project"**
3. Configure project:
   - **Name:** `ocr-bank-db`
   - **Database Password:** Generate strong password (save it!)
   - **Region:** Southeast Asia (Singapore)
   - **Pricing Plan:** Free
4. Click **"Create new project"**
5. Wait 2-3 minutes for project to be ready

#### 2.2 Get Database Connection String

1. In Supabase dashboard, go to **Settings** → **Database**
2. Find **Connection string** → **URI**
3. Select **Python** language
4. Copy the connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```

#### 2.3 Configure Database Settings

1. In Supabase dashboard, go to **Settings** → **Database**
2. Under **Connection pooling**, enable:
   - **Connection pooling:** Transaction mode
   - **Pool size:** 15
3. Save settings

**✅ Checklist:**
- [ ] Supabase project created
- [ ] Database password saved securely
- [ ] Connection string copied
- [ ] Connection pooling enabled

### Step 3: Deploy Backend (Railway)

#### 3.1 Push Code to GitHub

```bash
# If not already on GitHub
git init
git add .
git commit -m "Prepare for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ocr-bank2.git
git push -u origin main
```

#### 3.2 Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `ocr-bank2` repository
4. Click **"Deploy Now"**

#### 3.3 Configure Deployment

1. In Railway dashboard, click on your project
2. Go to **Settings** tab
3. Configure:
   - **Root Directory:** `backend`
   - **Python Version:** `3.11`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### 3.4 Set Environment Variables

Go to **Variables** tab and add:

```bash
# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# OCR Configuration
OCR_LANGUAGE=th
OCR_DEVICE=cpu

# LLM Configuration
GROQ_API_KEY=gsk_your_actual_key_here
GEMINI_API_KEY=AIzayour_actual_key_here
LLM_PROVIDER=groq

# VLM Configuration
VLM_PROVIDER=groq
LOCAL_LLM_URL=

# Vector Store
CHROMADB_PERSIST_DIRECTORY=/data/chromadb

# File Storage
IMAGE_STORAGE_PATH=/data/images
MAX_UPLOAD_SIZE=10485760

# Google Sheets (Optional)
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# CORS (update after frontend deployment)
CORS_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app

# Server Configuration
PORT=8000
PYTHON_VERSION=3.11
```

#### 3.5 Add Persistent Disk

1. In Railway service, go to **Storage** tab
2. Click **"+ New Volume"**
3. Create volume:
   - **Name:** `chromadb-data`
   - **Mount path:** `/data`
4. Click **"Create Volume"**

#### 3.6 Deploy Backend

1. Click **"Deploy"** button
2. Wait for deployment (2-3 minutes)
3. Copy your Railway URL: `https://your-app.up.railway.app`
4. Test health check:
   ```bash
   curl https://your-app.up.railway.app/health
   ```

**✅ Checklist:**
- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables configured
- [ ] Persistent disk added
- [ ] Backend deployed successfully
- [ ] Health check passing

### Step 4: Deploy Frontend (Vercel)

#### 4.1 Install Vercel CLI

```bash
npm install -g vercel
vercel login
```

#### 4.2 Create Production Environment File

Create `frontend/.env.production`:

```bash
VITE_API_URL=https://your-backend.up.railway.app
```

#### 4.3 Deploy Frontend

```bash
cd frontend

# Deploy to Vercel
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your username
# - Link to existing project? No
# - Project name: ocr-bank-frontend
# - Directory: ./
# - Override settings? No
```

#### 4.4 Configure Environment Variables

1. Go to https://vercel.com/dashboard
2. Select your project (ocr-bank-frontend)
3. Go to **Settings** → **Environment Variables**
4. Add variable:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://your-backend.up.railway.app`
5. Click **"Save"**
6. Redeploy:
   ```bash
   vercel --prod
   ```

#### 4.5 Update Backend CORS

1. Go back to Railway dashboard
2. Update `CORS_ORIGINS` variable:
   ```bash
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```
3. Railway will automatically redeploy

**✅ Checklist:**
- [ ] Vercel CLI installed
- [ ] Frontend deployed
- [ ] Environment variables configured
- [ ] Backend CORS updated
- [ ] Frontend URL obtained

---

## ⚙️ Configuration

### Environment Variables Reference

#### Backend Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` | ✅ Yes |
| `GROQ_API_KEY` | Groq API key for LLM | `gsk_...` | ✅ Yes |
| `GEMINI_API_KEY` | Gemini API key for LLM | `AIza...` | ✅ Yes |
| `LLM_PROVIDER` | LLM provider to use | `groq` | ✅ Yes |
| `OCR_LANGUAGE` | OCR language | `th` | ✅ Yes |
| `OCR_DEVICE` | Device for OCR | `cpu` | ✅ Yes |
| `CHROMADB_PERSIST_DIRECTORY` | Vector store path | `/data/chromadb` | ✅ Yes |
| `IMAGE_STORAGE_PATH` | Image storage path | `/data/images` | ✅ Yes |
| `CORS_ORIGINS` | Allowed CORS origins | `https://...` | ✅ Yes |
| `PORT` | Server port | `8000` | ✅ Yes |

#### Frontend Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `VITE_API_URL` | Backend API URL | `https://...` | ✅ Yes |

---

## 🧪 Testing

### Backend Testing

```bash
# Test health endpoint
curl https://your-backend.up.railway.app/health

# Test API documentation
# Open in browser: https://your-backend.up.railway.app/docs

# Test database connection
curl https://your-backend.up.railway.app/api/receipts/

# Test upload (with small image)
curl -X POST \
  -F "files=@test-image.jpg" \
  https://your-backend.up.railway.app/api/upload/
```

### Frontend Testing

```bash
# Open your Vercel URL
# https://your-frontend.vercel.app

# Check browser console for errors
# Test image upload
# Verify receipt display
```

### Database Testing

1. Go to Supabase dashboard
2. Click **Table Editor** → `receipts`
3. Verify data appears after upload
4. Check **Database** → **Logs** for any errors

### End-to-End Test

1. **Upload Test:**
   - Go to deployed frontend
   - Upload a receipt image
   - Verify OCR processing works
   - Check receipt appears in list

2. **Database Test:**
   - Verify receipt stored in Supabase
   - Check all fields populated correctly

3. **Search Test:**
   - Use search functionality
   - Verify results appear

**✅ Testing Checklist:**
- [ ] Backend health check passes
- [ ] API documentation accessible
- [ ] Frontend loads correctly
- [ ] Image upload works
- [ ] OCR processing works
- [ ] Database stores data
- [ ] Search functionality works
- [ ] No console errors

---

## 📊 Monitoring

### Railway Monitoring

**Dashboard:** https://railway.app/dashboard

1. **Metrics Tab:**
   - CPU usage
   - Memory usage
   - Disk usage
   - Network traffic

2. **Logs Tab:**
   - Application logs
   - Error messages
   - Request/response logs

3. **Deployments Tab:**
   - Deployment history
   - Build status
   - Rollback options

### Vercel Monitoring

**Dashboard:** https://vercel.com/dashboard

1. **Analytics Tab:**
   - Page views
   - Bandwidth usage
   - Geographic distribution

2. **Deployments Tab:**
   - Deployment history
   - Build times
   - Preview URLs

3. **Functions Tab:**
   - API performance
   - Execution time
   - Error rates

### Supabase Monitoring

**Dashboard:** https://supabase.com/dashboard

1. **Database → Metrics:**
   - Query performance
   - Connection count
   - Storage usage

2. **Database → Logs:**
   - Slow queries
   - Error logs
   - Connection issues

---

## 🔧 Troubleshooting

### Common Issues

#### 1. CORS Errors

**Problem:** Frontend can't connect to backend

**Solution:**
```bash
# In Railway, update CORS_ORIGINS
CORS_ORIGINS=https://your-frontend.vercel.app

# Redeploy backend
```

#### 2. Database Connection Failed

**Problem:** Backend can't connect to Supabase

**Solution:**
```bash
# Check DATABASE_URL format
# Should be: postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# Verify Supabase project is active (not paused)
# Check password is correct
```

#### 3. Images Not Uploading

**Problem:** Upload fails with "file not found"

**Solution:**
```bash
# Ensure IMAGE_STORAGE_PATH uses /data (Railway persistent disk)
IMAGE_STORAGE_PATH=/data/images

# Verify directory creation on startup
# Check backend/app/main.py has:
os.makedirs(settings.image_storage_path, exist_ok=True)
```

#### 4. ChromaDB Data Lost

**Problem:** Vector store resets after redeploy

**Solution:**
```bash
# Verify Railway volume is mounted at /data
# Use CHROMADB_PERSIST_DIRECTORY=/data/chromadb

# Check in Railway dashboard:
# Storage → chromadb-data → Mount path: /data
```

#### 5. LLM API Fails

**Problem:** Groq/Gemini API calls fail

**Solution:**
```bash
# Check API keys are set in Railway variables
# Ensure LLM_PROVIDER=groq (not lm_studio)
# Verify API keys are valid and not expired
```

#### 6. Build Failures

**Problem:** Deployment fails during build

**Solution:**
```bash
# Check Railway build logs
# Verify requirements.txt has all dependencies
# Check Python version is 3.11
# Ensure no syntax errors in code
```

### Debug Mode

Enable debug logging in Railway:

```bash
# Add to Railway variables
LOG_LEVEL=debug
DEBUG=true
```

---

## 🎯 Post-Deployment

### Security Checklist

- [ ] API keys not exposed in code
- [ ] CORS origins limited to your domain
- [ ] Database password is strong
- [ ] Rate limiting configured (if needed)
- [ ] HTTPS enabled (automatic on Vercel/Railway)
- [ ] File upload size limits set
- [ ] Input validation on all endpoints

### Performance Optimization

1. **Enable Caching:**
   ```bash
   # Add to backend
   # Use CDN for static files
   # Cache API responses
   ```

2. **Optimize Images:**
   ```bash
   # Compress images before upload
   # Use WebP format
   # Implement lazy loading
   ```

3. **Database Indexing:**
   ```bash
   # Add indexes to frequently queried fields
   # Monitor slow queries in Supabase
   ```

### Backup Strategy

**Weekly:**
1. Export Supabase database
2. Backup ChromaDB data from Railway
3. Verify backups work

**Monthly:**
1. Test restore from backup
2. Review and rotate API keys
3. Update dependencies

### Scaling Up

When you hit free tier limits:

**Railway ($5-20/month):**
- Upgrade to paid plan
- More RAM, CPU, disk
- Better performance

**Supabase (Pro plan - $25/month):**
- 8GB database storage
- More connections
- Daily backups

**Vercel (Pro - $20/month):**
- Unlimited bandwidth
- Faster builds
- Team collaboration

---

## 📝 Maintenance

### Regular Tasks

**Daily:**
- Check service status
- Review error logs
- Monitor usage metrics

**Weekly:**
- Backup database
- Check for updates
- Review security logs

**Monthly:**
- Update dependencies
- Test backups
- Review costs
- Optimize performance

---

## 🎉 Success!

Your OCR Bank is now live and free!

**Your URLs:**
- Frontend: `https://your-frontend.vercel.app`
- Backend: `https://your-backend.up.railway.app`
- Database: Supabase dashboard

**Monthly Cost:** $0 (free tiers)

**Deployment Time:** 30-45 minutes

**Next Steps:**
1. Set up custom domain (optional)
2. Add error tracking (Sentry - free tier)
3. Set up analytics (Plausible - free for personal)
4. Add rate limiting (prevent abuse)
5. Add user authentication (if needed)

---

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)

---

**Last Updated:** May 2026
**Version:** 1.0
**Status:** ✅ Production Ready