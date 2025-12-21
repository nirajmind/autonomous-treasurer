import secrets
from web3 import Account

# 1. Generate a random 32-byte hexadecimal string
# This is cryptographically secure enough for a hackathon
priv = secrets.token_hex(32)
private_key = "0x" + priv

# 2. Derive the public address from that key
acct = Account.from_key(private_key)

print("------------------------------------------------------")
print("🔐 NEW TESTNET IDENTITY GENERATED")
print("------------------------------------------------------")
print(f"PRIVATE_KEY: {private_key}")
print(f"ADDRESS:     {acct.address}")
print("------------------------------------------------------")
print("👉 COPY 'PRIVATE_KEY' into your backend/.env file")
print("------------------------------------------------------")