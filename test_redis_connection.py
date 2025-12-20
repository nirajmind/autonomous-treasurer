import redis

print("-----------------------------------------")
print("🔌 TESTING REDIS CONNECTION...")
print("-----------------------------------------")

try:
    # Try connecting to Docker from Windows
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Force a handshake
    r.ping()
    print("✅ SUCCESS: Connected to Redis!")
    
    # Write a test log
    r.lpush("treasury:daily_logs", "Test Log Entry")
    print("✅ SUCCESS: Wrote test data to 'treasury:daily_logs'")
    
except Exception as e:
    print("❌ FAILURE: Could not connect.")
    print(f"Error Detail: {e}")
    print("\nTroubleshooting:")
    print("1. Is the Docker container running? (Run 'docker ps')")
    print("2. Is port 6379 mapped? (Look for '0.0.0.0:6379->6379/tcp')")