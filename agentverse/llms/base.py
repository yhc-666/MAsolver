from abc import abstractmethod
from typing import Dict, List

from pydantic import BaseModel, Field
from agentverse.message import Message, StructuredPrompt


class LLMResult(BaseModel):
    content: str
    send_tokens: int = 0  # Not tracking API tokens
    recv_tokens: int = 0  # Not tracking API tokens
    total_tokens: int = 0  # Not tracking API tokens
    memory_tokens: int = 0  # NEW: memory-only tokens


class BaseModelArgs(BaseModel):
    pass


class BaseLLM(BaseModel):
    args: BaseModelArgs = Field(default_factory=BaseModelArgs)
    max_retry: int = Field(default=3)

    @abstractmethod
    def generate_response(self, structured_prompt: "StructuredPrompt", chat_memory: List[Message]) -> LLMResult:
        pass

    @abstractmethod
    async def agenerate_response(self, structured_prompt: "StructuredPrompt", chat_memory: List[Message]) -> LLMResult:
        pass


class BaseChatModel(BaseLLM):
    pass


class BaseCompletionModel(BaseLLM):
    pass
