"""
Core LLM module with intent classification and agent routing.
This module acts as the central coordinator between user input and specialized agents.
"""

import os
import httpx
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from agents import BaseAgent, InventoryAgent, LessonPlanAgent

load_dotenv()

LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:8001/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Meta-Llama-3.1-8B-Instruct")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()


class LLMRouter:
    """
    Routes user messages to appropriate agents based on intent classification.
    Uses the fine-tuned LLM for understanding STEM center specific queries.
    """
    
    def __init__(self):
        self.agents: List[BaseAgent] = []
        self._register_agents()
    
    def _register_agents(self):
        """
        Register all available agents.
        Easy to add/remove agents for modular design.
        """
        # Register inventory agent
        self.agents.append(InventoryAgent())
        # Register lesson plan agent (Phase 2)
        self.agents.append(LessonPlanAgent())
        # Future agents can be added here:
        # self.agents.append(ProcurementAgent())
        # self.agents.append(ApprovalAgent())
        # self.agents.append(LessonPlanAgent())
    
    async def route_message(self, user_message: str, context: Dict[str, Any], session: AsyncSession) -> Dict[str, Any]:
        """
        Route user message to the most appropriate agent.
        
        Returns:
            {
                "agent_used": str,
                "response": str,
                "data": Any,
                "success": bool
            }
        """
        # Check each agent's ability to handle the message
        agent_scores = []
        for agent in self.agents:
            can_handle, confidence = await agent.can_handle(user_message, context)
            if can_handle:
                agent_scores.append((agent, confidence))
        
        # Sort by confidence
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        if agent_scores:
            # Use the most confident agent
            best_agent, confidence = agent_scores[0]
            
            try:
                result = await best_agent.execute(user_message, context, session)
                return {
                    "agent_used": best_agent.name,
                    "confidence": confidence,
                    "response": result["message"],
                    "data": result.get("data"),
                    "success": result["success"],
                    "actions": result.get("actions", [])
                }
            except Exception as e:
                return {
                    "agent_used": best_agent.name,
                    "confidence": confidence,
                    "response": f"Error executing agent: {str(e)}",
                    "data": None,
                    "success": False,
                    "actions": ["error"]
                }
        else:
            # No agent can handle - use general LLM
            return await self._fallback_llm_response(user_message, context)
    
    async def _fallback_llm_response(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback to general LLM when no agent can handle the query.
        """
        system_prompt = (
            "You are an AI assistant for a STEM center group chat. "
            "You help teachers with inventory, lesson plans, approvals, and procurement. "
            "Be concise, helpful, and professional. If you're unsure, guide the user on what you can help with."
        )
        
        try:
            response = await chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ])
            return {
                "agent_used": "GeneralLLM",
                "confidence": 0.3,
                "response": response,
                "data": None,
                "success": True,
                "actions": ["general_chat"]
            }
        except Exception as e:
            return {
                "agent_used": "GeneralLLM",
                "confidence": 0.0,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "data": None,
                "success": False,
                "actions": ["error"]
            }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered agents.
        """
        return [agent.get_info() for agent in self.agents]


async def chat_completion(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 512) -> str:
    """
    Calls an OpenAI-compatible /v1/chat/completions endpoint.
    Works with llama.cpp server, vLLM, or other compatible backends.
    """
    url = f"{LLM_API_BASE}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


# Global router instance
llm_router = LLMRouter()
