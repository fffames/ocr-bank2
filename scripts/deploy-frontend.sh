#!/bin/bash

# OCR Bank - Frontend Deployment Script for Vercel
# This script helps deploy the frontend to Vercel

set -e

echo "🚀 Deploying OCR Bank Frontend to Vercel..."

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed."
    echo "Installing Vercel CLI..."
    npm install -g vercel
fi

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Create production environment file
if [ ! -f ".env.production" ]; then
    echo "Creating .env.production file..."
    echo "Please enter your backend URL (e.g., https://your-backend.up.railway.app):"
    read -r BACKEND_URL
    echo "VITE_API_URL=$BACKEND_URL" > .env.production
    echo "✅ Created .env.production"
fi

# Login to Vercel
echo "Logging in to Vercel..."
vercel login

# Deploy to Vercel
echo "Deploying frontend to Vercel..."
vercel --prod

echo ""
echo "✅ Frontend deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Copy your Vercel URL from the output above"
echo "2. Update CORS_ORIGINS in Railway with your Vercel URL"
echo "3. Redeploy backend to apply CORS changes"
echo "4. Test your deployed application"
echo ""
echo "📝 For detailed instructions, see DEPLOY_INSTRUCTIONS.md"