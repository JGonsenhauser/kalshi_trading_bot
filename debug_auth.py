"""
Debug script to verify Kalshi authentication setup
"""
import os
from dotenv import load_dotenv
from kalshi_auth import KalshiAuth
import jwt

load_dotenv()

print("="*60)
print("🔍 Kalshi Authentication Debug")
print("="*60)
print()

# Load credentials
api_key = os.getenv('KALSHI_API_KEY')
private_key_path = os.getenv('KALSHI_PRIVATE_KEY_PATH')

print(f"API Key: {api_key}")
print(f"Private Key Path: {private_key_path}")
print()

# Test authentication
try:
    auth = KalshiAuth(api_key, private_key_path)
    print("✅ Private key loaded successfully")
    print()
    
    # Generate token
    token = auth.generate_token()
    print(f"✅ JWT Token generated ({len(token)} chars)")
    print(f"Token (first 50 chars): {token[:50]}...")
    print()
    
    # Decode token to inspect
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("📋 Token Payload:")
    for key, value in decoded.items():
        print(f"  {key}: {value}")
    print()
    
    # Get auth headers
    headers = auth.get_auth_headers()
    print("📋 Auth Headers:")
    for key, value in headers.items():
        if key == "Authorization":
            print(f"  {key}: Bearer {value[:50]}...")
        else:
            print(f"  {key}: {value}")
    
    print()
    print("="*60)
    print("✅ Authentication setup appears correct")
    print("If API still fails, the issue may be:")
    print("1. API key not activated on Kalshi")
    print("2. Wrong JWT payload format for Kalshi")
    print("3. Private key doesn't match API key")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
