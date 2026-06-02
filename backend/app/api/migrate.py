"""Database migration endpoint for running Alembic migrations."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from app.database.connection import engine, get_db
from alembic.config import Config
from alembic import command
import os
import tempfile

router = APIRouter()


@router.post("/migrate")
async def run_migrations():
    """
    Run database migrations to create/update tables.

    This endpoint is useful for initial database setup on deployments
    where migrations cannot be run manually.
    """
    try:
        # Create a temporary alembic config
        config = Config()

        # Set the script location
        config.set_main_option("script_location", "app/database/migrations")

        # Set the database URL from environment
        from app.config import settings
        db_url = settings.get_database_url()
        config.set_main_option("sqlalchemy.url", db_url)

        # Run the migration
        with tempfile.TemporaryDirectory() as tmpdir:
            config.set_main_option("here", tmpdir)
            command.upgrade(config, "head")

        return {
            "status": "success",
            "message": "Database migrations completed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/migrate/status")
async def migration_status():
    """
    Check if database tables exist.

    Returns the status of the database migration.
    """
    try:
        from app.models.user import User
        from app.models.receipt import Receipt
        from app.models.income import Income
        from app.models.income_category import IncomeCategory
        from app.models.salary import Salary

        # Try to query each table
        tables_status = {}

        with engine.connect() as conn:
            # Check users table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                tables_status["users"] = "exists"
            except Exception:
                tables_status["users"] = "missing"

            # Check receipts table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM receipts"))
                tables_status["receipts"] = "exists"
            except Exception:
                tables_status["receipts"] = "missing"

            # Check income table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM income"))
                tables_status["income"] = "exists"
            except Exception:
                tables_status["income"] = "missing"

            # Check income_categories table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM income_categories"))
                tables_status["income_categories"] = "exists"
            except Exception:
                tables_status["income_categories"] = "missing"

            # Check salary table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM salary"))
                tables_status["salary"] = "exists"
            except Exception:
                tables_status["salary"] = "missing"

        # Determine overall status
        all_exist = all(status == "exists" for status in tables_status.values())

        return {
            "status": "ready" if all_exist else "needs_migration",
            "tables": tables_status
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check migration status: {str(e)}"
        )
