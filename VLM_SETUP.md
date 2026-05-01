# VLM Setup for OCR Bank

## What Changed
We've replaced PaddleOCR with Groq's Vision Language Model (LLaVA) for much more accurate receipt data extraction!

## Setup

### 1. Install Groq dependency
```bash
cd backend
source venv/bin/activate
pip install groq
```

### 2. Get Groq API Key
1. Go to https://console.groq.com/
2. Sign up / Login
3. Create a new API key
4. Copy the API key

### 3. Update .env file
Add your Groq API key:
```bash
GROQ_API_KEY=gsk_your_api_key_here
```

### 4. Restart backend
```bash
# Stop the server (Ctrl+C)
./venv/bin/uvicorn app.main:app --reload
```

## Why VLM is Better

### ✅ **No more regex!**
- PaddleOCR + Regex: Extract text → Parse with complex regex patterns
- VLM: Direct structured extraction in one step

### ✅ **Better accuracy**
- Understands context and layout
- Handles Thai text, numbers, dates naturally
- Recognizes sender/receiver patterns

### ✅ **Flexible**
- Easy to adjust extraction rules
- Just change the prompt!
- No need to rewrite regex

### ✅ **Fast & Free**
- Groq provides fast inference
- Generous free tier
- No heavy model downloads

## Model Details

- **Model**: LLaVA 1.5 7B (vision-language model)
- **Provider**: Groq
- **Capabilities**: Image understanding + structured JSON output
- **Speed**: Fast inference on Groq's infrastructure

## Example Extraction

The VLM can now understand:
- Buddhist era dates (พ.ศ. 2567 → 2024)
- Thai month names (เมษายน → April)
- Name titles (นาย, นาง, นางสาว)
- Thai numbers and currency (บาท)
- Context (sender vs receiver)

Try uploading your Thai bank receipts now! 🚀
