# Income & Salary Tracking Feature - Design Specification

**Date:** 2026-05-04
**Status:** Approved
**Author:** OCR Bank Team

---

## Overview

Add manual income tracking to complement receipt-based expense tracking. Store all income in the existing `receipts` table with `transaction_type="receiving"`, auto-generate monthly salary entries, and provide full CRUD control for manual income entries.

**Problem Statement:**
- Current system only tracks expenses from receipts (payment confirmations)
- Users have income (salary, freelance work) with no receipts
- Analytics only shows partial financial picture (expenses only)
- No way to track regular monthly salary or one-time additional income

**Solution:**
- Auto-generate monthly salary entries
- Manual income entry with custom categories
- Unified view of income + expenses in Analytics
- Full integration with existing features (RAG chat, Google Sheets)

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Data Storage** | Use existing `receipts` table with `transaction_type="receiving"` | Reuse infrastructure, unified data model |
| **Salary Auto-Generation** | On login + Analytics page visit | Ensures salary exists when needed |
| **Income Management** | Salary in Settings, additional income in Analytics | Logical separation: config vs transactions |
| **Income Categories** | User-created custom categories | Maximum flexibility |
| **Date Handling** | Date picker (defaults to today, editable) | Full user control |
| **Edit/Delete** | Full control on all income entries | User needs flexibility |
| **Analytics Display** | Separate sections + merged timeline toggle | Both detailed and unified views |
| **Integration** | RAG chat + Google Sheets export | Complete feature parity |

---

## 1. Database Schema Changes

### 1.1 Add fields to `receipts` table

```python
# backend/app/models/receipt.py - Add to Receipt model

class Receipt(Base):
    # ... existing fields ...

    # New fields for income tracking
    is_salary = Column(Boolean, default=False, nullable=True)
    """Auto-generated salary entry (vs OCR receipt or manual income)"""

    is_manual_income = Column(Boolean, default=False, nullable=True)
    """Manually added income entry (vs OCR receipt)"""

    income_category = Column(String(100), nullable=True)
    """User-defined income category: 'Salary', 'Freelance', 'Bonus', etc."""
```

**Migration SQL:**
```sql
ALTER TABLE receipts ADD COLUMN is_salary BOOLEAN DEFAULT FALSE;
ALTER TABLE receipts ADD COLUMN is_manual_income BOOLEAN DEFAULT FALSE;
ALTER TABLE receipts ADD COLUMN income_category VARCHAR(100);
```

### 1.2 Add fields to `user_settings` table

```python
# backend/app/models/user_settings.py - Add to UserSettings model

class UserSettings(Base):
    # ... existing fields ...

    # Salary configuration
    default_salary_amount = Column(DECIMAL(15, 2), nullable=True)
    """Monthly salary amount (e.g., 25000.00)"""

    salary_day_of_month = Column(Integer, default=1)
    """Which day of month to use for salary entry (default: 1st)"""

    salary_category = Column(String(100), default="Salary")
    """Category name for salary entries"""
```

**Migration SQL:**
```sql
ALTER TABLE user_settings ADD COLUMN default_salary_amount DECIMAL(15, 2);
ALTER TABLE user_settings ADD COLUMN salary_day_of_month INTEGER DEFAULT 1;
ALTER TABLE user_settings ADD COLUMN salary_category VARCHAR(100) DEFAULT 'Salary';
```

### 1.3 New table: `income_categories`

```python
# backend/app/models/income_category.py (NEW FILE)

from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.database.connection import Base


class IncomeCategory(Base):
    """User-defined income categories."""
    __tablename__ = "income_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    """Category name: 'Freelance', 'Bonus', 'Investment', etc."""

    color = Column(String(20), default="#10b981")
    """Hex color for UI display (default green)"""

    icon = Column(String(50), nullable=True)
    """Icon name for UI: 'briefcase', 'gift', 'trending-up', etc."""

    created_at = Column(TIMESTAMP, server_default=func.now())
```

**Migration SQL:**
```sql
CREATE TABLE income_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(20) DEFAULT '#10b981',
    icon VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Initial Data:**
```sql
-- Create default "Salary" category
INSERT INTO income_categories (name, color, icon) VALUES ('Salary', '#3b82f6', 'briefcase');

-- Create common additional income categories
INSERT INTO income_categories (name, color, icon) VALUES ('Freelance', '#10b981', 'laptop');
INSERT INTO income_categories (name, color, icon) VALUES ('Bonus', '#f59e0b', 'gift');
INSERT INTO income_categories (name, color, icon) VALUES ('Investment', '#8b5cf6', 'trending-up');
INSERT INTO income_categories (name, color, icon) VALUES ('Other', '#6b7280', 'more-horizontal');
```

---

## 2. Backend API Changes

### 2.1 New Endpoints

#### Income Category Management

**File:** `backend/app/api/income_categories.py` (NEW)

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.income_category import IncomeCategory

router = APIRouter()

class IncomeCategoryCreate(BaseModel):
    name: str
    color: str = "#10b981"
    icon: str = "more-horizontal"

class IncomeCategoryUpdate(BaseModel):
    name: str = None
    color: str = None
    icon: str = None

@router.get("/")
async def list_categories(db: Session = Depends(get_db)):
    """List all income categories."""
    categories = db.query(IncomeCategory).all()
    return categories

@router.post("/")
async def create_category(category: IncomeCategoryCreate, db: Session = Depends(get_db)):
    """Create new income category."""
    # Check if name already exists
    existing = db.query(IncomeCategory).filter(IncomeCategory.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists")

    new_category = IncomeCategory(
        name=category.name,
        color=category.color,
        icon=category.icon
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.put("/{category_id}")
async def update_category(category_id: int, category: IncomeCategoryUpdate, db: Session = Depends(get_db)):
    """Update income category."""
    db_category = db.query(IncomeCategory).filter(IncomeCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.name:
        db_category.name = category.name
    if category.color:
        db_category.color = category.color
    if category.icon:
        db_category.icon = category.icon

    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete income category (if not in use)."""
    category = db.query(IncomeCategory).filter(IncomeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if any income entries use this category
    from app.models.receipt import Receipt
    entries_using = db.query(Receipt).filter(Receipt.income_category == category.name).count()
    if entries_using > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {entries_using} income entries use this category"
        )

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}
```

#### Salary Management

**File:** `backend/app/api/salary.py` (NEW)

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime
from calendar import monthrange

from app.database.connection import get_db
from app.models.user_settings import UserSettings
from app.models.receipt import Receipt
from app.models.income_category import IncomeCategory

router = APIRouter()

class SalaryConfig(BaseModel):
    default_salary_amount: float
    salary_day_of_month: int = 1
    salary_category: str = "Salary"

@router.get("/config")
async def get_salary_config(db: Session = Depends(get_db)):
    """Get current salary configuration."""
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "default_salary_amount": float(settings.default_salary_amount) if settings.default_salary_amount else 0,
        "salary_day_of_month": settings.salary_day_of_month,
        "salary_category": settings.salary_category
    }

@router.put("/config")
async def update_salary_config(config: SalaryConfig, db: Session = Depends(get_db)):
    """Update salary configuration."""
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)

    settings.default_salary_amount = config.default_salary_amount
    settings.salary_day_of_month = config.salary_day_of_month
    settings.salary_category = config.salary_category

    db.commit()
    db.refresh(settings)

    return {
        "message": "Salary configuration updated",
        "config": {
            "default_salary_amount": float(settings.default_salary_amount),
            "salary_day_of_month": settings.salary_day_of_month,
            "salary_category": settings.salary_category
        }
    }

@router.get("/check-and-generate")
async def check_and_generate_salary(db: Session = Depends(get_db)):
    """
    Check if current month has salary entry, create if missing.

    Called on app load and Analytics page visit.
    """
    settings = db.query(UserSettings).first()
    if not settings or not settings.default_salary_amount:
        return {"status": "no_config", "message": "Salary not configured"}

    # Get current month/year
    today = date.today()
    year = today.year
    month = today.month

    # Check if salary entry exists for current month
    existing_salary = db.query(Receipt).filter(
        Receipt.is_salary == True,
        Receipt.extracted_date >= date(year, month, 1),
        Receipt.extracted_date <= date(year, month, monthrange(year, month)[1])
    ).first()

    if existing_salary:
        return {
            "status": "already_exists",
            "message": f"Salary already generated for {year}-{month:02d}",
            "salary_entry": {
                "id": existing_salary.id,
                "amount": float(existing_salary.amount),
                "date": existing_salary.extracted_date.isoformat()
            }
        }

    # Generate salary entry
    salary_date = date(year, month, settings.salary_day_of_month)

    new_salary = Receipt(
        filename=f"salary_{year}_{month}.txt",
        image_path="",
        ocr_raw_text=f"Auto-generated salary entry for {year}-{month:02d}",
        extracted_date=salary_date,
        extracted_time=None,
        sender=None,
        receiver=None,
        amount=settings.default_salary_amount,
        note=f"Monthly salary for {year}-{month:02d}",
        confidence_score=None,
        status="confirmed",
        transaction_type="receiving",
        transaction_confidence="high",
        classification_reason="Auto-generated salary entry",
        is_salary=True,
        is_manual_income=True,
        income_category=settings.salary_category
    )

    db.add(new_salary)
    db.commit()
    db.refresh(new_salary)

    # Index in vector store for RAG
    try:
        from app.services.vector_store import get_vector_store
        vector_store = get_vector_store()

        receipt_data = {
            'extracted_date': new_salary.extracted_date.isoformat(),
            'sender': new_salary.sender,
            'receiver': new_salary.receiver,
            'amount': float(new_salary.amount),
            'note': new_salary.note,
            'transaction_type': new_salary.transaction_type,
            'income_category': new_salary.income_category
        }
        vector_store.index_receipt(new_salary.id, receipt_data)
        print(f"  ✅ Auto-indexed salary entry {new_salary.id} in vector store")
    except Exception as e:
        print(f"  ⚠️  Failed to index salary entry: {e}")

    return {
        "status": "created",
        "message": f"Salary generated for {year}-{month:02d}",
        "salary_entry": {
            "id": new_salary.id,
            "amount": float(new_salary.amount),
            "date": new_salary.extracted_date.isoformat()
        }
    }

@router.get("/history")
async def get_salary_history(
    year: int = None,
    db: Session = Depends(get_db)
):
    """List all salary entries, optionally filtered by year."""
    query = db.query(Receipt).filter(Receipt.is_salary == True)

    if year:
        query = query.filter(
            Receipt.extracted_date >= date(year, 1, 1),
            Receipt.extracted_date <= date(year, 12, 31)
        )

    salaries = query.order_by(Receipt.extracted_date.desc()).all()

    return [
        {
            "id": s.id,
            "amount": float(s.amount),
            "date": s.extracted_date.isoformat(),
            "category": s.income_category,
            "note": s.note,
            "created_at": s.created_at.isoformat()
        }
        for s in salaries
    ]
```

#### Manual Income Management

**File:** `backend/app/api/income.py` (NEW)

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from decimal import Decimal

from app.database.connection import get_db
from app.models.receipt import Receipt
from app.models.income_category import IncomeCategory

router = APIRouter()

class ManualIncomeCreate(BaseModel):
    amount: float
    category: str
    income_date: date
    note: str = ""

class ManualIncomeUpdate(BaseModel):
    amount: float = None
    category: str = None
    income_date: date = None
    note: str = None

@router.post("/")
async def create_income(income: ManualIncomeCreate, db: Session = Depends(get_db)):
    """Add manual income entry."""
    if income.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")

    if income.income_date > date.today():
        raise HTTPException(status_code=400, detail="Income date cannot be in the future")

    # Verify category exists
    category = db.query(IncomeCategory).filter(IncomeCategory.name == income.category).first()
    if not category:
        raise HTTPException(status_code=400, detail=f"Category '{income.category}' not found")

    new_income = Receipt(
        filename=f"income_{income.income_date.isoformat()}.txt",
        image_path="",
        ocr_raw_text=f"Manual income entry: {income.note}",
        extracted_date=income.income_date,
        extracted_time=None,
        sender=None,
        receiver=None,
        amount=Decimal(str(income.amount)),
        note=income.note,
        confidence_score=None,
        status="confirmed",
        transaction_type="receiving",
        transaction_confidence="high",
        classification_reason="Manually added income",
        is_salary=False,
        is_manual_income=True,
        income_category=income.category
    )

    db.add(new_income)
    db.commit()
    db.refresh(new_income)

    # Index in vector store
    try:
        from app.services.vector_store import get_vector_store
        vector_store = get_vector_store()

        receipt_data = {
            'extracted_date': new_income.extracted_date.isoformat(),
            'sender': new_income.sender,
            'receiver': new_income.receiver,
            'amount': float(new_income.amount),
            'note': new_income.note,
            'transaction_type': new_income.transaction_type,
            'income_category': new_income.income_category
        }
        vector_store.index_receipt(new_income.id, receipt_data)
        print(f"  ✅ Auto-indexed income entry {new_income.id}")
    except Exception as e:
        print(f"  ⚠️  Failed to index income entry: {e}")

    return {
        "id": new_income.id,
        "amount": float(new_income.amount),
        "date": new_income.extracted_date.isoformat(),
        "category": new_income.income_category,
        "note": new_income.note
    }

@router.put("/{income_id}")
async def update_income(
    income_id: int,
    income: ManualIncomeUpdate,
    db: Session = Depends(get_db)
):
    """Update manual income entry."""
    db_income = db.query(Receipt).filter(
        Receipt.id == income_id,
        Receipt.is_manual_income == True
    ).first()

    if not db_income:
        raise HTTPException(status_code=404, detail="Income entry not found")

    if income.amount is not None:
        if income.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        db_income.amount = Decimal(str(income.amount))

    if income.income_date is not None:
        if income.income_date > date.today():
            raise HTTPException(status_code=400, detail="Income date cannot be in the future")
        db_income.extracted_date = income.income_date

    if income.category is not None:
        # Verify category exists
        category = db.query(IncomeCategory).filter(IncomeCategory.name == income.category).first()
        if not category:
            raise HTTPException(status_code=400, detail=f"Category '{income.category}' not found")
        db_income.income_category = income.category

    if income.note is not None:
        db_income.note = income.note

    db_income.updated_at = datetime.now()
    db.commit()
    db.refresh(db_income)

    # Re-index in vector store
    try:
        from app.services.vector_store import get_vector_store
        vector_store = get_vector_store()

        receipt_data = {
            'extracted_date': db_income.extracted_date.isoformat(),
            'sender': db_income.sender,
            'receiver': db_income.receiver,
            'amount': float(db_income.amount),
            'note': db_income.note,
            'transaction_type': db_income.transaction_type,
            'income_category': db_income.income_category
        }
        vector_store.index_receipt(db_income.id, receipt_data)
    except Exception as e:
        print(f"  ⚠️  Failed to re-index income entry: {e}")

    return {
        "id": db_income.id,
        "amount": float(db_income.amount),
        "date": db_income.extracted_date.isoformat(),
        "category": db_income.income_category,
        "note": db_income.note
    }

@router.delete("/{income_id}")
async def delete_income(income_id: int, db: Session = Depends(get_db)):
    """Delete manual income entry."""
    income = db.query(Receipt).filter(
        Receipt.id == income_id,
        Receipt.is_manual_income == True
    ).first()

    if not income:
        raise HTTPException(status_code=404, detail="Income entry not found")

    # Delete from vector store
    try:
        from app.services.vector_store import get_vector_store
        vector_store = get_vector_store()
        vector_store.delete_receipt(income_id)
        print(f"  ✅ Deleted income entry {income_id} from vector store")
    except Exception as e:
        print(f"  ⚠️  Could not delete from vector store: {e}")

    db.delete(income)
    db.commit()

    return {"message": "Income entry deleted successfully"}

@router.get("/{year}/{month}")
async def get_income_for_month(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """Get all income entries for specific month."""
    from calendar import monthrange

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    incomes = db.query(Receipt).filter(
        Receipt.is_manual_income == True,
        Receipt.extracted_date >= start_date,
        Receipt.extracted_date <= end_date
    ).order_by(Receipt.extracted_date.desc()).all()

    return [
        {
            "id": inc.id,
            "amount": float(inc.amount),
            "date": inc.extracted_date.isoformat(),
            "category": inc.income_category,
            "note": inc.note,
            "is_salary": inc.is_salary
        }
        for inc in incomes
    ]
```

### 2.2 Modified Endpoints

#### Analytics Enhancement

**File:** `backend/app/api/analytics.py` (MODIFY EXISTING)

Add year/month filter parameters:

```python
@router.get("/overview")
async def get_analytics_overview(
    year: int = None,  # NEW: Optional year filter
    month: int = None,  # NEW: Optional month filter
    db: Session = Depends(get_db)
):
    """
    Get analytics overview with optional year/month filtering.

    If year/month provided, filter data to that period.
    Otherwise, return all-time data.
    """
    # Base query
    query = db.query(Receipt)

    # Apply date filters if provided
    if year and month:
        from calendar import monthrange
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        query = query.filter(Receipt.extracted_date >= start_date,
                           Receipt.extracted_date <= end_date)
    elif year:
        query = query.filter(
            Receipt.extracted_date >= date(year, 1, 1),
            Receipt.extracted_date <= date(year, 12, 31)
        )

    all_receipts = query.all()

    # Separate income (receiving) and expenses (sending)
    income_receipts = [r for r in all_receipts if r.transaction_type == 'receiving']
    expense_receipts = [r for r in all_receipts if r.transaction_type == 'sending']

    # Calculate totals
    total_income = sum((r.amount or 0) for r in income_receipts)
    total_expenses = sum((r.amount or 0) for r in expense_receipts)

    # Break down income by category
    income_by_category = {}
    for r in income_receipts:
        category = r.income_category or "Uncategorized"
        if category not in income_by_category:
            income_by_category[category] = 0
        income_by_category[category] += float(r.amount or 0)

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "net_balance": float(total_income - total_expenses),
        "income_count": len(income_receipts),
        "expense_count": len(expense_receipts),
        "income_by_category": income_by_category,
        "period": {
            "year": year,
            "month": month,
            "filtered": bool(year or month)
        }
    }
```

### 2.3 Update Main Router

**File:** `backend/app/main.py` (MODIFY)

Add new routers:

```python
# Import new routers
from app.api import income_categories, salary, income

# Register new routes
app.include_router(income_categories.router, prefix="/api/income-categories", tags=["income_categories"])
app.include_router(salary.router, prefix="/api/salary", tags=["salary"])
app.include_router(income.router, prefix="/api/income", tags=["income"])
```

---

## 3. Frontend Components

### 3.1 Settings Page Updates

**File:** `frontend/src/pages/Settings.tsx` (MODIFY)

Add new section for salary configuration:

```typescript
// Add to SettingsPage component
const [salaryConfig, setSalaryConfig] = useState({
  default_salary_amount: 0,
  salary_day_of_month: 1,
  salary_category: 'Salary'
});

// Add to existing settings form
<section className="salary-config-section">
  <h2>💰 Monthly Salary Configuration</h2>

  <div className="form-group">
    <label>Default Salary Amount (THB)</label>
    <input
      type="number"
      value={salaryConfig.default_salary_amount}
      onChange={(e) => setSalaryConfig({
        ...salaryConfig,
        default_salary_amount: parseFloat(e.target.value)
      })}
      placeholder="25000"
    />
  </div>

  <div className="form-group">
    <label>Pay Day</label>
    <select
      value={salaryConfig.salary_day_of_month}
      onChange={(e) => setSalaryConfig({
        ...salaryConfig,
        salary_day_of_month: parseInt(e.target.value)
      })}
    >
      {Array.from({length: 31}, (_, i) => (
        <option key={i+1} value={i+1}>{i+1}{getOrdinalSuffix(i+1)}</option>
      ))}
    </select>
  </div>

  <div className="form-group">
    <label>Category Name</label>
    <input
      type="text"
      value={salaryConfig.salary_category}
      onChange={(e) => setSalaryConfig({
        ...salaryConfig,
        salary_category: e.target.value
      })}
    />
  </div>

  <div className="actions">
    <button onClick={saveSalaryConfig}>Save Salary Configuration</button>
    <button onClick={viewSalaryHistory}>View/Edit History</button>
  </div>
</section>
```

### 3.2 Analytics Page Updates

**File:** `frontend/src/pages/Analytics.tsx` (MODIFY)

Add year/month filters and income breakdown:

```typescript
function AnalyticsPage() {
  const [yearFilter, setYearFilter] = useState(new Date().getFullYear());
  const [monthFilter, setMonthFilter] = useState(new Date().getMonth() + 1);
  const [viewMode, setViewMode] = useState<'separate' | 'merged'>('separate');
  const [showAddIncome, setShowAddIncome] = useState(false);

  // Fetch analytics with filters
  const fetchAnalytics = async () => {
    const params: any = {};
    if (yearFilter) params.year = yearFilter;
    if (monthFilter && monthFilter !== 'all') params.month = monthFilter;

    const data = await analyticsService.getOverview(params);
    setAnalytics(data);
  };

  return (
    <div>
      {/* Filters */}
      <div className="analytics-filters">
        <select value={yearFilter} onChange={(e) => setYearFilter(parseInt(e.target.value))}>
          <option value={2023}>2023</option>
          <option value={2024}>2024</option>
          <option value={2025}>2025</option>
          <option value={2026}>2026</option>
        </select>

        <select value={monthFilter} onChange={(e) => setMonthFilter(e.target.value)}>
          <option value="all">All Months</option>
          {months.map(m => <option value={m.value}>{m.label}</option>)}
        </select>

        <div className="view-toggle">
          <button
            className={viewMode === 'separate' ? 'active' : ''}
            onClick={() => setViewMode('separate')}
          >
            Separate Sections
          </button>
          <button
            className={viewMode === 'merged' ? 'active' : ''}
            onClick={() => setViewMode('merged')}
          >
            Merged Timeline
          </button>
        </div>

        <button onClick={() => setShowAddIncome(true)}>+ Add Income</button>
      </div>

      {/* Income Breakdown Section */}
      {viewMode === 'separate' && (
        <section className="income-breakdown">
          <h2>💵 Income Breakdown</h2>
          <IncomeBreakdown
            income={analytics.income_by_category}
            total={analytics.total_income}
            onEdit={handleEditIncome}
            onDelete={handleDeleteIncome}
          />
        </section>
      )}

      {/* Expense Breakdown Section */}
      {viewMode === 'separate' && (
        <section className="expense-breakdown">
          <h2>💸 Expense Breakdown</h2>
          <ExpenseBreakdown expenses={analytics.expenses_by_category} />
        </section>
      )}

      {/* Merged Timeline */}
      {viewMode === 'merged' && (
        <section className="merged-timeline">
          <h2>📊 Transaction Timeline</h2>
          <TransactionTimeline
            income={analytics.income_by_category}
            expenses={analytics.expenses_by_category}
          />
        </section>
      )}
    </div>
  );
}
```

### 3.3 New Components

**File:** `frontend/src/components/IncomeBreakdown.tsx` (NEW)

```typescript
interface IncomeBreakdownProps {
  income: Record<string, number>;
  total: number;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

export function IncomeBreakdown({ income, total, onEdit, onDelete }: IncomeBreakdownProps) {
  return (
    <div className="income-breakdown">
      <div className="total-income">
        <h3>Total Income: ฿{total.toLocaleString()}</h3>
      </div>

      <div className="income-by-category">
        {Object.entries(income).map(([category, amount]) => (
          <div key={category} className="income-category">
            <span className="category-name">{category}</span>
            <span className="amount">฿{amount.toLocaleString()}</span>
            <span className="percentage">
              {((amount / total) * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**File:** `frontend/src/components/AddIncomeModal.tsx` (NEW)

```typescript
interface AddIncomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (income: ManualIncomeCreate) => void;
}

export function AddIncomeModal({ isOpen, onClose, onSubmit }: AddIncomeModalProps) {
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Freelance');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [note, setNote] = useState('');

  const handleSubmit = () => {
    onSubmit({
      amount: parseFloat(amount),
      category,
      income_date: new Date(date),
      note
    });
    onClose();
    // Reset form
    setAmount('');
    setNote('');
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Add Manual Income</h2>

        <div className="form-group">
          <label>Amount (THB)</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="3000"
          />
        </div>

        <div className="form-group">
          <label>Category</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="Salary">Salary</option>
            <option value="Freelance">Freelance</option>
            <option value="Bonus">Bonus</option>
            <option value="Investment">Investment</option>
            <option value="Other">Other</option>
          </select>
          <button onClick={() => setShowCategoryModal(true)}>+ New Category</button>
        </div>

        <div className="form-group">
          <label>Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Note</label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Website design project"
          />
        </div>

        <div className="modal-actions">
          <button onClick={onClose} className="cancel-btn">Cancel</button>
          <button onClick={handleSubmit} className="submit-btn">Add Income</button>
        </div>
      </div>
    </div>
  );
}
```

### 3.4 App Initialization

**File:** `frontend/src/App.tsx` (MODIFY)

Add salary check on app load:

```typescript
function App() {
  const [mode, setMode] = useState<'user' | 'developer'>('user');

  // Auto-generate salary on app load
  useEffect(() => {
    if (mode === 'user') {
      checkAndGenerateSalary();
    }
  }, [mode]);

  const checkAndGenerateSalary = async () => {
    try {
      const result = await salaryService.checkAndGenerate();
      if (result.status === 'created') {
        console.log('✅ Salary generated for current month');
      }
    } catch (error) {
      console.error('Failed to check salary:', error);
    }
  };

  // ... rest of app
}
```

### 3.5 New Frontend Services

**File:** `frontend/src/services/incomeService.ts` (NEW)

```typescript
import api from './api';

export const incomeService = {
  // Income categories
  getCategories: async () => {
    const response = await api.get('/income-categories/');
    return response.data;
  },

  createCategory: async (category: { name: string; color?: string; icon?: string }) => {
    const response = await api.post('/income-categories/', category);
    return response.data;
  },

  deleteCategory: async (id: number) => {
    const response = await api.delete(`/income-categories/${id}`);
    return response.data;
  },

  // Salary
  getSalaryConfig: async () => {
    const response = await api.get('/salary/config');
    return response.data;
  },

  updateSalaryConfig: async (config: {
    default_salary_amount: number;
    salary_day_of_month?: number;
    salary_category?: string;
  }) => {
    const response = await api.put('/salary/config', config);
    return response.data;
  },

  checkAndGenerate: async () => {
    const response = await api.get('/salary/check-and-generate');
    return response.data;
  },

  getSalaryHistory: async (year?: number) => {
    const params = year ? { year } : {};
    const response = await api.get('/salary/history', { params });
    return response.data;
  },

  // Manual income
  createIncome: async (income: {
    amount: number;
    category: string;
    income_date: string;
    note?: string;
  }) => {
    const response = await api.post('/income/', income);
    return response.data;
  },

  updateIncome: async (id: number, income: {
    amount?: number;
    category?: string;
    income_date?: string;
    note?: string;
  }) => {
    const response = await api.put(`/income/${id}`, income);
    return response.data;
  },

  deleteIncome: async (id: number) => {
    const response = await api.delete(`/income/${id}`);
    return response.data;
  },

  getIncomeForMonth: async (year: number, month: number) => {
    const response = await api.get(`/income/${year}/${month}`);
    return response.data;
  }
};
```

**File:** `frontend/src/services/analyticsService.ts` (NEW or MODIFY EXISTING)

```typescript
import api from './api';

export const analyticsService = {
  getOverview: async (params?: { year?: number; month?: number }) => {
    const response = await api.get('/analytics/overview', { params });
    return response.data;
  }
};
```

---

## 4. User Experience Flows

### 4.1 First-Time Salary Setup

```
1. User logs in → Goes to Settings page
2. Scrolls to "💰 Monthly Salary Configuration" section
3. Enters:
   - Default Salary Amount: 25000
   - Pay Day: 1st
   - Category Name: Salary
4. Clicks "Save Salary Configuration"
5. System saves to user_settings table
6. Success message: "✅ Salary configuration saved"
```

### 4.2 Monthly Salary Auto-Generation

```
1. User logs in OR visits Analytics page
2. System calls GET /api/salary/check-and-generate
3. Backend checks: Does current month have salary entry?
4. If NO:
   - Creates receipt entry with is_salary=true, is_manual_income=true
   - Amount: 25000 (from settings)
   - Date: 1st of current month
   - Category: "Salary"
   - Indexes in vector store
   - Returns: {status: "created", ...}
5. If YES:
   - Returns: {status: "already_exists", ...}
6. Frontend logs result, shows notification if created
```

### 4.3 Adding Manual Income

```
1. User in Analytics page, clicks "+ Add Income"
2. Modal opens with form:
   - Amount: [3000]
   - Category: [Freelance ▼] or [+ New Category]
   - Date: [2026-05-15] (default today)
   - Note: [Website design project]
3. User fills form, clicks "Add Income"
4. Frontend calls POST /api/income/
5. Backend validates:
   - Amount > 0
   - Date not in future
   - Category exists
6. Creates receipt entry:
   - is_salary=false
   - is_manual_income=true
   - transaction_type="receiving"
7. Indexes in vector store
8. Updates Analytics display
9. Success message: "✅ Income entry added"
```

### 4.4 Editing Income

```
1. User clicks income entry in Analytics
2. Modal opens with current values
3. User changes:
   - Amount: 3000 → 3500
   - Category: Freelance → Bonus
4. Clicks "Save Changes"
5. Frontend calls PUT /api/income/{id}
6. Backend validates and updates
7. Re-indexes in vector store
8. Refreshes Analytics display
9. Success message: "✅ Income updated"
```

### 4.5 Deleting Income

```
1. User clicks "Delete" on income entry
2. Confirmation dialog: "Delete this income entry?"
3. User confirms
4. Frontend calls DELETE /api/income/{id}
5. Backend:
   - Deletes from vector store
   - Deletes from database
6. Refreshes Analytics display
7. Success message: "✅ Income deleted"
```

---

## 5. Data Validation & Error Handling

### 5.1 Input Validation

**Backend validations:**
- Salary amount must be > 0
- Income amount must be > 0
- Income date cannot be in future
- Category must exist before use
- Only one salary entry per month

**Frontend validations:**
- Same as backend (duplicate for better UX)
- Real-time feedback on form inputs

### 5.2 Error Messages

| Scenario | Error Message |
|----------|---------------|
| Salary not configured | "Please configure your salary in Settings first" |
| Amount <= 0 | "Amount must be greater than 0" |
| Date in future | "Income date cannot be in the future" |
| Category not found | "Category 'X' not found. Please create it first." |
| Category in use | "Cannot delete: 5 income entries use this category" |
| Duplicate salary | "Salary already generated for this month" |

---

## 6. Integration Points

### 6.1 RAG Chat Integration

**No changes needed** - income entries automatically included because:
- Stored in `receipts` table
- Have `transaction_type="receiving"`
- Indexed in vector store on creation
- Chat queries like "How much did I earn in May?" will return salary + manual income

### 6.2 Google Sheets Export

**No changes needed** - existing export logic includes:
- All receipts with `transaction_type="receiving"`
- Salary entries marked with `is_salary=true`
- Manual income marked with `is_manual_income=true`
- Income category shown in spreadsheet

### 6.3 Transaction Classification

**No changes needed** - manual income bypasses classification:
- `is_manual_income=true` entries skip classification
- OCR receipts classified as before
- LLM only processes OCR receipts

---

## 7. Testing Checklist

### 7.1 Database Migration
- [ ] Migration runs successfully
- [ ] New fields added to receipts table
- [ ] New fields added to user_settings table
- [ ] income_categories table created
- [ ] Default categories seeded

### 7.2 Salary Configuration
- [ ] Can set default salary amount
- [ ] Can set pay day of month
- [ ] Can set salary category name
- [ ] Configuration persists across sessions

### 7.3 Salary Auto-Generation
- [ ] Salary generates on first login of new month
- [ ] Salary generates when visiting Analytics page
- [ ] Doesn't duplicate if already exists
- [ ] Correct amount from settings
- [ ] Correct date (configured day of month)
- [ ] Indexed in vector store

### 7.4 Manual Income
- [ ] Can add manual income with all fields
- [ ] Can edit income entries
- [ ] Can delete income entries
- [ ] Date validation works (no future dates)
- [ ] Amount validation works (> 0)
- [ ] Category validation works

### 7.5 Income Categories
- [ ] Can create custom categories
- [ ] Can edit categories
- [ ] Can't delete if in use
- [ ] Can delete if not in use
- [ ] Categories show in dropdown

### 7.6 Analytics Display
- [ ] Income breakdown shows correct totals
- [ ] Year/month filters work correctly
- [ ] Separate sections view works
- [ ] Merged timeline view works
- [ ] Salary and manual income both shown
- [ ] Income by category breakdown correct

### 7.7 Integration
- [ ] Income included in RAG chat queries
- [ ] Income exports to Google Sheets
- [ ] Vector store indexing works
- [ ] Transaction classification unchanged

---

## 8. Performance Considerations

- **Salary check overhead**: Minimal (one DB query per login/page visit)
- **Indexing**: Ensure `extracted_date`, `is_salary`, `is_manual_income` columns are indexed
- **Vector store**: Automatic indexing on income creation (acceptable overhead)
- **Analytics queries**: Optimized with proper filtering and indexing

---

## 9. Security Considerations

- **Income deletion**: Soft delete recommended (add `deleted_at` column)
- **Validation**: Server-side validation critical (client-side can be bypassed)
- **Authorization**: All income/endpoints require authentication (future enhancement)
- **Rate limiting**: Consider rate limiting on income creation endpoints

---

## 10. Future Enhancements

### Phase 2 (Future):
- **Recurring additional income**: Setup recurring freelance income
- **Income goals**: Set monthly income targets, track progress
- **Income reports**: Monthly/annual income reports
- **Tax categories**: Mark income as taxable/non-taxable
- **Multi-currency**: Support income in different currencies
- **Receipt attachment**: Attach supporting docs to income entries
- **Income reminders**: Notify to add income if missing

---

## 11. Migration Strategy

### Database Migration

**File:** `backend/alembic/versions/XXX_add_income_tracking.py` (NEW)

```python
"""add income tracking

Revision ID: XXX
Revises: [previous-revision]
Create Date: 2026-05-04

"""
from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add fields to receipts table
    op.add_column('receipts', sa.Column('is_salary', sa.Boolean(), nullable=True))
    op.add_column('receipts', sa.Column('is_manual_income', sa.Boolean(), nullable=True))
    op.add_column('receipts', sa.Column('income_category', sa.String(100), nullable=True))

    # Add fields to user_settings table
    op.add_column('user_settings', sa.Column('default_salary_amount', sa.Numeric(15, 2), nullable=True))
    op.add_column('user_settings', sa.Column('salary_day_of_month', sa.Integer(), nullable=True))
    op.add_column('user_settings', sa.Column('salary_category', sa.String(100), nullable=True))

    # Create income_categories table
    op.create_table(
        'income_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Insert default categories
    op.execute("INSERT INTO income_categories (name, color, icon) VALUES ('Salary', '#3b82f6', 'briefcase')")
    op.execute("INSERT INTO income_categories (name, color, icon) VALUES ('Freelance', '#10b981', 'laptop')")
    op.execute("INSERT INTO income_categories (name, color, icon) VALUES ('Bonus', '#f59e0b', 'gift')")
    op.execute("INSERT INTO income_categories (name, color, icon) VALUES ('Investment', '#8b5cf6', 'trending-up')")
    op.execute("INSERT INTO income_categories (name, color, icon) VALUES ('Other', '#6b7280', 'more-horizontal')")


def downgrade():
    # Remove fields from receipts table
    op.drop_column('receipts', 'income_category')
    op.drop_column('receipts', 'is_manual_income')
    op.drop_column('receipts', 'is_salary')

    # Remove fields from user_settings table
    op.drop_column('user_settings', 'salary_category')
    op.drop_column('user_settings', 'salary_day_of_month')
    op.drop_column('user_settings', 'default_salary_amount')

    # Drop income_categories table
    op.drop_table('income_categories')
```

### Run Migration

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

---

## 12. Implementation Order

### Phase 1: Backend Foundation (2-3 days)
1. Create database migration
2. Run migration
3. Create new models (income_category.py)
4. Create new API endpoints (income_categories, salary, income)
5. Update main router

### Phase 2: Frontend UI (3-4 days)
1. Create new services (incomeService, analyticsService)
2. Update Settings page (salary config)
3. Update Analytics page (filters, income breakdown)
4. Create new components (AddIncomeModal, IncomeBreakdown)
5. Update App.tsx (salary check on load)

### Phase 3: Integration & Testing (2 days)
1. Test salary auto-generation
2. Test manual income CRUD
3. Test category management
4. Test Analytics filters
5. Test RAG chat integration
6. Test Google Sheets export

**Total: 7-9 days**

---

## 13. Rollback Plan

If issues arise:

1. **Database**: Alembic downgrade `alembic downgrade -1`
2. **Backend**: Revert commit, redeploy previous version
3. **Frontend**: Revert commit, redeploy previous version
4. **Data**: Manual income entries remain in receipts table (harmless, just won't have new fields populated)

---

**End of Specification**

**Next Steps:**
1. Review this specification
2. Approve or request changes
3. Create implementation plan using writing-plans skill
4. Begin implementation
