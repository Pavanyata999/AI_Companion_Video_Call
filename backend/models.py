from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RoomStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class UserRole(str, Enum):
    USER = "user"
    COMPANION = "companion"

class VideoRoom(BaseModel):
    roomId: str
    companionId: str
    userId: str
    expiresAt: datetime
    status: RoomStatus = RoomStatus.ACTIVE
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class RoomInfo(BaseModel):
    roomId: str
    status: RoomStatus

class ICEConfig(BaseModel):
    iceServers: List[Dict[str, Any]]

class Companion(BaseModel):
    id: str
    name: str
    avatarUrl: str
    description: Optional[str] = None
    voiceId: Optional[str] = None  # ElevenLabs voice ID
    personality: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CompanionsResponse(BaseModel):
    companions: List[Companion]

class ChatMessage(BaseModel):
    roomId: str
    from_: str = Field(alias="from")
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RecordingUpload(BaseModel):
    recordingId: str
    roomId: str
    url: str

# WebSocket Event Models
class JoinEvent(BaseModel):
    roomId: str
    userId: str
    role: UserRole

class OfferEvent(BaseModel):
    roomId: str
    from_: str = Field(alias="from")
    sdp: str

class AnswerEvent(BaseModel):
    roomId: str
    from_: str = Field(alias="from")
    sdp: str

class CandidateEvent(BaseModel):
    roomId: str
    from_: str = Field(alias="from")
    candidate: Dict[str, Any]

class LeaveEvent(BaseModel):
    roomId: str
    userId: str

class EndEvent(BaseModel):
    roomId: str
    reason: Optional[str] = None
