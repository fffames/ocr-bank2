# Deploy OCR Bank for Free - Complete Guide

Your OCR Bank project is ready to deploy for free! This guide walks you through deploying to production using free-tier cloud services.

## 🚀 Quick Start (30 minutes)

### What You'll Deploy

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │      │    Backend      │      │   Database      │
│   (Vercel)      │ ←→   │   (Railway)     │ ←→   │  (Supabase)     │
│   React + Vite  │      │   FastAPI       │      │   PostgreSQL    │
│   Free forever  │      │   $5 credit/mo  │      │   500MB free    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                ↓
                         ChromaDB (Vector Store)
                         Groq/Gemini (LLM APIs)
                         Google Sheets (Export)
```

### Services Used (All Free!)

| Service | Purpose | Free Tier | Cost |
|---------|---------|-----------|------|
| **Vercel** | Frontend hosting | Unlimited | $0 |
| **Railway** | Backend hosting | $5 credit/mo | $0 |
| **Supabase** | Database | 500MB storage | $0 |
| **Groq** | LLM API | Free tier | $0 |
| **Google Sheets** | Export | Personal use | $0 |
| **Total** | - | - | **$0/mo** |

## 📋 Prerequisites

Before you start, make sure you have:

1. ✅ GitHub account (for code hosting)
2. ✅ Railway account (https://railway.app)
3. ✅ Vercel account (https://vercel.com)
4. ✅ Supabase account (https://supabase.com)
5. ✅ API keys:
   - Groq API key (https://console.groq.com)
   - Gemini API key (https://ai.google.dev)

## 🎯 Deployment Checklist

Follow the step-by-step checklist:

**[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)**

This will walk you through:
1. ✅ Deploy database (Supabase) - 5 minutes
2. ✅ Deploy backend (Railway) - 10 minutes
3. ✅ Deploy frontend (Vercel) - 10 minutes
4. ✅ Configure and test - 5 minutes

## 📖 Detailed Documentation

For detailed information, see:

**[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

This comprehensive guide includes:
- Architecture overview
- Service configurations
- Environment variables
- Troubleshooting guide
- Scaling strategies
- Backup procedures
- Security checklist

## 🛠️ Files Created for Deployment

### Configuration Files
- `railway.toml` - Railway deployment configuration
- `.railwayignore` - Files to exclude from Railway
- `frontend/.env.production.example` - Frontend environment template
- `backend/.env.example` - Backend environment template (production-ready)

### Code Updates
- `frontend/src/services/api.ts` - Uses environment variables for API URL
- `frontend/src/vite-env.d.ts` - TypeScript definitions for Vite env vars
- `backend/app/config.py` - Production-ready configuration with /tmp paths
- `backend/app/main.py` - Startup event for directory creation
- `backend/.env` - Local development (NOT for deployment)
- `backend/.env.example` - Template for deployment (safe to commit)

### Security Improvements
- ✅ API keys removed from code
- ✅ `.env.example` file created with safe placeholders
- ✅ Local LLM dependencies removed (no more LM Studio)
- ✅ Production-ready path defaults (`/tmp` for cloud environments)
- ✅ JWT secret key configuration

## 🔧 Key Changes from Development

### Frontend Changes
1. **API URL**: Now uses `VITE_API_URL` environment variable
2. **Image paths**: Updated to work with deployed backend
3. **Environment-aware**: Automatically switches between dev and production

### Backend Changes
1. **CORS**: Reads allowed origins from environment variable
2. **Directories**: Creates required directories on startup
3. **Static files**: Uses configurable image storage path
4. **Environment**: Production-ready configuration

## 🚦 Common Issues & Fixes

### Issue: CORS Errors
**Problem:** Frontend can't connect to backend
**Fix:** Update `CORS_ORIGINS` in Railway with your Vercel URL

### Issue: Database Connection Failed
**Problem:** Backend can't connect to Supabase
**Fix:** Verify `DATABASE_URL` in Railway is correct

### Issue: Images Not Uploading
**Problem:** Upload fails with file errors
**Fix:** Ensure Railway persistent disk is mounted at `/data`

### Issue: ChromaDB Data Lost
**Problem:** Vector store resets after redeployment
**Fix:** Verify Railway volume is mounted at `/data`

For more troubleshooting, see the [Deployment Guide](./DEPLOYMENT_GUIDE.md).

## 📊 Monitoring Your Deployment

### Railway (Backend)
- URL: https://railway.app
- Monitor: CPU, memory, disk usage
- Logs: Error messages and request logs
- Metrics: Response times, request counts

### Vercel (Frontend)
- URL: https://vercel.com/dashboard
- Analytics: Page views, bandwidth
- Deployments: Build and deployment history
- Functions: API performance

### Supabase (Database)
- URL: https://supabase.com/dashboard
- Database: Query performance, storage
- Logs: Slow queries, errors
- Storage: File storage usage

## 🔒 Security Checklist

- [x] Never commit API keys to GitHub (`.env` in `.gitignore`)
- [x] Use `.env.example` template for deployment
- [x] Local LLM dependencies removed (security improvement)
- [ ] Use strong password for database
- [ ] Limit CORS to your frontend domain only
- [ ] Add rate limiting to API endpoints
- [ ] Validate and sanitize user inputs
- [ ] Use HTTPS (automatic on all platforms)
- [ ] Generate secure `SECRET_KEY` for production (not the default)
- [ ] Regular security updates
- [ ] Monitor for suspicious activity

## 🆕 Recent Updates (May 2026)

### Security & Configuration Improvements
- **Removed Local LLM Dependencies**: No more LM Studio or local Gemma dependencies
- **API Key Management**: Created `.env.example` template for safe deployment
- **Production-Ready Paths**: Default paths now use `/tmp` for cloud compatibility
- **Environment Variables**: Updated all configuration to use environment variables
- **Cleaner Codebase**: Removed unused local LLM service files

### Files Changed
- ✅ `backend/.env.example` - New production template (safe to commit)
- ✅ `backend/.env` - Updated for local development (not for deployment)
- ✅ `backend/app/config.py` - Removed local LLM options
- ✅ `backend/app/api/upload.py` - Removed LM Studio fallback
- ✅ `backend/app/services/llm_interface.py` - Simplified to cloud APIs only
- ✅ `backend/app/services/lm_studio_vlm_service.py` - Removed (no longer needed)

### Deployment Benefits
1. **Simpler Setup**: No local LLM configuration needed
2. **Better Security**: API keys properly managed
3. **Cloud-Ready**: Uses cloud APIs (Gemini, Groq) instead of local models
4. **Cleaner Code**: Removed unused dependencies and files
5. **Easier Debugging**: Fewer moving parts in production

## 💰 Cost Summary

### Free Tier Limits
- **Vercel**: Unlimited bandwidth, 100GB/month
- **Railway**: $5 credit/month (~512MB RAM)
- **Supabase**: 500MB database, 1GB storage
- **Groq API**: Free tier (generous limits)

### When to Upgrade
- More than 10,000 requests/month
- Database > 500MB
- Need faster response times
- Multiple users/collaborators

### Paid Plans (if needed)
- Railway Pro: $20/month
- Supabase Pro: $25/month
- Vercel Pro: $20/month

## 🎉 Success!

Your OCR Bank is now live and accessible from anywhere!

**Your URLs:**
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-backend.up.railway.app`
- Database: Supabase dashboard

**Monthly Cost:** $0 (free tiers)

**Maintenance:** Minimal (monitor and backup)

## 🆘 Support

If you encounter issues:

1. Check the [Deployment Guide](./DEPLOYMENT_GUIDE.md) troubleshooting section
2. Review Railway/Vercel/Supabase logs
3. Verify environment variables are set correctly
4. Check CORS configuration
5. Test database connection

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Railway Volumes](https://docs.railway.app/reference/volumes)

---

**Ready to deploy?** Start with the [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md)!

**Total Time:** ~30 minutes
**Total Cost:** $0/month
**Difficulty:** Beginner-friendly

Good luck with your deployment! 🚀
