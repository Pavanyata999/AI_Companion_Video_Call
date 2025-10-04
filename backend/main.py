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
from utils.redis_manager import redis_manager
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

# Store active connections
active_connections: Dict[str, Dict[str, Any]] = {}

# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Companion Video Call API is running", "status": "healthy"}

@app.post("/api/video/rooms", response_model=VideoRoom)
async def create_video_room(
    companion_id: str,
    user_id: str,
    expire_minutes: int = 60
):
    """Create a new video room"""
    try:
        logger.info(f"Creating video room for companion {companion_id} and user {user_id}")
        
        # Verify companion exists
        companion = await companion_service.get_companion_by_id(companion_id)
        if not companion:
            raise HTTPException(status_code=404, detail="Companion not found")
        
        # Create room
        room = await redis_manager.create_room(companion_id, user_id, expire_minutes)
        
        logger.info(f"Created room {room.roomId}")
        return room
        
    except Exception as e:
        logger.error(f"Error creating video room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create video room")

@app.get("/api/video/rooms/{room_id}", response_model=RoomInfo)
async def get_room_info(room_id: str):
    """Fetch or validate room info"""
    try:
        room = await redis_manager.get_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Check if room is expired
        if datetime.utcnow() > room.expiresAt:
            await redis_manager.update_room_status(room_id, "expired")
            raise HTTPException(status_code=410, detail="Room has expired")
        
        return RoomInfo(roomId=room_id, status=room.status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting room info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room info")

@app.get("/api/webrtc/config", response_model=ICEConfig)
async def get_webrtc_config():
    """Provide ICE server configuration"""
    try:
        config = webrtc_config_service.get_ice_config()
        logger.info("Providing WebRTC ICE configuration")
        return config
    except Exception as e:
        logger.error(f"Error getting WebRTC config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get WebRTC config")

@app.get("/api/companions", response_model=CompanionsResponse)
async def get_companions():
    """List available companions with images and metadata"""
    try:
        logger.info("Fetching companions")
        companions = await companion_service.fetch_companions()
        return CompanionsResponse(companions=companions)
    except Exception as e:
        logger.error(f"Error fetching companions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch companions")

@app.post("/api/video/recordings", response_model=RecordingUpload)
async def upload_recording(
    recording_id: str,
    room_id: str,
    url: str
):
    """Upload recorded session video file"""
    try:
        logger.info(f"Uploading recording {recording_id} for room {room_id}")
        
        # Verify room exists
        room = await redis_manager.get_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        recording = RecordingUpload(
            recordingId=recording_id,
            roomId=room_id,
            url=url
        )
        
        # Store recording info in Redis
        recording_key = f"recording:{recording_id}"
        redis_manager.redis_client.hset(recording_key, mapping={
            "recordingId": recording.recordingId,
            "roomId": recording.roomId,
            "url": recording.url,
            "uploadedAt": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Successfully uploaded recording {recording_id}")
        return recording
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading recording: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload recording")

@app.post("/api/chat/messages")
async def send_chat_message(message: ChatMessage):
    """Send chat message (REST fallback)"""
    try:
        logger.info(f"Sending chat message in room {message.roomId}")
        
        # Store message
        message_data = {
            "from": message.from_,
            "text": message.text,
            "timestamp": message.timestamp.isoformat()
        }
        
        await redis_manager.store_chat_message(message.roomId, message_data)
        
        # Broadcast to WebSocket clients if they're connected
        await sio.emit("message", message_data, room=message.roomId)
        
        return {"status": "success", "message": "Message sent"}
        
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Client {sid} connected")
    active_connections[sid] = {"connected_at": datetime.utcnow()}

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client {sid} disconnected")
    if sid in active_connections:
        del active_connections[sid]

@sio.event
async def join(sid, data):
    """Handle join room event"""
    try:
        join_event = JoinEvent(**data)
        logger.info(f"Client {sid} joining room {join_event.roomId}")
        
        # Verify room exists
        room = await redis_manager.get_room(join_event.roomId)
        if not room:
            await sio.emit("error", {"message": "Room not found"}, room=sid)
            return
        
        # Join the room
        await sio.enter_room(sid, join_event.roomId)
        active_connections[sid]["roomId"] = join_event.roomId
        active_connections[sid]["userId"] = join_event.userId
        active_connections[sid]["role"] = join_event.role
        
        # Notify others in the room
        await sio.emit("user_joined", {
            "userId": join_event.userId,
            "role": join_event.role
        }, room=join_event.roomId, skip_sid=sid)
        
        logger.info(f"Client {sid} joined room {join_event.roomId}")
        
    except Exception as e:
        logger.error(f"Error in join event: {e}")
        await sio.emit("error", {"message": "Failed to join room"}, room=sid)

@sio.event
async def offer(sid, data):
    """Handle WebRTC offer"""
    try:
        offer_event = OfferEvent(**data)
        logger.info(f"Offer from {offer_event.from_} in room {offer_event.roomId}")
        
        # Store signaling data
        signal_data = {
            "type": "offer",
            "from": offer_event.from_,
            "sdp": offer_event.sdp,
            "timestamp": datetime.utcnow().isoformat()
        }
        await redis_manager.store_webrtc_signal(offer_event.roomId, signal_data)
        
        # Forward to other clients in the room
        await sio.emit("offer", {
            "from": offer_event.from_,
            "sdp": offer_event.sdp
        }, room=offer_event.roomId, skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Error in offer event: {e}")
        await sio.emit("error", {"message": "Failed to handle offer"}, room=sid)

@sio.event
async def answer(sid, data):
    """Handle WebRTC answer"""
    try:
        answer_event = AnswerEvent(**data)
        logger.info(f"Answer from {answer_event.from_} in room {answer_event.roomId}")
        
        # Store signaling data
        signal_data = {
            "type": "answer",
            "from": answer_event.from_,
            "sdp": answer_event.sdp,
            "timestamp": datetime.utcnow().isoformat()
        }
        await redis_manager.store_webrtc_signal(answer_event.roomId, signal_data)
        
        # Forward to other clients in the room
        await sio.emit("answer", {
            "from": answer_event.from_,
            "sdp": answer_event.sdp
        }, room=answer_event.roomId, skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Error in answer event: {e}")
        await sio.emit("error", {"message": "Failed to handle answer"}, room=sid)

@sio.event
async def candidate(sid, data):
    """Handle WebRTC ICE candidate"""
    try:
        candidate_event = CandidateEvent(**data)
        logger.info(f"ICE candidate from {candidate_event.from_} in room {candidate_event.roomId}")
        
        # Store signaling data
        signal_data = {
            "type": "candidate",
            "from": candidate_event.from_,
            "candidate": candidate_event.candidate,
            "timestamp": datetime.utcnow().isoformat()
        }
        await redis_manager.store_webrtc_signal(candidate_event.roomId, signal_data)
        
        # Forward to other clients in the room
        await sio.emit("candidate", {
            "from": candidate_event.from_,
            "candidate": candidate_event.candidate
        }, room=candidate_event.roomId, skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Error in candidate event: {e}")
        await sio.emit("error", {"message": "Failed to handle candidate"}, room=sid)

@sio.event
async def leave(sid, data):
    """Handle leave room event"""
    try:
        leave_event = LeaveEvent(**data)
        logger.info(f"Client {sid} leaving room {leave_event.roomId}")
        
        # Leave the room
        await sio.leave_room(sid, leave_event.roomId)
        
        # Notify others in the room
        await sio.emit("user_left", {
            "userId": leave_event.userId
        }, room=leave_event.roomId, skip_sid=sid)
        
        # Clean up connection data
        if sid in active_connections:
            active_connections[sid].pop("roomId", None)
            active_connections[sid].pop("userId", None)
            active_connections[sid].pop("role", None)
        
    except Exception as e:
        logger.error(f"Error in leave event: {e}")

@sio.event
async def end(sid, data):
    """Handle end call event"""
    try:
        end_event = EndEvent(**data)
        logger.info(f"Ending call in room {end_event.roomId}")
        
        # Notify all clients in the room
        await sio.emit("call_ended", {
            "reason": end_event.reason
        }, room=end_event.roomId)
        
        # Update room status
        await redis_manager.update_room_status(end_event.roomId, "inactive")
        
    except Exception as e:
        logger.error(f"Error in end event: {e}")

@sio.event
async def message(sid, data):
    """Handle chat message"""
    try:
        logger.info(f"Chat message from {sid}")
        
        # Store message
        message_data = {
            "from": data.get("from", "unknown"),
            "text": data.get("text", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        room_id = active_connections.get(sid, {}).get("roomId")
        if room_id:
            await redis_manager.store_chat_message(room_id, message_data)
            
            # Broadcast to all clients in the room
            await sio.emit("message", message_data, room=room_id)
        
    except Exception as e:
        logger.error(f"Error in message event: {e}")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI Companion Video Call API")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Companion Video Call API")
    await companion_service.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
