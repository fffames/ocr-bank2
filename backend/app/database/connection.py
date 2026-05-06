from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLAlchemy engine with proper URL encoding
try:
    database_url = settings.get_database_url()
    print(f"🔗 Connecting to database...")
    engine = create_engine(database_url)
    print(f"✅ Database engine created successfully")
except Exception as e:
    print(f"❌ Error creating database engine: {e}")
    print(f"   DATABASE_URL format may be incorrect")
    raise

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
