#!/usr/bin/env python3
"""
AI Companion Video Call - Health Check Explanation
Shows why health check fails and how to fix it
"""

import httpx
import asyncio
import subprocess
import time
import sys

def check_backend_status():
    """Check if backend is running"""
    print("🔍 DIAGNOSING HEALTH CHECK FAILURE")
    print("=" * 50)
    
    # Check if port 8000 is in use
    try:
        result = subprocess.run(['lsof', '-i', ':8000'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Port 8000 is in use - Backend might be running")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print("❌ Port 8000 is NOT in use - Backend is NOT running")
    except FileNotFoundError:
        print("⚠️  lsof command not available, checking with netstat...")
        try:
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            if ':8000' in result.stdout:
                print("✅ Port 8000 appears to be in use")
            else:
                print("❌ Port 8000 is NOT in use")
        except FileNotFoundError:
            print("⚠️  Cannot check port status - tools not available")
    
    print("\n🔧 WHY HEALTH CHECK FAILS:")
    print("1. Backend server is not running on port 8000")
    print("2. Redis server is not running (required for backend)")
    print("3. Dependencies might not be installed")
    
    print("\n🚀 HOW TO FIX:")
    print("1. Install Redis:")
    print("   brew install redis")
    print("   brew services start redis")
    print("\n2. Start Backend:")
    print("   cd backend")
    print("   pip install -r requirements.txt")
    print("   python3 main.py")
    print("\n3. Test Health Check:")
    print("   curl http://localhost:8000/")
    
    print("\n📊 EXPECTED HEALTH CHECK OUTPUT:")
    print('{"message": "AI Companion Video Call API is running", "status": "healthy"}')

async def test_health_check():
    """Test the health check endpoint"""
    print("\n🧪 TESTING HEALTH CHECK...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/")
            if response.status_code == 200:
                print("✅ Health check SUCCESS!")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"❌ Health check FAILED!")
                print(f"   Status Code: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except httpx.ConnectError:
        print("❌ Health check FAILED!")
        print("   Error: Connection refused - Backend not running")
        return False
    except Exception as e:
        print(f"❌ Health check FAILED!")
        print(f"   Error: {e}")
        return False

def show_backend_startup():
    """Show what backend startup should look like"""
    print("\n🎬 EXPECTED BACKEND STARTUP OUTPUT:")
    print("=" * 50)
    print("$ cd backend && python3 main.py")
    print("")
    print("INFO:__main__:Starting AI Companion Video Call API")
    print("INFO:__main__:Redis URL: redis://localhost:6379")
    print("INFO:__main__:CORS Origins: ['http://localhost:3000', 'http://127.0.0.1:3000']")
    print("Server initialized for sanic.")
    print("INFO:engineio.server:Server initialized for sanic.")
    print("INFO:     Started server process [12345]")
    print("INFO:     Waiting for application startup.")
    print("INFO:     Application startup complete.")
    print("INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)")
    print("")
    print("✅ Backend is now running and ready for health checks!")

def show_working_health_check():
    """Show what a working health check looks like"""
    print("\n✅ WORKING HEALTH CHECK OUTPUT:")
    print("=" * 50)
    print("$ curl http://localhost:8000/")
    print("")
    print('{"message": "AI Companion Video Call API is running", "status": "healthy"}')
    print("")
    print("✅ Health check successful!")

async def main():
    """Main function"""
    print("🚀 AI COMPANION VIDEO CALL - HEALTH CHECK DIAGNOSIS")
    print("=" * 60)
    
    # Check backend status
    check_backend_status()
    
    # Test health check
    is_healthy = await test_health_check()
    
    if not is_healthy:
        print("\n🔧 SOLUTION STEPS:")
        print("1. Install Redis: brew install redis && brew services start redis")
        print("2. Install dependencies: cd backend && pip install -r requirements.txt")
        print("3. Start backend: python3 main.py")
        print("4. Test again: curl http://localhost:8000/")
        
        show_backend_startup()
        show_working_health_check()
    else:
        print("\n🎉 Backend is running correctly!")
        print("Health check is working as expected!")

if __name__ == "__main__":
    asyncio.run(main())
