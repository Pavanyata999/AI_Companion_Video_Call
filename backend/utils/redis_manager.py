import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from config import settings
from models import VideoRoom, RoomStatus, Companion, CompanionsResponse

class RedisManager:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def create_room(self, companion_id: str, user_id: str, expire_minutes: int = 60) -> VideoRoom:
        """Create a new video room"""
        room_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        room = VideoRoom(
            roomId=room_id,
            companionId=companion_id,
            userId=user_id,
            expiresAt=expires_at,
            status=RoomStatus.ACTIVE
        )
        
        # Store room data in Redis
        room_key = f"room:{room_id}"
        self.redis_client.hset(room_key, mapping={
            "roomId": room.roomId,
            "companionId": room.companionId,
            "userId": room.userId,
            "expiresAt": room.expiresAt.isoformat(),
            "status": room.status.value,
            "createdAt": room.createdAt.isoformat()
        })
        
        # Set expiration
        self.redis_client.expire(room_key, expire_minutes * 60)
        
        return room
    
    async def get_room(self, room_id: str) -> Optional[VideoRoom]:
        """Get room information"""
        room_key = f"room:{room_id}"
        room_data = self.redis_client.hgetall(room_key)
        
        if not room_data:
            return None
        
        return VideoRoom(
            roomId=room_data["roomId"],
            companionId=room_data["companionId"],
            userId=room_data["userId"],
            expiresAt=datetime.fromisoformat(room_data["expiresAt"]),
            status=RoomStatus(room_data["status"]),
            createdAt=datetime.fromisoformat(room_data["createdAt"])
        )
    
    async def update_room_status(self, room_id: str, status: RoomStatus) -> bool:
        """Update room status"""
        room_key = f"room:{room_id}"
        return bool(self.redis_client.hset(room_key, "status", status.value))
    
    async def delete_room(self, room_id: str) -> bool:
        """Delete a room"""
        room_key = f"room:{room_id}"
        return bool(self.redis_client.delete(room_key))
    
    async def store_chat_message(self, room_id: str, message_data: Dict[str, Any]) -> None:
        """Store chat message"""
        message_key = f"chat:{room_id}"
        self.redis_client.lpush(message_key, json.dumps(message_data))
        # Keep only last 100 messages
        self.redis_client.ltrim(message_key, 0, 99)
    
    async def get_chat_messages(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat messages for a room"""
        message_key = f"chat:{room_id}"
        messages = self.redis_client.lrange(message_key, 0, limit - 1)
        return [json.loads(msg) for msg in messages]
    
    async def store_webrtc_signal(self, room_id: str, signal_data: Dict[str, Any]) -> None:
        """Store WebRTC signaling data"""
        signal_key = f"signal:{room_id}"
        self.redis_client.lpush(signal_key, json.dumps(signal_data))
        # Keep only last 20 signals
        self.redis_client.ltrim(signal_key, 0, 19)
    
    async def get_webrtc_signals(self, room_id: str) -> List[Dict[str, Any]]:
        """Get WebRTC signaling data for a room"""
        signal_key = f"signal:{room_id}"
        signals = self.redis_client.lrange(signal_key, 0, -1)
        return [json.loads(signal) for signal in signals]

# Global Redis manager instance
redis_manager = RedisManager()
