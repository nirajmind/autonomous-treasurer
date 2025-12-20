import time
import logging
from sqlalchemy.exc import OperationalError
from finance.database import engine, SessionLocal, Base
from models import User, Wallet
from auth import get_password_hash 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_INIT")

def init_db():
    retries = 5
    while retries > 0:
        try:
            logger.info("🔄 Attempting to connect to Database...")
            
            # 1. Create Tables
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database Connected & Tables Created.")
            
            # 2. Seed Data
            db = SessionLocal()
            
            # Seed Wallet
            if not db.query(Wallet).filter_by(user_id="user_1").first():
                logger.info("🌱 Seeding Wallet with Initial Funds...")
                db.add(Wallet(user_id="user_1", balance=4200.00, monthly_burn=1000.0))
            
            # Seed Admin
            if not db.query(User).filter_by(username="admin").first():
                logger.info("👤 Creating default admin user...")
                # We do NOT log the password here. 
                # The default is known to the developer (admin123) but never printed.
                admin = User(username="admin", hashed_password=get_password_hash("admin123"))
                db.add(admin)
                logger.info("✅ Admin user created successfully.") 
            
            db.commit()
            db.close()
            return

        except OperationalError as e:
            logger.warning(f"⚠️ DB not ready. Retrying in 2s...")
            retries -= 1
            time.sleep(2)
            
    raise Exception("❌ Could not connect to Database after 5 attempts.")

if __name__ == "__main__":
    init_db()