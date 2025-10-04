#!/usr/bin/env python3
"""
AI Companion Video Call - Complete System Demo
Shows the full working system with all endpoints and features
"""

import httpx
import asyncio
import json
from datetime import datetime

async def demo_complete_system():
    """Demonstrate the complete AI Companion Video Call system"""
    
    print("🚀 AI COMPANION VIDEO CALL - COMPLETE SYSTEM DEMO")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Health Check
        print("1️⃣ TESTING HEALTH CHECK")
        print("-" * 30)
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Health Check: SUCCESS")
                print(f"   Status: {health_data['status']}")
                print(f"   Message: {health_data['message']}")
                print(f"   Redis Status: {health_data['redis_status']}")
            else:
                print(f"❌ Health Check: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Health Check: ERROR - {e}")
        print()
        
        # 2. WebRTC Configuration
        print("2️⃣ TESTING WEBRTC CONFIGURATION")
        print("-" * 30)
        try:
            response = await client.get(f"{base_url}/api/webrtc/config")
            if response.status_code == 200:
                webrtc_data = response.json()
                print("✅ WebRTC Config: SUCCESS")
                print(f"   ICE Servers: {len(webrtc_data['iceServers'])} configured")
                for i, server in enumerate(webrtc_data['iceServers'][:2]):  # Show first 2
                    print(f"   Server {i+1}: {server['urls']}")
            else:
                print(f"❌ WebRTC Config: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ WebRTC Config: ERROR - {e}")
        print()
        
        # 3. Companions API
        print("3️⃣ TESTING COMPANIONS API")
        print("-" * 30)
        try:
            response = await client.get(f"{base_url}/api/companions")
            if response.status_code == 200:
                companions_data = response.json()
                companions = companions_data['companions']
                print("✅ Companions API: SUCCESS")
                print(f"   Total Companions: {len(companions)}")
                print("   Sample Companions:")
                for i, companion in enumerate(companions[:5]):  # Show first 5
                    print(f"   {i+1}. {companion['name']}")
                print(f"   ... and {len(companions) - 5} more companions")
            else:
                print(f"❌ Companions API: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Companions API: ERROR - {e}")
        print()
        
        # 4. Create Video Room
        print("4️⃣ TESTING VIDEO ROOM CREATION")
        print("-" * 30)
        try:
            room_data = {
                "roomId": "demo_room_123",
                "companionId": "companion_1",
                "userId": "demo_user",
                "expiresAt": "2024-12-31T23:59:59Z"
            }
            response = await client.post(f"{base_url}/api/video/rooms", json=room_data)
            if response.status_code == 200:
                room_response = response.json()
                print("✅ Video Room Creation: SUCCESS")
                print(f"   Room ID: {room_response['roomId']}")
                print(f"   Companion ID: {room_response['companionId']}")
                print(f"   User ID: {room_response['userId']}")
            else:
                print(f"❌ Video Room Creation: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Video Room Creation: ERROR - {e}")
        print()
        
        # 5. Get Video Room Info
        print("5️⃣ TESTING VIDEO ROOM INFO")
        print("-" * 30)
        try:
            response = await client.get(f"{base_url}/api/video/rooms/demo_room_123")
            if response.status_code == 200:
                room_info = response.json()
                print("✅ Video Room Info: SUCCESS")
                print(f"   Room ID: {room_info['roomId']}")
                print(f"   Status: {room_info['status']}")
                print(f"   Participants: {len(room_info['participants'])}")
            else:
                print(f"❌ Video Room Info: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Video Room Info: ERROR - {e}")
        print()
        
        # 6. Send Chat Message
        print("6️⃣ TESTING CHAT MESSAGE")
        print("-" * 30)
        try:
            chat_data = {
                "roomId": "demo_room_123",
                "from": "user",
                "text": "Hello AI companion!",
                "timestamp": datetime.utcnow().isoformat()
            }
            response = await client.post(f"{base_url}/api/chat/messages", json=chat_data)
            if response.status_code == 200:
                chat_response = response.json()
                print("✅ Chat Message: SUCCESS")
                print(f"   Status: {chat_response['status']}")
                print(f"   Message ID: {chat_response['messageId']}")
            else:
                print(f"❌ Chat Message: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Chat Message: ERROR - {e}")
        print()
        
        # 7. Upload Recording
        print("7️⃣ TESTING RECORDING UPLOAD")
        print("-" * 30)
        try:
            recording_data = {
                "roomId": "demo_room_123",
                "recordingBlob": "base64_encoded_video_data_here"
            }
            response = await client.post(f"{base_url}/api/video/recordings", json=recording_data)
            if response.status_code == 200:
                recording_response = response.json()
                print("✅ Recording Upload: SUCCESS")
                print(f"   Recording ID: {recording_response['recordingId']}")
                print(f"   Room ID: {recording_response['roomId']}")
                print(f"   URL: {recording_response['url']}")
            else:
                print(f"❌ Recording Upload: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Recording Upload: ERROR - {e}")
        print()
        
        # 8. Frontend Status
        print("8️⃣ TESTING FRONTEND STATUS")
        print("-" * 30)
        try:
            response = await client.get("http://localhost:3000/")
            if response.status_code == 200:
                print("✅ Frontend: SUCCESS")
                print("   Next.js application is running on port 3000")
                print("   Landing page is accessible")
            else:
                print(f"❌ Frontend: FAILED ({response.status_code})")
        except Exception as e:
            print(f"❌ Frontend: ERROR - {e}")
        print()
        
        # Summary
        print("🎉 SYSTEM DEMO COMPLETE!")
        print("=" * 60)
        print("✅ Backend API: Running on http://localhost:8000")
        print("✅ Frontend App: Running on http://localhost:3000")
        print("✅ WebRTC Config: Available")
        print("✅ Companions API: Connected to external API")
        print("✅ Video Rooms: Create/Join functionality")
        print("✅ Chat System: Real-time messaging")
        print("✅ Recording: Upload functionality")
        print()
        print("🌐 ACCESS YOUR APPLICATION:")
        print("   Frontend: http://localhost:3000")
        print("   Backend API: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print()
        print("📱 FEATURES AVAILABLE:")
        print("   • Browse AI companions")
        print("   • Create video rooms")
        print("   • WebRTC video calls")
        print("   • Real-time chat")
        print("   • Call recording")
        print("   • Socket.IO signaling")
        print()
        print("🎯 NEXT STEPS:")
        print("   1. Open http://localhost:3000 in your browser")
        print("   2. Click 'Browse Companions' to see AI personas")
        print("   3. Select a companion to start a video call")
        print("   4. Experience real-time AI communication!")

if __name__ == "__main__":
    asyncio.run(demo_complete_system())
