from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from config import settings
from models import (
    VideoRoom, RoomInfo, ICEConfig, CompanionsResponse, 
    ChatMessage, RecordingUpload, JoinEvent, OfferEvent, 
    AnswerEvent, CandidateEvent, LeaveEvent, EndEvent
)
from utils.companion_service import companion_service
from utils.webrtc_config import webrtc_config_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Companion Video Call API",
    description="Backend API for AI Companion Video Call & Streaming",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=True,
    engineio_logger=True
)

# Create Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

# Store active connections (in-memory instead of Redis)
active_connections: Dict[str, Dict[str, Any]] = {}
active_rooms: Dict[str, Dict[str, Any]] = {}

# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "message": "AI Companion Video Call API is running",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis_status": "disabled (using in-memory storage)"
    }

# Video room endpoints
@app.post("/api/video/rooms", response_model=VideoRoom)
async def create_video_room(room_data: VideoRoom):
    """Create a new video room"""
    try:
        room_id = room_data.roomId
        companion_id = room_data.companionId
        user_id = room_data.userId
        
        # Store room info in memory
        active_rooms[room_id] = {
            "roomId": room_id,
            "companionId": companion_id,
            "userId": user_id,
            "createdAt": datetime.utcnow().isoformat(),
            "expiresAt": room_data.expiresAt,
            "status": "active",
            "participants": []
        }
        
        logger.info(f"Created video room: {room_id} for user: {user_id} with companion: {companion_id}")
        
        return VideoRoom(
            roomId=room_id,
            companionId=companion_id,
            userId=user_id,
            expiresAt=room_data.expiresAt
        )
    except Exception as e:
        logger.error(f"Error creating video room: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/video/rooms/{room_id}", response_model=RoomInfo)
async def get_video_room(room_id: str):
    """Get video room information"""
    try:
        if room_id not in active_rooms:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room_info = active_rooms[room_id]
        return RoomInfo(
            roomId=room_id,
            status=room_info["status"],
            createdAt=room_info["createdAt"],
            expiresAt=room_info["expiresAt"],
            participants=room_info["participants"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video room: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebRTC configuration endpoint
@app.get("/api/webrtc/config", response_model=ICEConfig)
async def get_webrtc_config():
    """Get WebRTC ICE server configuration"""
    try:
        config = webrtc_config_service.get_ice_config()
        return ICEConfig(iceServers=config["iceServers"])
    except Exception as e:
        logger.error(f"Error getting WebRTC config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Companions endpoint
@app.get("/api/companions", response_model=CompanionsResponse)
async def get_companions():
    """Get available AI companions"""
    try:
        companions = await companion_service.fetch_companions()
        return CompanionsResponse(companions=companions)
    except Exception as e:
        logger.error(f"Error getting companions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoints
@app.post("/api/chat/messages")
async def send_chat_message(message: ChatMessage):
    """Send a chat message"""
    try:
        # Store message in memory (in a real app, you'd store in database)
        logger.info(f"Chat message from {message.from_user} in room {message.roomId}: {message.text}")
        
        # Broadcast message to room participants via Socket.IO
        await sio.emit("chat_message", {
            "roomId": message.roomId,
            "from": message.from_user,
            "text": message.text,
            "timestamp": message.timestamp
        }, room=message.roomId)
        
        return {"status": "sent", "messageId": f"msg_{datetime.utcnow().timestamp()}"}
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Recording endpoints
@app.post("/api/video/recordings")
async def upload_recording(recording: RecordingUpload):
    """Upload recorded session video"""
    try:
        recording_id = f"rec_{datetime.utcnow().timestamp()}"
        logger.info(f"Recording uploaded: {recording_id} for room: {recording.roomId}")
        
        return {
            "recordingId": recording_id,
            "roomId": recording.roomId,
            "url": f"/recordings/{recording_id}",
            "status": "uploaded"
        }
    except Exception as e:
        logger.error(f"Error uploading recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")
    active_connections[sid] = {
        "connected_at": datetime.utcnow().isoformat(),
        "room_id": None,
        "user_id": None,
        "role": None
    }

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")
    if sid in active_connections:
        connection_info = active_connections[sid]
        room_id = connection_info.get("room_id")
        
        if room_id and room_id in active_rooms:
            # Remove participant from room
            participants = active_rooms[room_id]["participants"]
            active_rooms[room_id]["participants"] = [
                p for p in participants if p["sid"] != sid
            ]
            
            # Notify other participants
            await sio.emit("participant_left", {
                "roomId": room_id,
                "userId": connection_info.get("user_id"),
                "role": connection_info.get("role")
            }, room=room_id, skip_sid=sid)
        
        del active_connections[sid]

@sio.event
async def join(sid, data: JoinEvent):
    """Handle join room event"""
    try:
        room_id = data.roomId
        user_id = data.userId
        role = data.role
        
        # Update connection info
        if sid in active_connections:
            active_connections[sid].update({
                "room_id": room_id,
                "user_id": user_id,
                "role": role
            })
        
        # Add to room
        if room_id not in active_rooms:
            active_rooms[room_id] = {
                "roomId": room_id,
                "participants": [],
                "status": "active"
            }
        
        participant = {
            "sid": sid,
            "userId": user_id,
            "role": role,
            "joinedAt": datetime.utcnow().isoformat()
        }
        
        active_rooms[room_id]["participants"].append(participant)
        
        # Join Socket.IO room
        await sio.enter_room(sid, room_id)
        
        # Notify other participants
        await sio.emit("participant_joined", {
            "roomId": room_id,
            "userId": user_id,
            "role": role
        }, room=room_id, skip_sid=sid)
        
        logger.info(f"User {user_id} joined room {room_id} as {role}")
        
    except Exception as e:
        logger.error(f"Error in join event: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.event
async def offer(sid, data: OfferEvent):
    """Handle WebRTC offer"""
    try:
        room_id = data.roomId
        from_user = data.from_user
        sdp = data.sdp
        
        # Broadcast offer to other participants in the room
        await sio.emit("offer", {
            "roomId": room_id,
            "from": from_user,
            "sdp": sdp
        }, room=room_id, skip_sid=sid)
        
        logger.info(f"Offer from {from_user} in room {room_id}")
        
    except Exception as e:
        logger.error(f"Error in offer event: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.event
async def answer(sid, data: AnswerEvent):
    """Handle WebRTC answer"""
    try:
        room_id = data.roomId
        from_user = data.from_user
        sdp = data.sdp
        
        # Broadcast answer to other participants in the room
        await sio.emit("answer", {
            "roomId": room_id,
            "from": from_user,
            "sdp": sdp
        }, room=room_id, skip_sid=sid)
        
        logger.info(f"Answer from {from_user} in room {room_id}")
        
    except Exception as e:
        logger.error(f"Error in answer event: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.event
async def candidate(sid, data: CandidateEvent):
    """Handle WebRTC ICE candidate"""
    try:
        room_id = data.roomId
        from_user = data.from_user
        candidate = data.candidate
        
        # Broadcast candidate to other participants in the room
        await sio.emit("candidate", {
            "roomId": room_id,
            "from": from_user,
            "candidate": candidate
        }, room=room_id, skip_sid=sid)
        
        logger.info(f"ICE candidate from {from_user} in room {room_id}")
        
    except Exception as e:
        logger.error(f"Error in candidate event: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.event
async def leave(sid, data: LeaveEvent):
    """Handle leave room event"""
    try:
        room_id = data.roomId
        user_id = data.userId
        
        # Remove from room participants
        if room_id in active_rooms:
            participants = active_rooms[room_id]["participants"]
            active_rooms[room_id]["participants"] = [
                p for p in participants if p["sid"] != sid
            ]
        
        # Leave Socket.IO room
        await sio.leave_room(sid, room_id)
        
        # Notify other participants
        await sio.emit("participant_left", {
            "roomId": room_id,
            "userId": user_id
        }, room=room_id, skip_sid=sid)
        
        logger.info(f"User {user_id} left room {room_id}")
        
    except Exception as e:
        logger.error(f"Error in leave event: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

@sio.event
async def end(sid, data: EndEvent):
    """Handle end call event"""
    try:
        room_id = data.roomId
        reason = data.reason
        
        # Notify all participants in the room
        await sio.emit("call_ended", {
            "roomId": room_id,
            "reason": reason
        }, room=room_id)
        
        # Clean up room
        if room_id in active_rooms:
            del active_rooms[room_id]
        
        logger.info(f"Call ended in room {room_id}, reason: {reason}")
        
    except Exception as e:
        logger.error(f"Error in end event: {e}")
        await sio.emit("error", {"message": str(e)}, room=sid)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Companion Video Call API")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
