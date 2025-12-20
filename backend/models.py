from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import UTC, datetime
from finance.database import Base  # <--- Importing from the new clean file

# --- AUTH MODELS ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

# --- LEDGER MODELS ---
class TransactionLog(Base):
    __tablename__ = "ledger"
    id = Column(Integer, primary_key=True, index=True)
    tx_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    vendor = Column(String)
    amount = Column(Float)
    status = Column(String)
    tx_hash = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Wallet(Base):
    __tablename__ = "wallets"
    user_id = Column(String, primary_key=True, index=True)
    balance = Column(Float, default=0.0)
    monthly_burn = Column(Float, default=1000.0)

class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now(UTC))
    vendor = Column(String)
    amount = Column(Float)
    status = Column(String) # SUCCESS, PENDING, FAILED
    tx_hash = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    balance_snapshot = Column(Float) # The balance at that moment    