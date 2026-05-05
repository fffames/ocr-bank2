#!/bin/bash

# OCR Bank - Deployment Testing Script
# This script tests the deployed application

set -e

echo "🧪 Testing OCR Bank Deployment..."

# Check if backend URL is provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/test-deployment.sh <backend-url> <frontend-url>"
    echo "Example: ./scripts/test-deployment.sh https://your-backend.up.railway.app https://your-frontend.vercel.app"
    exit 1
fi

BACKEND_URL=$1
FRONTEND_URL=$2

echo "Testing Backend: $BACKEND_URL"
echo "Testing Frontend: $FRONTEND_URL"
echo ""

# Test backend health
echo "1. Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "   ✅ Backend health check passed"
else
    echo "   ❌ Backend health check failed (HTTP $HEALTH_RESPONSE)"
fi

# Test API documentation
echo "2. Testing API documentation..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs")
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo "   ✅ API documentation accessible"
else
    echo "   ❌ API documentation not accessible (HTTP $DOCS_RESPONSE)"
fi

# Test receipts endpoint
echo "3. Testing receipts endpoint..."
RECEIPTS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/receipts/")
if [ "$RECEIPTS_RESPONSE" = "200" ]; then
    echo "   ✅ Receipts endpoint working"
else
    echo "   ❌ Receipts endpoint failed (HTTP $RECEIPTS_RESPONSE)"
fi

# Test frontend
if [ -n "$FRONTEND_URL" ]; then
    echo "4. Testing frontend..."
    FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
    if [ "$FRONTEND_RESPONSE" = "200" ]; then
        echo "   ✅ Frontend accessible"
    else
        echo "   ❌ Frontend not accessible (HTTP $FRONTEND_RESPONSE)"
    fi
fi

# Test CORS
echo "5. Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -H "Origin: $FRONTEND_URL" -H "Access-Control-Request-Method: GET" "$BACKEND_URL/api/receipts/")
if [ "$CORS_RESPONSE" = "200" ] || [ "$CORS_RESPONSE" = "204" ]; then
    echo "   ✅ CORS configured correctly"
else
    echo "   ⚠️  CORS may not be configured (HTTP $CORS_RESPONSE)"
fi

echo ""
echo "✅ Testing complete!"
echo ""
echo "Summary:"
echo "- Backend Health: $([ "$HEALTH_RESPONSE" = "200" ] && echo "✅" || echo "❌")"
echo "- API Docs: $([ "$DOCS_RESPONSE" = "200" ] && echo "✅" || echo "❌")"
echo "- Receipts API: $([ "$RECEIPTS_RESPONSE" = "200" ] && echo "✅" || echo "❌")"
echo "- Frontend: $([ -n "$FRONTEND_URL" ] && ([ "$FRONTEND_RESPONSE" = "200" ] && echo "✅" || echo "❌") || echo "⏭️  Not tested")"
echo "- CORS: $([ "$CORS_RESPONSE" = "200" ] || [ "$CORS_RESPONSE" = "204" ] && echo "✅" || echo "⚠️")"
echo ""
echo "📝 If any tests failed, see DEPLOY_INSTRUCTIONS.md for troubleshooting"