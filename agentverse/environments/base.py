from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List
import time

from pydantic import BaseModel, Field

# from agentverse.agents.agent import Agent

if TYPE_CHECKING:
    from agentverse.agents.base import BaseAgent
    from agentverse.environments.rules.base import Rule
    from agentverse.message import Message


class BaseEnvironment(BaseModel):
    """
    Base class for environment.

    Args:
        agents: List of agents
        rule: Rule for the environment
        max_turns: Maximum number of turns
        cnt_turn: Current turn number
        last_messages: Messages from last turn
        rule_params: Variables set by the rule
        complete_chat_history: Centralized chat history with real-time logging
    """

    agents: List[BaseAgent]
    rule: Rule
    max_turns: int = 10
    cnt_turn: int = 0
    last_messages: List[Message] = Field(default_factory=list)
    rule_params: Dict = {}
    complete_chat_history: List[Dict] = Field(default_factory=list)

    @abstractmethod
    async def step(self) -> List[Message]:
        """Run one step of the environment"""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the environment"""
        pass

    def is_done(self) -> bool:
        """Check if the environment is done"""
        return self.cnt_turn >= self.max_turns

    def add_to_chat_history(self, messages: List[Message]) -> None:
        """Add messages to centralized chat history with round and sender tagging"""
        for message in messages:
            if hasattr(message, 'sender') and hasattr(message, 'content'):
                self.complete_chat_history.append({
                    "round": self.cnt_turn + 1,  # Use 1-based round numbering
                    "role": message.sender,
                    "content": message.content,
                    "timestamp": time.time()
                })

    def get_chat_history(self) -> List[Dict]:
        """Get the complete chat history in the format expected by run scripts"""
        return [{"role": entry["role"], "content": entry["content"]} 
                for entry in self.complete_chat_history]
