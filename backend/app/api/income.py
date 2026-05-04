"""Manual income management API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime
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


class IncomeCategoryCreate(BaseModel):
    name: str
    description: str = None
    color: str = "#10b981"
    icon: str = None


# Income Category endpoints
@router.get("/categories")
async def get_income_categories(db: Session = Depends(get_db)):
    """Get all income categories."""
    categories = db.query(IncomeCategory).order_by(IncomeCategory.name).all()
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "description": cat.__dict__.get("description"),
            "color": cat.color,
            "icon": cat.icon
        }
        for cat in categories
    ]


@router.post("/categories")
async def create_income_category(category: IncomeCategoryCreate, db: Session = Depends(get_db)):
    """Create a new income category."""
    # Check if category already exists
    existing = db.query(IncomeCategory).filter(IncomeCategory.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Category '{category.name}' already exists")

    new_category = IncomeCategory(
        name=category.name,
        color=category.color,
        icon=category.icon
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return {
        "id": new_category.id,
        "name": new_category.name,
        "color": new_category.color,
        "icon": new_category.icon
    }


@router.delete("/categories/{category_id}")
async def delete_income_category(category_id: int, db: Session = Depends(get_db)):
    """Delete an income category."""
    category = db.query(IncomeCategory).filter(IncomeCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if category is in use
    in_use = db.query(Receipt).filter(Receipt.income_category == category.name).first()
    if in_use:
        raise HTTPException(status_code=400, detail="Cannot delete category that is in use")

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}


# Manual Income endpoints
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

    # Get user's name from settings to use as receiver
    from app.models.user_settings import UserSettings
    user_settings = db.query(UserSettings).first()
    user_name = user_settings.user_name if user_settings else None

    new_income = Receipt(
        filename=f"income_{income.income_date.isoformat()}.txt",
        image_path="",
        ocr_raw_text=f"Manual income entry: {income.note}",
        extracted_date=income.income_date,
        extracted_time=None,
        sender=None,
        receiver=user_name,  # Use user's name from settings as receiver
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

    # Ensure receiver is always set to user's name from settings
    from app.models.user_settings import UserSettings
    user_settings = db.query(UserSettings).first()
    if user_settings and user_settings.user_name:
        db_income.receiver = user_settings.user_name

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
