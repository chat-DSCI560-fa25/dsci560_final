"""
Agent system for modular functionality.
Each agent handles a specific domain (inventory, procurement, approvals, etc.)
"""

from agents.base_agent import BaseAgent
from agents.inventory_agent import InventoryAgent

__all__ = ['BaseAgent', 'InventoryAgent']
