#!/bin/bash

# OCR Bank - Backend Deployment Script for Railway
# This script helps deploy the backend to Railway

set -e

echo "🚀 Deploying OCR Bank Backend to Railway..."

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "Installing Railway CLI..."
    npm install -g railway
fi

# Check if logged in to Railway
echo "Logging in to Railway..."
railway login || true

# Check if project is initialized
if ! git remote get-url origin &> /dev/null; then
    echo "⚠️  Git remote not set. Please push your code to GitHub first."
    echo "1. Create a new repository on GitHub"
    echo "2. Run: git remote add origin https://github.com/YOUR_USERNAME/ocr-bank2.git"
    echo "3. Run: git push -u origin main"
    exit 1
fi

# Initialize Railway project
echo "Initializing Railway project..."
railway init

# Deploy backend
echo "Deploying backend..."
railway up

echo "Adding environment variables..."
echo "Please enter the following environment variables in Railway dashboard:"
echo ""
echo "Required Variables:"
echo "  DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres"
echo "  GROQ_API_KEY=gsk_your_key_here"
echo "  GEMINI_API_KEY=AIzayour_key_here"
echo "  LLM_PROVIDER=groq"
echo "  OCR_LANGUAGE=th"
echo "  OCR_DEVICE=cpu"
echo "  CHROMADB_PERSIST_DIRECTORY=/data/chromadb"
echo "  IMAGE_STORAGE_PATH=/data/images"
echo "  CORS_ORIGINS=http://localhost:5173"
echo "  PORT=8000"
echo ""

# Open Railway dashboard
echo "Opening Railway dashboard..."
railway open

echo "✅ Backend deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Set environment variables in Railway dashboard"
echo "2. Add persistent disk (/data) in Railway storage settings"
echo "3. Wait for deployment to complete"
echo "4. Copy your Railway URL"
echo "5. Update frontend with backend URL"
echo ""
echo "📝 For detailed instructions, see DEPLOY_INSTRUCTIONS.md"