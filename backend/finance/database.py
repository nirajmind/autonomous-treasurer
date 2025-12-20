import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:securepassword@localhost:5432/treasurer_ledger")

# 2. Engine & Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. The Base Class (Imported by everyone else)
Base = declarative_base()

# 4. Dependency for FastAPI Routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()