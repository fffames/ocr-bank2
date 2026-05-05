# Quick Deployment Checklist

Follow this checklist to deploy OCR Bank for free in 30 minutes.

## Pre-Deployment (5 minutes)

### 1. Prepare Your Accounts

- [ ] GitHub account (for code hosting)
- [ ] Railway account (https://railway.app - login with GitHub)
- [ ] Vercel account (https://vercel.com - login with GitHub)
- [ ] Supabase account (https://supabase.com - login with GitHub)

### 2. Prepare API Keys

- [ ] Groq API key (https://console.groq.com - free)
- [ ] Gemini API key (https://ai.google.dev - free)
- [ ] Google Sheets credentials JSON file
- [ ] Google Sheets spreadsheet ID

### 3. Update Environment Files

- [ ] Copy `frontend/.env.production.example` → `frontend/.env.production`
- [ ] Copy `backend/.env.production.example` → use for Railway variables (not a file)

---

## Step 1: Deploy Database (5 minutes)

### Create Supabase Project

1. Go to https://supabase.com
2. Click "Start your project"
3. **Project name:** ocr-bank-db
4. **Database password:** Generate and save securely!
5. **Region:** Southeast Asia (Singapore)
6. Click "Create new project"

### Get Database URL

1. In Supabase dashboard, go to **Settings** → **Database**
2. Find **Connection string** → **URI**
3. Select **Python** language
4. Copy connection string (looks like `postgresql://postgres...`)
5. Save it for Railway setup

**Checklist:**
- [ ] Supabase project created
- [ ] Database connection string copied

---

## Step 2: Deploy Backend (10 minutes)

### Deploy to Railway

1. Go to https://railway.app
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `ocr-bank2` repository
4. Configure:
   - **Root directory:** `backend`
   - **Python version:** 3.11

### Set Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```bash
# Database (from Supabase - use your actual connection string)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres

# OCR
OCR_LANGUAGE=th
OCR_DEVICE=cpu

# LLM (use your actual API keys)
GROQ_API_KEY=gsk_your_actual_key_here
GEMINI_API_KEY=AIzayour_actual_key_here
LLM_PROVIDER=groq

# VLM
VLM_PROVIDER=groq

# Vector Store
CHROMADB_PERSIST_DIRECTORY=/data/chromadb

# File Storage
IMAGE_STORAGE_PATH=/data/images
MAX_UPLOAD_SIZE=10485760

# CORS (we'll update this after frontend deployment)
CORS_ORIGINS=http://localhost:5173

# Port
PORT=8000
```

### Add Persistent Disk

1. In Railway service, go to **Storage** tab
2. Click **+ New Volume**
3. Create volume:
   - **Name:** chromadb-data
   - **Mount path:** `/data`

### Deploy

1. Click **Deploy** button
2. Wait for deployment (2-3 minutes)
3. Copy your Railway URL: `https://your-app.up.railway.app`

**Checklist:**
- [ ] Railway project created
- [ ] Environment variables set
- [ ] Persistent disk added
- [ ] Backend deployed successfully
- [ ] Backend URL copied

---

## Step 3: Deploy Frontend (10 minutes)

### Deploy to Vercel

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy frontend:
   ```bash
   cd frontend
   vercel
   ```

4. Follow prompts:
   - **Set up and deploy?** Yes
   - **Which scope?** Your username
   - **Link to existing project?** No
   - **Project name:** ocr-bank-frontend
   - **Directory:** `./`
   - **Override settings?** No

### Set Environment Variables

1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add variable:
   ```
   NAME: VITE_API_URL
   VALUE: https://your-backend.up.railway.app
   ```
5. Click **Save**
6. Redeploy (variables apply on next deployment)

**Checklist:**
- [ ] Vercel CLI installed
- [ ] Frontend deployed
- [ ] Environment variable set
- [ ] Frontend URL obtained

---

## Step 4: Final Configuration (5 minutes)

### Update Backend CORS

1. Go back to Railway dashboard
2. Update `CORS_ORIGINS` variable:
   ```bash
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```
3. Railway will automatically redeploy

### Update Frontend Image Paths

If needed, update image path handling in frontend to use deployed backend URL.

**Checklist:**
- [ ] CORS origins updated
- [ ] Backend redeployed

---

## Step 5: Test Deployment (5 minutes)

### Health Checks

1. **Frontend:**
   - Open your Vercel URL
   - Should see OCR Bank homepage
   - Check browser console for errors

2. **Backend:**
   - Open: `https://your-backend.railway.app/`
   - Should see FastAPI documentation
   - Or: `https://your-backend.railway.app/docs`

3. **Database:**
   - Go to Supabase dashboard
   - Check **Table Editor** → `receipts` table exists

### Upload Test

1. In deployed frontend, upload a test receipt
2. Check it appears in receipts list
3. Verify data in Supabase database

**Checklist:**
- [ ] Frontend loads correctly
- [ ] Backend API responds
- [ ] Database connection works
- [ ] Test upload successful

---

## Troubleshooting

### Frontend Can't Connect to Backend

**Error:** CORS error or network error

**Fix:**
1. Check `CORS_ORIGINS` in Railway includes your Vercel URL
2. Check `VITE_API_URL` in Vercel is correct
3. Redeploy both services

### Database Connection Failed

**Error:** Backend can't connect to Supabase

**Fix:**
1. Check `DATABASE_URL` in Railway is correct
2. Verify Supabase project is active (not paused)
3. Check password in connection string

### Images Not Uploading

**Error:** Upload fails

**Fix:**
1. Check `IMAGE_STORAGE_PATH=/data/images` in Railway
2. Verify persistent disk is mounted at `/data`
3. Check Railway logs for errors

### ChromaDB Data Lost

**Error:** Vector store resets after redeploy

**Fix:**
1. Verify Railway volume exists
2. Check mount path is `/data`
3. Verify `CHROMADB_PERSIST_DIRECTORY=/data/chromadb`

---

## Post-Deployment

### Monitor Your Services

**Railway:**
- Dashboard shows CPU, memory, disk usage
- Logs tab shows error messages
- Metrics tab shows request/response times

**Vercel:**
- Analytics tab shows page views, bandwidth
- Deployments tab shows deployment history
- Functions tab shows API performance

**Supabase:**
- Database → Metrics shows query performance
- Database → Logs shows slow queries
- Storage shows file usage

### Backup Strategy

**Weekly:**
1. Export Supabase database
2. Backup ChromaDB data from Railway
3. Verify backups work

**Monthly:**
1. Test restore from backup
2. Review and rotate API keys
3. Update dependencies

---

## Success! 🎉

Your OCR Bank is now live and free!

**Your URLs:**
- Frontend: `https://your-frontend.vercel.app`
- Backend: `https://your-backend.up.railway.app`
- Database: Supabase dashboard

**Monthly Cost:** $0 (free tiers)

**Next Steps:**
1. Set up custom domain (optional)
2. Add error tracking (Sentry - free tier)
3. Set up analytics (Plausible - free for personal)
4. Add rate limiting (prevent abuse)
5. Add user authentication (if needed)

---

**Deployment Time:** ~30 minutes
**Ongoing Cost:** $0/month
**Maintenance:** Minimal (monitor and backup)
