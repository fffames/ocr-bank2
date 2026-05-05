# 🚀 Quick Deploy Guide - OCR Bank

Get OCR Bank deployed to production for **FREE** in 30 minutes!

---

## ⏱️ 30-Minute Quick Deploy

### Pre-Deployment (5 min)

**1. Create Accounts**
- [ ] GitHub: https://github.com/signup
- [ ] Railway: https://railway.app (login with GitHub)
- [ ] Vercel: https://vercel.com (login with GitHub)
- [ ] Supabase: https://supabase.com (login with GitHub)

**2. Get API Keys**
- [ ] Groq API: https://console.groq.com (free)
- [ ] Gemini API: https://ai.google.dev (free)

**3. Organize Project**
```bash
cd /Users/boonkerdinchoi/Downloads/year\ 4/ocr_bank/ocr-bank2
./scripts/organize-project.sh
```

---

## Step 1: Deploy Database (5 min)

**Create Supabase Project:**
1. Go to https://supabase.com
2. Click "Start your project"
3. **Name:** `ocr-bank-db`
4. **Password:** Generate and save securely!
5. **Region:** Southeast Asia (Singapore)
6. Click "Create new project"

**Get Connection String:**
1. In Supabase dashboard: **Settings** → **Database**
2. Find **Connection string** → **URI**
3. Select **Python** language
4. Copy connection string: `postgresql://postgres...`

---

## Step 2: Deploy Backend (10 min)

**Option A: Automated Script**
```bash
./scripts/deploy-backend.sh
```

**Option B: Manual**
1. Go to https://railway.app
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `ocr-bank2` repository
4. Click **Deploy Now**

**Set Environment Variables:**
In Railway dashboard, add these variables:

```bash
# Database (from Supabase)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres

# LLM (use your actual API keys)
GROQ_API_KEY=gsk_your_actual_key
GEMINI_API_KEY=AIzayour_actual_key
LLM_PROVIDER=groq

# OCR & Storage
OCR_LANGUAGE=th
OCR_DEVICE=cpu
CHROMADB_PERSIST_DIRECTORY=/data/chromadb
IMAGE_STORAGE_PATH=/data/images

# CORS (update after frontend deployment)
CORS_ORIGINS=http://localhost:5173

# Port
PORT=8000
```

**Add Persistent Disk:**
1. In Railway service: **Storage** tab
2. Click **+ New Volume**
3. **Name:** `chromadb-data`
4. **Mount path:** `/data`
5. Click **Create Volume**

**Deploy:**
1. Click **Deploy** button
2. Wait 2-3 minutes
3. Copy your Railway URL: `https://your-app.up.railway.app`

---

## Step 3: Deploy Frontend (10 min)

**Option A: Automated Script**
```bash
./scripts/deploy-frontend.sh
```

**Option B: Manual**
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

**Set Environment Variable:**
1. Go to https://vercel.com/dashboard
2. Select your project
3. **Settings** → **Environment Variables**
4. Add:
   - **Name:** `VITE_API_URL`
   - **Value:** `https://your-backend.up.railway.app`
5. Click **Save**
6. Redeploy: `vercel --prod`

---

## Step 4: Final Configuration (2 min)

**Update Backend CORS:**
1. Go back to Railway dashboard
2. Update `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```
3. Railway will automatically redeploy

---

## Step 5: Test Deployment (3 min)

**Automated Testing:**
```bash
./scripts/test-deployment.sh https://your-backend.up.railway.app https://your-frontend.vercel.app
```

**Manual Testing:**

1. **Frontend:**
   - Open your Vercel URL
   - Should see OCR Bank homepage

2. **Backend:**
   - Open: `https://your-backend.up.railway.app/docs`
   - Should see FastAPI documentation

3. **Upload Test:**
   - Upload a receipt image
   - Verify it appears in receipts list

---

## ✅ Success!

Your OCR Bank is now live!

**Your URLs:**
- Frontend: `https://your-frontend.vercel.app`
- Backend: `https://your-backend.up.railway.app`
- Database: Supabase dashboard

**Monthly Cost:** $0 (free tiers)

---

## 📚 Additional Information

**Detailed Instructions:** See [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)

**Troubleshooting:** See [DEPLOY_INSTRUCTIONS.md#troubleshooting](DEPLOY_INSTRUCTIONS.md#troubleshooting)

**Monitoring:** See [DEPLOY_INSTRUCTIONS.md#monitoring](DEPLOY_INSTRUCTIONS.md#monitoring)

---

## 🆘 Need Help?

**Common Issues:**
- CORS errors → Update `CORS_ORIGINS` in Railway
- Database errors → Check `DATABASE_URL` in Railway
- Upload failures → Check persistent disk is mounted at `/data`

**Resources:**
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Supabase Docs: https://supabase.com/docs

---

**Time:** ~30 minutes | **Cost:** $0/month | **Status:** ✅ Production Ready