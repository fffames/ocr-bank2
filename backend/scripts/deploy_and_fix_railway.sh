#!/bin/bash
# Railway deployment script with all fixes

echo "🚀 OCR Bank - Railway Deployment Script"
echo "========================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set!"
    echo "   Get it from Railway Dashboard → PostgreSQL Service → Variables"
    exit 1
fi

echo "✅ DATABASE_URL found"

# Run chat history schema migration
echo ""
echo "📝 Step 1: Fixing chat_history schema..."
cd backend || exit 1
PYTHONPATH=/Users/boonkerdinchoi/Downloads/year\ 4/ocr_bank/ocr-bank2/backend \
python scripts/fix_chat_history_schema.py

# Index receipts in vector database
echo ""
echo "📝 Step 2: Indexing receipts in vector database..."
PYTHONPATH=/Users/boonkerdinchoi/Downloads/year\ 4/ocr_bank/ocr-bank2/backend \
python scripts/index_receipts.py

echo ""
echo "✅ All fixes completed!"
echo ""
echo "🎯 Next steps:"
echo "1. Push code changes to Railway: git push"
echo "2. Test chatbot at: https://frontend-chi-six-75.vercel.app/chat"
echo "3. Try questions like:"
echo "   - 'How much did I receive last month?'"
echo "   - 'What are my total payments?'"
echo "   - 'Show me transactions to TUNGNGERN'"