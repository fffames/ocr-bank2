"""Salary management API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from calendar import monthrange

from app.database.connection import get_db
from app.models.user_settings import UserSettings
from app.models.receipt import Receipt
from app.models.income_category import IncomeCategory
from app.models.user import User
from app.services.auth_service import get_current_active_user

router = APIRouter()


class SalaryConfig(BaseModel):
    default_salary_amount: float
    salary_day_of_month: int = 1
    salary_category: str = "Salary"


@router.get("/config")
async def get_salary_config(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current salary configuration."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "default_salary_amount": float(settings.default_salary_amount) if settings.default_salary_amount else 0,
        "salary_day_of_month": settings.salary_day_of_month,
        "salary_category": settings.salary_category
    }


@router.put("/config")
async def update_salary_config(
    config: SalaryConfig,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update salary configuration and update current month's salary if exists."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    old_amount = settings.default_salary_amount
    old_category = settings.salary_category

    settings.default_salary_amount = config.default_salary_amount
    settings.salary_day_of_month = config.salary_day_of_month
    settings.salary_category = config.salary_category

    db.commit()
    db.refresh(settings)

    # If salary amount changed, update current month's salary entry
    updated_salary = None
    if old_amount != config.default_salary_amount or old_category != config.salary_category:
        today = date.today()
        year = today.year
        month = today.month

        existing_salary = db.query(Receipt).filter(
            Receipt.user_id == current_user.id,
            Receipt.is_salary == True,
            Receipt.extracted_date >= date(year, month, 1),
            Receipt.extracted_date <= date(year, month, monthrange(year, month)[1])
        ).first()

        if existing_salary:
            # Update existing salary entry
            from decimal import Decimal
            existing_salary.amount = Decimal(str(config.default_salary_amount))
            existing_salary.income_category = config.salary_category
            existing_salary.receiver = settings.user_name  # Ensure receiver is set to user's name
            existing_salary.note = f"Monthly salary for {year}-{month:02d}"
            existing_salary.updated_at = date.today()

            db.commit()
            db.refresh(existing_salary)

            # Re-index in vector store
            try:
                from app.services.vector_store import get_vector_store
                vector_store = get_vector_store()

                receipt_data = {
                    'extracted_date': existing_salary.extracted_date.isoformat(),
                    'sender': existing_salary.sender,
                    'receiver': existing_salary.receiver,
                    'amount': float(existing_salary.amount),
                    'note': existing_salary.note,
                    'transaction_type': existing_salary.transaction_type,
                    'income_category': existing_salary.income_category
                }
                vector_store.index_receipt(existing_salary.id, receipt_data)
                print(f"  ✅ Updated salary entry {existing_salary.id} in vector store")
            except Exception as e:
                print(f"  ⚠️  Failed to re-index salary entry: {e}")

            updated_salary = {
                "id": existing_salary.id,
                "amount": float(existing_salary.amount),
                "date": existing_salary.extracted_date.isoformat()
            }

    response = {
        "message": "Salary configuration updated",
        "config": {
            "default_salary_amount": float(settings.default_salary_amount),
            "salary_day_of_month": settings.salary_day_of_month,
            "salary_category": settings.salary_category
        }
    }

    if updated_salary:
        response["updated_current_month_salary"] = updated_salary

    return response


@router.get("/check-and-generate")
async def check_and_generate_salary(
    year: int = None,
    month: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if specified month has salary entry, create if missing.

    If year/month not specified, uses current month.
    Called on app load and when viewing Receipts page for a specific month.
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings or not settings.default_salary_amount:
        return {"status": "no_config", "message": "Salary not configured"}

    # Use provided year/month or default to current month
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month

    # Validate year/month
    if month < 1 or month > 12:
        return {"status": "error", "message": "Invalid month"}

    # Check if salary entry exists for specified month
    existing_salary = db.query(Receipt).filter(
        Receipt.user_id == current_user.id,
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
    from decimal import Decimal
    salary_date = date(year, month, settings.salary_day_of_month)

    new_salary = Receipt(
        user_id=current_user.id,
        filename=f"salary_{year}_{month}.txt",
        image_path="",
        ocr_raw_text=f"Auto-generated salary entry for {year}-{month:02d}",
        extracted_date=salary_date,
        extracted_time=None,
        sender=None,
        receiver=settings.user_name,  # Use user's name from settings as receiver
        amount=Decimal(str(settings.default_salary_amount)),
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all salary entries, optionally filtered by year."""
    query = db.query(Receipt).filter(
        Receipt.user_id == current_user.id,
        Receipt.is_salary == True
    )

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
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in salaries
    ]
