import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class MNEEWallet:
    def __init__(self):
        # 1. Connect to Blockchain (Sepolia Testnet)
        rpc_url = os.getenv("MNEE_RPC_URL", "https://rpc.sepolia.org")
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # 2. Load Your Identity
        self.private_key = os.getenv("PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("PRIVATE_KEY is missing in .env")
        
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.my_address = self.account.address
        
        # 3. MNEE Contract Details (You need to get this from Hackathon Docs)
        # This is a generic ERC-20 ABI (Interface)
        self.contract_address = "0x..." # <--- REPLACE THIS WITH MNEE ADDRESS
        self.erc20_abi = [
            {
                "constant": False,
                "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        # Initialize Contract
        if self.w3.is_connected():
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.erc20_abi)
            print(f"✅ Connected to Blockchain. Wallet: {self.my_address}")
        else:
            print("❌ Failed to connect to RPC URL.")

    def send_mnee(self, to_address: str, amount_usd: float):
        """
        Sends MNEE tokens to a vendor.
        Note: MNEE likely uses 6 or 18 decimals. We assume 18 here (Standard).
        """
        # Convert 45.00 USD -> Wei (Atomic Units)
        # If MNEE has 6 decimals (like USDC), change 18 to 6.
        decimals = 18 
        amount_in_wei = int(amount_usd * (10 ** decimals))
        
        # 1. Build Transaction
        nonce = self.w3.eth.get_transaction_count(self.my_address)
        
        tx = self.contract.functions.transfer(
            to_address,
            amount_in_wei
        ).build_transaction({
            'chainId': 11155111, # Sepolia Chain ID
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # 2. Sign Transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        
        # 3. Broadcast
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return self.w3.to_hex(tx_hash)