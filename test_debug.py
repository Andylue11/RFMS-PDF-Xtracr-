#!/usr/bin/env python3

import sys
print("Python version:", sys.version)

try:
    import requests
    print("✅ requests module loaded successfully")
except ImportError as e:
    print("❌ requests import failed:", e)

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv loaded successfully")
    
    load_dotenv('.env-test')
    import os
    
    STORE_CODE = os.getenv('RFMS_STORE_CODE')
    API_KEY = os.getenv('RFMS_API_KEY')
    BASE_URL = os.getenv('RFMS_BASE_URL')
    
    print(f"✅ Environment variables loaded:")
    print(f"   STORE_CODE: {STORE_CODE[:20]}..." if STORE_CODE else "   STORE_CODE: None")
    print(f"   API_KEY: {API_KEY[:10]}..." if API_KEY else "   API_KEY: None")
    print(f"   BASE_URL: {BASE_URL}")
    
except ImportError as e:
    print("❌ dotenv import failed:", e)
except Exception as e:
    print("❌ Environment loading failed:", e)

print("🎯 Debug test completed successfully!") 