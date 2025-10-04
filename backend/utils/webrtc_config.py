import logging
from typing import Dict, Any, List
from config import settings
from models import ICEConfig

logger = logging.getLogger(__name__)

class WebRTCConfigService:
    def __init__(self):
        self.stun_servers = [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]}
        ]
        
        self.turn_servers = []
        if settings.TURN_USERNAME and settings.TURN_CREDENTIAL:
            self.turn_servers.append({
                "urls": [settings.TURN_SERVER_URL],
                "username": settings.TURN_USERNAME,
                "credential": settings.TURN_CREDENTIAL
            })
    
    def get_ice_config(self) -> ICEConfig:
        """Get ICE server configuration for WebRTC"""
        ice_servers = self.stun_servers + self.turn_servers
        
        logger.info(f"Providing ICE configuration with {len(ice_servers)} servers")
        
        return ICEConfig(iceServers=ice_servers)
    
    def get_media_constraints(self) -> Dict[str, Any]:
        """Get default media constraints for WebRTC"""
        return {
            "video": {
                "width": {"ideal": 1280, "max": 1920},
                "height": {"ideal": 720, "max": 1080},
                "frameRate": {"ideal": 30, "max": 60}
            },
            "audio": {
                "echoCancellation": True,
                "noiseSuppression": True,
                "autoGainControl": True
            }
        }

# Global WebRTC config service instance
webrtc_config_service = WebRTCConfigService()
