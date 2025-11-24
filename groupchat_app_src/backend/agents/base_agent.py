"""
Base Agent class that all specialized agents inherit from.
Provides common interface for intent matching and action execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    Each agent must implement methods to:
    - Match user intent
    - Execute actions
    - Provide help/documentation
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.keywords = []
    
    @abstractmethod
    async def can_handle(self, user_message: str, context: Dict[str, Any]) -> tuple[bool, float]:
        """
        Determines if this agent can handle the given message.
        
        Args:
            user_message: The user's input text
            context: Additional context (user info, conversation history, etc.)
        
        Returns:
            Tuple of (can_handle: bool, confidence: float between 0-1)
        """
        pass
    
    @abstractmethod
    async def execute(self, user_message: str, context: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
        """
        Executes the agent's action based on the user message.
        
        Args:
            user_message: The user's input text
            context: Additional context
            session: Database session for operations
        
        Returns:
            Dictionary with response data:
            {
                "success": bool,
                "message": str,  # Human-readable response
                "data": Any,     # Additional structured data
                "actions": List[str]  # Actions performed
            }
        """
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """
        Returns a list of capabilities this agent provides.
        Used for help and documentation.
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Returns basic information about this agent.
        """
        return {
            "name": self.name,
            "description": self.description,
            "keywords": self.keywords
        }
