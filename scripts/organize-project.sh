#!/bin/bash

# OCR Bank - Project Organization Script
# This script organizes the project structure for deployment

set -e

echo "🗂️  Organizing OCR Bank project structure..."

# Create organized folder structure
echo "Creating folder structure..."
mkdir -p deployment/railway deployment/vercel deployment/supabase
mkdir -p tests/images tests/data
mkdir -p backend/scripts
mkdir -p docs/guides docs/api docs/deployment

# Move test images
echo "Moving test images..."
find . -maxdepth 1 -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.JPG" -o -name "*.PNG" \) -exec mv {} tests/images/ \; 2>/dev/null || true

# Move backend utility scripts
echo "Moving backend utility scripts..."
find backend -maxdepth 1 -type f -name "*.py" ! -name "main.py" ! -name "config.py" -exec mv {} backend/scripts/ \; 2>/dev/null || true

# Move deployment docs
echo "Moving deployment documentation..."
mv DEPLOYMENT*.md SETUP-COMPLETE.md VLM_SETUP.md docs/deployment/ 2>/dev/null || true
mv API-ENDPOINTS.md docs/api/ 2>/dev/null || true
mv TESTING_GUIDE.md FIX_SUMMARY.md docs/guides/ 2>/dev/null || true

# Clean up any .DS_Store files
echo "Cleaning up .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null || true

echo "✅ Project organization complete!"
echo ""
echo "📁 New structure:"
tree -L 2 -I 'node_modules|__pycache__|*.pyc|venv|env|.git' -a || ls -la

echo ""
echo "🚀 Ready for deployment! See DEPLOY_INSTRUCTIONS.md for details."