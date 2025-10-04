import httpx
import logging
from typing import List, Optional
from config import settings
from models import Companion, CompanionsResponse

logger = logging.getLogger(__name__)

class CompanionService:
    def __init__(self):
        self.base_url = settings.PERSONA_FETCHER_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_companions(self) -> List[Companion]:
        """Fetch companions from external API"""
        try:
            logger.info(f"Fetching companions from {self.base_url}")
            response = await self.client.get(self.base_url)
            response.raise_for_status()
            
            data = response.json()
            companions = []
            
            # Parse the response from the external API
            if isinstance(data, list):
                for item in data:
                    companion = Companion(
                        id=item.get("id", ""),
                        name=item.get("name", "Unknown"),
                        avatarUrl=item.get("avatarUrl", ""),
                        description=item.get("description"),
                        voiceId=item.get("voiceId"),  # ElevenLabs voice ID
                        personality=item.get("personality"),
                        metadata=item.get("metadata", {})
                    )
                    companions.append(companion)
            
            logger.info(f"Successfully fetched {len(companions)} companions")
            return companions
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching companions: {e}")
            # Return mock data as fallback
            return self._get_mock_companions()
        except Exception as e:
            logger.error(f"Error fetching companions: {e}")
            return self._get_mock_companions()
    
    def _get_mock_companions(self) -> List[Companion]:
        """Return mock companions as fallback"""
        logger.info("Using mock companions as fallback")
        return [
            Companion(
                id="companion_1",
                name="Alex",
                avatarUrl="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face",
                description="A friendly and helpful AI companion",
                voiceId="voice_1",
                personality="Friendly and supportive",
                metadata={"age": "25", "interests": ["technology", "music"]}
            ),
            Companion(
                id="companion_2",
                name="Sarah",
                avatarUrl="https://images.unsplash.com/photo-1494790108755-2616b612b786?w=200&h=200&fit=crop&crop=face",
                description="An intelligent and curious AI companion",
                voiceId="voice_2",
                personality="Intelligent and curious",
                metadata={"age": "28", "interests": ["science", "art"]}
            ),
            Companion(
                id="companion_3",
                name="Marcus",
                avatarUrl="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face",
                description="A creative and artistic AI companion",
                voiceId="voice_3",
                personality="Creative and artistic",
                metadata={"age": "30", "interests": ["art", "literature"]}
            )
        ]
    
    async def get_companion_by_id(self, companion_id: str) -> Optional[Companion]:
        """Get a specific companion by ID"""
        companions = await self.fetch_companions()
        for companion in companions:
            if companion.id == companion_id:
                return companion
        return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global companion service instance
companion_service = CompanionService()
