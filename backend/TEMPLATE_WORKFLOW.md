# Template Management Workflow

## TL;DR

**NO, you don't need to re-run indexing when adding new templates!**

Templates are used for **OCR extraction**, not for RAG search. The RAG searches by **receipt content**, not by template.

---

## What Gets Indexed?

### ✅ Indexed in Vector Store (for RAG Chat):
- Receipt **content**: sender, receiver, amount, date, note
- Used for: Semantic search (e.g., "show me payments to Major Cineplex")

### ❌ NOT Indexed:
- Templates (YAML files)
- Template IDs
- Bank names

---

## Workflow Scenarios

### Scenario 1: Adding a NEW Template ✅

**When**: You create a new `BBL.yaml` template for Bangkok Bank

**Steps**:
```bash
# 1. Create template (via web UI or manually)
# 2. Place in: backend/app/templates/BBL.yaml
# 3. Restart backend
# ✅ DONE! No indexing needed!
```

**Why**: Templates are only used when **processing new receipts**, not for searching existing ones.

---

### Scenario 2: Uploading a NEW Receipt ✅

**When**: User uploads a receipt image via web interface

**Steps**:
```bash
# 1. User uploads: receipt.jpg
# 2. Backend:
#    - Detects template (Kasikorn/SCB/TTB/etc.)
#    - Extracts data using template zones
#    - Saves to database
#    - ✅ AUTO-indexes in vector store (NEW!)
# 3. Immediately searchable in chat
# ✅ DONE! No manual indexing needed!
```

**Auto-indexing** (now implemented):
- Receipts with extracted data are automatically indexed
- Happens immediately after upload
- No manual `index_receipts.py` needed anymore

---

### Scenario 3: Re-processing Existing Receipt with New Template ✅

**When**: You added a better template and want to re-process old receipts

**Steps**:
```bash
# Option A: Via Web UI (if available)
# 1. Go to receipt details page
# 2. Click "Re-process with new template"
# ✅ Auto-indexed after re-processing

# Option B: Via API
curl -X POST http://localhost:8000/api/upload/process-ocr/{receipt_id}

# Option C: Manual (delete and re-upload)
# 1. Delete old receipt from database
# 2. Re-upload receipt image
# ✅ Auto-indexed with new extraction
```

---

### Scenario 4: When to Run `index_receipts.py` ⚠️

**Only need to run manually if**:

1. **Initial setup**: First time setting up RAG
   ```bash
   python index_receipts.py
   ```

2. **Bulk import**: Importing many receipts at once (bypassing upload API)
   ```bash
   python index_receipts.py
   ```

3. **Vector store corruption**: Vector store gets corrupted or deleted
   ```bash
   python index_receipts.py  # Rebuilds from scratch
   ```

4. **Missing data**: Some receipts weren't indexed (e.g., upload failed partway)
   ```bash
   python index_receipts.py  # Idempotent - safe to re-run
   ```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Upload Receipt Image                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Template Manager (detect_template)              │
│  - Checks all 3 templates: Kasikorn, SCB, TTB               │
│  - Returns: best matching template_id                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Template OCR Service (extract_from_image)          │
│  - Uses template zones to crop and OCR                       │
│  - Returns: {sender, receiver, amount, date, ...}           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ├──────────────────────────────────┐
                           │                                  │
                           ▼                                  ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│     PostgreSQL Database       │              │       Vector Store            │
│  - Stores receipt record      │              │  - Indexed for RAG search     │
│  - Used for: listing, details │              │  - Used for: chat queries     │
└──────────────────────────────┘              └──────────────────────────────┘
```

---

## Key Insight

### Templates are for **Extraction**, Not Search

| Component | Purpose | When Updated |
|-----------|---------|--------------|
| **Templates** | Extract data from images | Add new template → Restart backend |
| **Database** | Store receipt records | Upload new receipt → Automatic |
| **Vector Store** | Semantic search | Upload new receipt → **Automatic** ✅ |

### The RAG System Doesn't Care About Templates!

When you ask: *"How much did I pay to Major Cineplex?"*

The RAG system:
1. Searches vector store for "Major Cineplex"
2. Finds receipts with matching `receiver` field
3. **Doesn't check which template was used!**

Template only matters **during extraction**, not during search.

---

## Summary

### ✅ What's Automatic Now:
- New receipt upload → Auto-indexed in vector store
- Re-process receipt → Auto-indexed in vector store
- Template detection → Automatic (no config needed)

### ⚠️ What Still Needs Manual Work:
- Creating new templates (but no indexing needed!)
- Initial setup (run `index_receipts.py` once)
- Bulk imports (run `index_receipts.py` after)

### 🎯 Bottom Line:

**Add as many templates as you want - no re-indexing needed!**

The templates will be automatically used when:
- You upload new receipts
- You re-process existing receipts

The RAG will find receipts by **content**, regardless of which template extracted them.
