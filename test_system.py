#!/usr/bin/env python3
"""
AI Companion Video Call - Test Script
Tests the backend API endpoints
"""

import asyncio
import httpx
import json
import time

API_BASE_URL = "http://localhost:8000"

async def test_api_endpoints():
    """Test all API endpoints"""
    print("🧪 Testing AI Companion Video Call API")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Health Check
        print("\n1️⃣ Testing Health Check...")
        try:
            response = await client.get(f"{API_BASE_URL}/")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 2: Get Companions
        print("\n2️⃣ Testing Companions API...")
        try:
            response = await client.get(f"{API_BASE_URL}/api/companions")
            if response.status_code == 200:
                data = response.json()
                companions = data.get("companions", [])
                print(f"✅ Companions API passed - Found {len(companions)} companions")
                for companion in companions[:2]:  # Show first 2
                    print(f"   - {companion.get('name', 'Unknown')} ({companion.get('id', 'No ID')})")
            else:
                print(f"❌ Companions API failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Companions API error: {e}")
        
        # Test 3: Get WebRTC Config
        print("\n3️⃣ Testing WebRTC Config...")
        try:
            response = await client.get(f"{API_BASE_URL}/api/webrtc/config")
            if response.status_code == 200:
                config = response.json()
                ice_servers = config.get("iceServers", [])
                print(f"✅ WebRTC Config passed - Found {len(ice_servers)} ICE servers")
                for server in ice_servers[:2]:  # Show first 2
                    urls = server.get("urls", [])
                    print(f"   - {urls[0] if urls else 'No URL'}")
            else:
                print(f"❌ WebRTC Config failed: {response.status_code}")
        except Exception as e:
            print(f"❌ WebRTC Config error: {e}")
        
        # Test 4: Create Video Room
        print("\n4️⃣ Testing Video Room Creation...")
        try:
            room_data = {
                "companion_id": "companion_1",
                "user_id": "test_user_123",
                "expire_minutes": 60
            }
            response = await client.post(
                f"{API_BASE_URL}/api/video/rooms",
                json=room_data
            )
            if response.status_code == 200:
                room = response.json()
                room_id = room.get("roomId")
                print(f"✅ Video Room Creation passed - Room ID: {room_id}")
                
                # Test 5: Get Room Info
                print("\n5️⃣ Testing Room Info Retrieval...")
                try:
                    response = await client.get(f"{API_BASE_URL}/api/video/rooms/{room_id}")
                    if response.status_code == 200:
                        room_info = response.json()
                        print(f"✅ Room Info Retrieval passed - Status: {room_info.get('status')}")
                    else:
                        print(f"❌ Room Info Retrieval failed: {response.status_code}")
                except Exception as e:
                    print(f"❌ Room Info Retrieval error: {e}")
                
            else:
                print(f"❌ Video Room Creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Video Room Creation error: {e}")
        
        # Test 6: Send Chat Message
        print("\n6️⃣ Testing Chat Message...")
        try:
            message_data = {
                "roomId": "test_room_123",
                "from": "test_user",
                "text": "Hello from test!"
            }
            response = await client.post(
                f"{API_BASE_URL}/api/chat/messages",
                json=message_data
            )
            if response.status_code == 200:
                print("✅ Chat Message passed")
            else:
                print(f"❌ Chat Message failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Chat Message error: {e}")
        
        # Test 7: Upload Recording
        print("\n7️⃣ Testing Recording Upload...")
        try:
            recording_data = {
                "recordingId": "test_recording_123",
                "roomId": "test_room_123",
                "url": "https://example.com/recording.webm"
            }
            response = await client.post(
                f"{API_BASE_URL}/api/video/recordings",
                json=recording_data
            )
            if response.status_code == 200:
                print("✅ Recording Upload passed")
            else:
                print(f"❌ Recording Upload failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Recording Upload error: {e}")

def test_frontend_build():
    """Test if frontend can be built"""
    print("\n8️⃣ Testing Frontend Build...")
    import subprocess
    import os
    
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    
    if not os.path.exists(frontend_dir):
        print("❌ Frontend directory not found")
        return
    
    try:
        # Check if node_modules exists
        node_modules = os.path.join(frontend_dir, "node_modules")
        if not os.path.exists(node_modules):
            print("⚠️  Frontend dependencies not installed")
            print("   Run: cd frontend && npm install")
            return
        
        # Try to build
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Frontend build passed")
        else:
            print(f"❌ Frontend build failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("❌ Frontend build timed out")
    except Exception as e:
        print(f"❌ Frontend build error: {e}")

async def main():
    """Main test function"""
    print("🚀 AI Companion Video Call - System Test")
    print("Make sure the backend is running on http://localhost:8000")
    print("=" * 60)
    
    # Test backend API
    await test_api_endpoints()
    
    # Test frontend build
    test_frontend_build()
    
    print("\n" + "=" * 60)
    print("🎉 Test completed!")
    print("\n📱 Next steps:")
    print("1. Start Redis: brew services start redis")
    print("2. Start Backend: cd backend && python main.py")
    print("3. Start Frontend: cd frontend && npm run dev")
    print("4. Open browser: http://localhost:3000")

if __name__ == "__main__":
    asyncio.run(main())
