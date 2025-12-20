import logging
import os
import json
import time
import redis
from web3 import Web3
from decimal import Decimal
import asyncio
from notifications.email_service import EmailService

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SagaOrchestrator")

class SagaOrchestrator:
    def __init__(self, session_factory):
        self.Session = session_factory
        
        # 1. REDIS CONNECTION
        redis_host = os.getenv("REDIS_HOST", "localhost")
        try:
            self.redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"✅ Connected to Redis at {redis_host}")
        except:
            logger.warning("⚠️ Redis not found. Dashboard reporting will be disabled.")
            self.redis_client = None

        # 2. REAL BLOCKCHAIN CONNECTION
        self.rpc_url = os.getenv("MNEE_RPC_URL", "https://rpc.minato.soneium.org/")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # 3. MNEE CONTRACT
        self.contract_address = os.getenv("MNEE_TOKEN_ADDRESS", "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF")
        self.erc20_abi = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}, {"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
        self.mnee_contract = self.w3.eth.contract(address=self.contract_address, abi=self.erc20_abi)
        self.email_service = EmailService()

    # --- MAIN CONDUCTOR ---
    async def execute_payment_saga(self, user_id: str, vendor_wallet: str, amount: float):
        """
        Orchestrates the full payment flow: Validation -> Reservation -> Execution.
        """
        logger.info(f"🎼 Starting Payment Saga for {amount} MNEE to {vendor_wallet}")
        
        # Step 1: Validate
        invoice_data = {"amount": amount, "vendor_wallet": vendor_wallet}
        validation_status = await self._step_validate_request(invoice_data)
        
        if validation_status != "APPROVED":
            logger.info(f"Saga paused at Validation: {validation_status}")
            return {"status": "PAUSED", "reason": validation_status}

        # Step 2: Reserve (Database)
        reserved = await self._step_reserve_funds_db(invoice_data)
        if not reserved:
            return {"status": "FAILED", "reason": "DB_RESERVATION_FAILED"}

        # Step 3: Execute (Blockchain)
        try:
            tx_hash = await self._step_execute_chain_transaction(vendor_wallet, amount)
            
            # Check if it was a failure response
            if "FAILED" in tx_hash:
                 return {"status": "FAILED", "reason": tx_hash}
            
            return {"status": "SUCCESS", "tx_hash": tx_hash}
            
        except Exception as e:
            logger.error(f"Saga failed at Blockchain Step: {e}")
            return {"status": "FAILED", "reason": str(e)}

    # --- STEP 1: VALIDATION ---
    async def _step_validate_request(self, invoice_data):
        logger.info("Step 1: Validating invoice against policy...")
        if not invoice_data.get("amount"):
            return "REQUIRES_APPROVAL"
        
        # DYNAMIC LIMIT CHECK
        if self.redis_client:
            # Fetch limit, default to 50.0 if missing
            limit_str = self.redis_client.get("system:approval_limit")
            limit = float(limit_str) if limit_str else 50.0
        else:
            limit = 50.0
            
        logger.info(f"🔍 Current Approval Limit: ${limit}")

        if float(invoice_data["amount"]) > limit:
            logger.info(f"⚠️ Amount exceeds limit (${limit}). Pausing.")
            return "REQUIRES_APPROVAL"
        
        return "APPROVED"

    # --- STEP 2: DB RESERVATION ---
    async def _step_reserve_funds_db(self, invoice_data):
        logger.info("Step 2: Reserving funds in Postgres Database...")
        # (Real DB logic would go here)
        await asyncio.sleep(0.1) 
        return True

    # --- STEP 3: BLOCKCHAIN EXECUTION (FIXED FOR TOKENS) ---
    async def _step_execute_chain_transaction(self, vendor_wallet, amount):
        logger.info(f"Step 3: Accessing Minato Blockchain...")

        # DEMO HACK: If the input is a name, swap it for a real wallet address
        if not vendor_wallet.startswith("0x"):
            logger.warning(f"⚠️ resolving vendor name '{vendor_wallet}' to demo address")
            # This is a random test wallet address to receive the payment
            vendor_wallet = "0x104F9C75c9F170e85D299F13766243838787Fa12" 
        # --- 👆 END BLOCK 👆 ---

        try:
            # 1. Load Keys
            private_key = os.getenv("WALLET_PRIVATE_KEY") # Ensure this matches your .env name
            if not private_key:
                raise Exception("CRITICAL: Private Key missing")
            
            account = self.w3.eth.account.from_key(private_key)
            my_address = account.address
            token_address = os.getenv("MNEE_TOKEN_ADDRESS")

            # 2. CHECK LIQUIDITY (The Fix: Check MNEE, not ETH)
            if token_address:
                # We are using the MNEE Token
                logger.info(f"Checking MNEE Token Balance at {token_address}...")
                
                # Call the Smart Contract
                raw_balance = self.mnee_contract.functions.balanceOf(my_address).call()
                # Convert from 18 decimals
                treasury_balance = self.w3.from_wei(raw_balance, 'ether')
                
                logger.info(f"💰 TREASURY BALANCE: {treasury_balance} MNEE")
            else:
                # Fallback to Native ETH if no token address found
                logger.warning("No Token Address found. Checking Native ETH balance.")
                wei_balance = self.w3.eth.get_balance(my_address)
                treasury_balance = self.w3.from_wei(wei_balance, 'ether')

            # 3. DECISION LOGIC
            if Decimal(treasury_balance) < Decimal(amount):
                error_msg = f"❌ INSUFFICIENT LIQUIDITY: Have {treasury_balance}, Need {amount}"
                logger.warning(error_msg)
                
                if self.redis_client:
                    self.redis_client.lpush("treasury:alerts", error_msg)
                
                self.email_service.send_alert("INSUFFICIENT_LIQUIDITY", error_msg)
                return "FAILED_NO_LIQUIDITY"

            logger.info("✅ Liquidity confirmed. Proceeding to Transfer...")

            # 4. EXECUTE TRANSFER (Write to Blockchain)
            # Create the transaction
            nonce = self.w3.eth.get_transaction_count(my_address)
            
            # Build the Token Transfer Transaction
            tx_data = self.mnee_contract.functions.transfer(
                vendor_wallet,
                self.w3.to_wei(amount, 'ether')
            ).build_transaction({
                'chainId': 1946, # Minato Chain ID
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })

            # Sign it
            signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key)
            
            # Send it
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hex = self.w3.to_hex(tx_hash)
            
            logger.info(f"🚀 Payment Sent! Hash: {tx_hex}")
            return tx_hex

        except Exception as e:
            logger.error(f"⚠️ Blockchain Error: {str(e)}")
            return f"FAILED_CHAIN_ERROR: {str(e)}"