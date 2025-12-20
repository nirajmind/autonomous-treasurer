import os
import logging
import json
import redis
import uvicorn
import uuid
import time
from contextlib import asynccontextmanager
from collections import deque
from datetime import datetime, timedelta, UTC
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from web3 import Web3

# --- IMPORTS ---
from init_db import init_db
from finance.database import SessionLocal, get_db
from models import TransactionModel, Wallet, TransactionLog, SystemConfig, User
from finance.saga_orchestrator import SagaOrchestrator
from auth import create_access_token, get_current_user, verify_password
from agents.invoice_parser import parse_invoice_text

# --- INTERNAL IMPORTS ---
from finance.database import get_db, engine, Base
from auth import (
    Token, User, authenticate_user, create_access_token, 
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash, 
    UserCreate, get_user, create_user
)
from notifications.email_service import EmailService
email_service = EmailService()

load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TreasurerAPI")

# --- GLOBAL STATE ---
agent_thoughts = deque(maxlen=20) 
saga_orchestrator = SagaOrchestrator(session_factory=SessionLocal)

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application Starting... Connecting to Ledger...")
    init_db()
    agent_thoughts.append("System initialized... Connected to Postgres Ledger.")
    yield 
    print("🛑 Application Shutdown")

app = FastAPI(title="The Autonomous Treasurer API", lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class InvoiceRequest(BaseModel):
    raw_text: str

# --- Pydantic Models ---
class LimitUpdate(BaseModel):
    new_limit: float

# ==================================================================
# 1. PUBLIC ENDPOINTS (Login & Health)
# ==================================================================

@app.get("/")
def read_root():
    """Public health check to show system is online."""
    return {"status": "Online", "service": "Autonomous Treasurer Backend 🚀"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Public Endpoint: Generates JWT Token for login.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ==================================================================
# 2. PROTECTED DASHBOARD (The Fix)
# ==================================================================

@app.get("/api/dashboard")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Returns live treasury stats."""
    treasury_balance = fetch_treasury_balance() # Use the helper!
    
    monthly_burn = 5000.0
    runway_months = treasury_balance / monthly_burn if monthly_burn > 0 else 0

    return {
        "status": "Online",
        "treasury_balance": treasury_balance,
        "currency": "MNEE",
        "monthly_burn": monthly_burn,
        "runway_months": round(runway_months, 1),
        "alerts": [] 
    }

@app.get("/api/dashboard/logs")
def get_dashboard_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db) # <--- Need DB Access
):
    """
    Hybrid Fetch:
    1. Try Redis (Fastest, Live Data).
    2. If Redis empty, Fallback to Postgres (Permanent History).
    """
    logs = []
    
    try:
        # A. Try Redis
        redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
        raw_logs = redis_client.lrange("treasury:daily_logs", 0, 49)
        
        if raw_logs:
            # If we found data in Redis, use it!
            return [json.loads(log) for log in raw_logs]
            
        # B. Fallback to Postgres (If Redis was wiped)
        logger.info("⚠️ Redis empty. Fetching history from Postgres Database.")
        
        db_txs = db.query(TransactionModel).order_by(TransactionModel.timestamp.desc()).limit(50).all()
        
        # Convert DB Rows -> JSON Format for Frontend
        for tx in db_txs:
            logs.append({
                "timestamp": int(tx.timestamp.timestamp()),
                "event": f"{'Payment to' if tx.status=='CONFIRMED' else 'Invoice for'} {tx.vendor}",
                "balance": tx.balance_snapshot,
                "status": tx.status,
                "tx_hash": tx.tx_hash,
                "required": tx.amount if tx.status == "REQUIRES_APPROVAL" else None
            })
            
        return logs

    except Exception as e:
        logger.error(f"Log Fetch Error: {e}")
        return []  

# ==================================================================
# 3. PROTECTED SETTINGS (CFO Controls)
# ==================================================================

@app.get("/api/settings/limit")
def get_approval_limit(
    current_user: User = Depends(get_current_user), # <--- 🔒 SECURED
    db: Session = Depends(get_db)
):
    import redis
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
    limit = redis_client.get("system:approval_limit")
    return {"limit": float(limit) if limit else 50.0}

@app.post("/api/settings/limit")
async def set_approval_limit(
    update_data: LimitUpdate, 
    current_user: User = Depends(get_current_user), # <--- 🔒 SECURED
    db: Session = Depends(get_db)
):
    import redis
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)
    
    # Update Redis
    redis_client.set("system:approval_limit", update_data.new_limit)
    logger.info(f"Policy Update: User {current_user.username} changed limit to {update_data.new_limit}")
    
    return {"status": "updated", "new_limit": update_data.new_limit}

# ==================================================================
# 4. STARTUP TASKS
# ==================================================================

@app.on_event("startup")
def startup_event():
    # Create a default admin user if one doesn't exist
    db = next(get_db())
    try:
        user = get_user(db, "admin")
        if not user:
            create_user(db, "admin", "admin123")
            logger.info("✅ Default Admin User Created")
    except Exception as e:
        logger.error(f"Startup Error: {e}")

# 2. INVOICE PROCESSING (THE BRAIN)
@app.post("/api/process-invoice")
async def process_invoice(
    invoice: InvoiceRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db) # <--- Need DB Access
):
    logger.info("Received invoice for processing...")
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, decode_responses=True)

    # A. Parse
    try:
        parsed_data = parse_invoice_text(invoice.raw_text)
        amount = float(parsed_data.amount or 0.0)
        vendor = parsed_data.vendor_name or "Unknown"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # B. Execute Saga
    result = await saga_orchestrator.execute_payment_saga("user_1", vendor, amount)

    # C. GET REAL BALANCE (Optimization Kept!)
    current_balance = fetch_treasury_balance()

    # D. Determine Status & Data
    tx_status = "FAILED"
    tx_hash = None
    reason = None
    event_label = f"Invoice for {vendor}"
    
    if result["status"] == "SUCCESS":
        tx_status = "CONFIRMED"
        tx_hash = result.get('tx_hash')
        event_label = f"Payment to {vendor}"
    elif result["status"] in ["PAUSED", "REQUIRES_APPROVAL"]:
        tx_status = "REQUIRES_APPROVAL"
        reason = "Exceeds Policy Limit"
    else:
        tx_status = "FAILED"
        reason = result.get('reason')

    # --- STEP 1: WRITE TO POSTGRES (Permanent Record) ---
    try:
        db_entry = TransactionModel(
            vendor=vendor,
            amount=amount,
            status=tx_status,
            tx_hash=tx_hash,
            reason=reason,
            balance_snapshot=current_balance,
            timestamp=datetime.now(UTC)
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        logger.info(f"✅ Saved Transaction {db_entry.id} to Postgres")
    except Exception as e:
        logger.error(f"❌ DB Save Failed: {e}")
        # We continue even if DB fails, to ensure UI updates, but normally you might abort here.

    # --- STEP 2: WRITE TO REDIS (Live Feed) ---
    # (Matches the logic the Frontend expects)
    log_entry = {
        "timestamp": int(time.time()),
        "event": event_label,
        "balance": current_balance,
        "status": tx_status,
        "tx_hash": tx_hash,
        "required": amount if tx_status == "REQUIRES_APPROVAL" else None,
        "reason": reason
    }
    redis_client.lpush("treasury:daily_logs", json.dumps(log_entry))

    # --- STEP 3: Handle Specific Approval Queue ---
    if tx_status == "REQUIRES_APPROVAL":
        approval_id = str(uuid.uuid4())
        approval_data = {
            "id": approval_id,
            "vendor": vendor,
            "amount": amount,
            "reason": reason,
            "status": "PENDING"
        }
        redis_client.lpush("treasury:approvals", json.dumps(approval_data))

        # 2. TRIGGER EMAIL (The Missing Part) 👇
        # Since we are in app.py, we call the service directly
        email_body = f"Invoice from {vendor} for ${amount} exceeds the auto-approval limit. Please review."
        email_service.send_alert("POLICY_APPROVAL_NEEDED", email_body)

        return {"status": "PAUSED_FOR_APPROVAL", "approval_id": approval_id}

    return {"status": result["status"], "tx_hash": tx_hash, "reason": reason}
    
# ==================================================================
# 🔄 HELPER: FETCH REAL BALANCE (New Addition)
# ==================================================================
def fetch_treasury_balance():
    """Reads the live MNEE balance from the blockchain."""
    try:
        rpc_url = os.getenv("RPC_URL", "https://rpc.minato.soneium.org/")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        private_key = os.getenv("WALLET_PRIVATE_KEY")
        token_address = os.getenv("MNEE_TOKEN_ADDRESS")
        
        if not private_key or not token_address:
            return 0.0

        my_address = w3.eth.account.from_key(private_key).address

        # Minimal ABI
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
        contract = w3.eth.contract(address=token_address, abi=abi)
        
        raw_balance = contract.functions.balanceOf(my_address).call()
        return float(w3.from_wei(raw_balance, 'ether'))
    except Exception as e:
        logger.error(f"Balance Check Failed: {e}")
        return 0.0    

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
