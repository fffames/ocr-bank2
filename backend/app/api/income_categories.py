"""Income category management API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.income_category import IncomeCategory
from app.models.receipt import Receipt

router = APIRouter()


class IncomeCategoryCreate(BaseModel):
    name: str
    description: str = None
    color: str = "#10b981"
    icon: str = None


@router.get("/")
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


@router.post("/")
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


@router.delete("/{category_id}")
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
