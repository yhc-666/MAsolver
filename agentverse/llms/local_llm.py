import logging
import re
import time
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from agentverse.llms.base import LLMResult
from . import llm_registry
from .base import BaseChatModel, BaseModelArgs
from agentverse.message import Message

logger = logging.getLogger(__name__)

# 共享的模型instances字典，用于避免重复加载同一模型
_model_instances = {}

try:
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    is_vllm_available = True
except ImportError:
    is_vllm_available = False
    logger.warning("vLLM or transformers not available. Local LLM support disabled.")


from pydantic import ConfigDict

class LocalLLMArgs(BaseModelArgs):
    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)
    
    model_path: str = Field(default="")
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)
    top_k: int = Field(default=50)
    max_tokens: int = Field(default=512)
    tensor_parallel_size: int = Field(default=1)
    gpu_memory_utilization: float = Field(default=0.9)
    max_model_len: int = Field(default=4096)
    trust_remote_code: bool = Field(default=True)


class BaseLocalLLM(BaseChatModel):
    """Local LLM base class"""
    args: LocalLLMArgs = Field(default_factory=LocalLLMArgs)
    
    def __init__(self, max_retry: int = 3, **kwargs):
        if not is_vllm_available:
            raise ImportError("vLLM and transformers are required for local LLM support")
        
        # 处理参数
        args = LocalLLMArgs()
        args_dict = args.dict()
        
        for k, v in args_dict.items():
            args_dict[k] = kwargs.pop(k, v)
        
        if len(kwargs) > 0:
            logger.warning(f"Unused arguments: {kwargs}")
        
        # 创建LocalLLMArgs实例
        local_args = LocalLLMArgs(**args_dict)
        
        super().__init__(args=local_args, max_retry=max_retry)
        
        # 生成模型实例键（用于共享）
        self._model_key = f"{self.args.model_path}_{self.args.tensor_parallel_size}_{self.args.gpu_memory_utilization}"
        
        # 初始化模型和tokenizer
        self._init_model()
    
    def _init_model(self):
        """初始化模型和tokenizer"""
        if self._model_key in _model_instances:
            logger.info(f"🔄 Reusing existing model instance for {self.args.model_path}")
            self._llm = _model_instances[self._model_key]['llm']
            self._tokenizer = _model_instances[self._model_key]['tokenizer']
        else:
            logger.info(f"🚀 Loading new model instance: {self.args.model_path}")
            start_time = time.time()
            
            # 加载tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.args.model_path,
                trust_remote_code=self.args.trust_remote_code
            )
            
            # 加载LLM
            self._llm = LLM(
                model=self.args.model_path,
                tensor_parallel_size=self.args.tensor_parallel_size,
                gpu_memory_utilization=self.args.gpu_memory_utilization,
                max_model_len=self.args.max_model_len,
                trust_remote_code=self.args.trust_remote_code
            )
            
            # 缓存模型实例
            _model_instances[self._model_key] = {
                'llm': self._llm,
                'tokenizer': self._tokenizer
            }
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f} seconds")
    
    def _construct_messages(self, prompt: str, chat_memory: List[Message], final_prompt: str):
        chat_messages = []
        for item_memory in chat_memory:
            chat_messages.append(str(item_memory.sender) + ": " + str(item_memory.content))
        processed_prompt = [{"role": "user", "content": prompt}]
        for chat_message in chat_messages:
            processed_prompt.append({"role": "assistant", "content": chat_message})
        processed_prompt.append({"role": "user", "content": final_prompt})
        return processed_prompt
    
    def _apply_chat_template(self, messages: List[Dict]):
        """应用chat template"""
        try:
            # 使用tokenizer的chat template
            if hasattr(self._tokenizer, 'apply_chat_template') and self._tokenizer.chat_template:
                #print(f"🔄 Applied chat template")
                formatted_prompt = self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
                #print(f"🔄 Formatted prompt: {formatted_prompt}")
                return formatted_prompt
            else:
                # 回退到简单格式
                return self._simple_format(messages)
        except Exception as e:
            logger.warning(f"Failed to apply chat template: {e}. Using simple format.")
            return self._simple_format(messages)
    
    def _simple_format(self, messages: List[Dict]):
        """简单的消息格式化"""
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted += f"System: {content}\n"
            elif role == "user":
                formatted += f"User: {content}\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n"
        formatted += "Assistant: "
        return formatted
    
    def _filter_think_tokens(self, text: str) -> str:
        """过滤think tokens"""
        filtered_text = text
        
        # 1. 首先处理从开头到结束标签的情况（过滤开头的思考内容）
        start_to_end_patterns = [
            r'^.*?</think>',
            r'^.*?</thinking>',
            r'^.*?\[/think\]',
            r'^.*?\[/thinking\]',
            r'^.*?</thought>',
            r'^.*?\[/thought\]'
        ]
        
        for pattern in start_to_end_patterns:
            filtered_text = re.sub(pattern, '', filtered_text, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. 然后处理完整的think token块
        complete_patterns = [
            r'<think>.*?</think>',
            r'<thinking>.*?</thinking>',
            r'\[think\].*?\[/think\]',
            r'\[thinking\].*?\[/thinking\]',
            r'<thought>.*?</thought>',
            r'\[thought\].*?\[/thought\]'
        ]
        
        for pattern in complete_patterns:
            filtered_text = re.sub(pattern, '', filtered_text, flags=re.DOTALL | re.IGNORECASE)
        
        return filtered_text.strip()
    
    def generate_response(self, prompt: str, chat_memory: List[Message], final_prompt: str) -> LLMResult:
        """生成响应"""
        try:
            # 构造消息
            messages = self._construct_messages(prompt, chat_memory, final_prompt)
            print(f"🔄 Messages: {messages}")
            
            # 应用chat template
            formatted_prompt = self._apply_chat_template(messages)
            
            # 设置采样参数
            sampling_params = SamplingParams(
                temperature=self.args.temperature,
                top_p=self.args.top_p,
                top_k=self.args.top_k,
                max_tokens=self.args.max_tokens
            )
            
            # 生成响应
            outputs = self._llm.generate([formatted_prompt], sampling_params)
            
            if outputs and len(outputs) > 0:
                output = outputs[0]
                generated_text = output.outputs[0].text
                
                # 过滤think tokens
                filtered_text = self._filter_think_tokens(generated_text)
                
                # 计算token使用量
                prompt_tokens = len(output.prompt_token_ids) if hasattr(output, 'prompt_token_ids') else 0
                completion_tokens = len(output.outputs[0].token_ids) if output.outputs[0].token_ids else 0
                
                return LLMResult(
                    content=filtered_text,
                    send_tokens=prompt_tokens,
                    recv_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            else:
                raise RuntimeError("No output generated")
                
        except Exception as e:
            logger.error(f"Error generating response with local LLM: {e}")
            raise
    
    async def agenerate_response(self, prompt: str, chat_memory: List[Message], final_prompt: str) -> LLMResult:
        """异步生成响应（当前使用同步实现）"""
        return self.generate_response(prompt, chat_memory, final_prompt)


@llm_registry.register("deepseek-local")
class DeepseekLocalLLM(BaseLocalLLM):
    """Deepseek本地LLM"""
    
    def __init__(self, max_retry: int = 3, **kwargs):
        if 'model_path' not in kwargs:
            kwargs['model_path'] = "/mnt/sdb/ssuser/llm_models/Deepseek-14B"
        super().__init__(max_retry=max_retry, **kwargs)


@llm_registry.register("qwen-local")
class QwenLocalLLM(BaseLocalLLM):
    """Qwen本地LLM"""
    
    def __init__(self, max_retry: int = 3, **kwargs):
        if 'model_path' not in kwargs:
            kwargs['model_path'] = "/mnt/sdb/ssuser/llm_models/Qwen-14B"
        super().__init__(max_retry=max_retry, **kwargs)


@llm_registry.register("chatglm-local")
class ChatGLMLocalLLM(BaseLocalLLM):
    """ChatGLM本地LLM"""
    
    def __init__(self, max_retry: int = 3, **kwargs):
        if 'model_path' not in kwargs:
            kwargs['model_path'] = "/mnt/sdb/ssuser/llm_models/ChatGLM-6B"
        super().__init__(max_retry=max_retry, **kwargs)


@llm_registry.register("llama-local")
class LlamaLocalLLM(BaseLocalLLM):
    """Llama本地LLM"""
    
    def __init__(self, max_retry: int = 3, **kwargs):
        if 'model_path' not in kwargs:
            kwargs['model_path'] = "/mnt/sdb/ssuser/llm_models/Llama-2-7b-chat-hf"
        super().__init__(max_retry=max_retry, **kwargs) 