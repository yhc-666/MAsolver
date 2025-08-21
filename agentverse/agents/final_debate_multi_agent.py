from __future__ import annotations

import logging
import bdb
from string import Template
from typing import TYPE_CHECKING, List, Optional, Dict

from agentverse.message import Message, StructuredPrompt
from pydantic import Field

from . import agent_registry
from .llm_eval_multi_agent import LLMEvalAgent

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentverse.environments.base import BaseEnvironment

from openai import RateLimitError

@agent_registry.register("final_debate_multi")
class FinalDebateMultiAgent(LLMEvalAgent):
    """
    Agent for final debate stage that supports predict and reasoning parameters
    from solver results.
    """
    
    # Additional attributes for solver results
    predict: str = ""      # Prediction from corresponding solver
    reasoning: str = ""    # Reasoning from corresponding solver
    options: str = ""      # Question options
    final_answer: str = ""  # Final answer parsed from output
    
    # Memory token tracking
    memory_token_usage: Dict = Field(default_factory=lambda: {
        "total_memory_tokens": 0,
        "rounds": []  # List of memory tokens per round
    })
    
    def _fill_prompt_template(self, env_description: str = "", env=None) -> StructuredPrompt:
        """
        Fill the placeholders in the prompt template and return structured prompt components.
        Overrides parent method to handle predict and reasoning parameters.
        
        Args:
            env_description: Environment description
            env: Environment object for turn information
            
        Returns:
            StructuredPrompt with system_content and user_content split by ${chat_history}
        """
        # Determine turn-specific instruction based on current turn
        if env and hasattr(env, 'cnt_turn') and hasattr(env, 'max_turns') and hasattr(env, 'agents'):
            # Check if using concurrent order
            is_final = False
            if hasattr(env, 'rule') and hasattr(env.rule, 'order'):
                order_type = env.rule.order.__class__.__name__.lower()
                if 'concurrent' in order_type:
                    # For concurrent: all agents speak in same round, so final round is just max_turns - 1
                    is_final = env.cnt_turn >= env.max_turns - 1
                else:
                    # For sequential: original logic
                    is_final = env.cnt_turn >= env.max_turns - len(env.agents)
            else:
                # Default to sequential logic if no order rule found
                is_final = env.cnt_turn >= env.max_turns - len(env.agents)
            
            turn_specific_instruction = self.final_prompt_to_use if is_final else Template(self.normal_turn_instruction).safe_substitute(agent_name=self.name)
        else:
            turn_specific_instruction = Template(self.normal_turn_instruction).safe_substitute(agent_name=self.name)
        
        input_arguments = {
            "agent_name": self.name,
            "role_description": self.role_description,
            "question": self.question,
            "context": self.context,
            "options": self.options,
            "predict": self.predict,
            "reasoning": self.reasoning,
            "final_prompt": self.final_prompt,
            "turn_specific_instruction": turn_specific_instruction,
            # Intentionally not filling chat_history to keep it as split point
        }
        
        # Use safe_substitute to preserve ${chat_history} as placeholder
        partially_filled_template = Template(self.prompt_template).safe_substitute(input_arguments)
        
        # Split by ${chat_history} to create structured prompt
        chat_history_placeholder = "${chat_history}"
        
        if chat_history_placeholder in partially_filled_template:
            # Split by ${chat_history}
            parts = partially_filled_template.split(chat_history_placeholder)
            if len(parts) == 2:
                system_content = parts[0].strip()
                user_content = parts[1].strip()
            else:
                # If multiple ${chat_history} or other anomalies, fallback
                system_content = partially_filled_template
                user_content = ""
        else:
            # If no ${chat_history} in template, all content as system_content
            system_content = partially_filled_template
            user_content = ""
        
        return StructuredPrompt(
            system_content=system_content,
            user_content=user_content
        )
    
    def step(self, env_description: str = "") -> Message:
        """Override step to save final_answer from parser"""
        structured_prompt = self._fill_prompt_template(env_description)

        parsed_response = None
        for i in range(self.max_retry):
            try:
                response = self.llm.generate_response(structured_prompt, self.memory.messages)
                parsed_response = self.output_parser.parse(response)
                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(e)
                logging.warning("Retrying...")
                continue

        if parsed_response is None:
            logging.error(f"{self.name} failed to generate valid response.")

        # Save final_answer if available
        if parsed_response and hasattr(parsed_response, 'return_values'):
            self.final_answer = parsed_response.return_values.get("final_answer", "")

        message = Message(
            content=""
            if parsed_response is None
            else parsed_response.return_values["output"],
            sender=self.name,
            receiver=self.get_receiver(),
        )
        return message

    async def astep(self, env: Optional["BaseEnvironment"] = None, env_description: str = "") -> Message:
        """Override astep to save final_answer from parser"""
        # Check if using concurrent order for final round detection
        if env:
            is_final_round = False
            if hasattr(env, 'rule') and hasattr(env.rule, 'order'):
                order_type = env.rule.order.__class__.__name__.lower()
                if 'concurrent' in order_type:
                    is_final_round = env.cnt_turn >= env.max_turns - 1
                else:
                    is_final_round = env.cnt_turn >= env.max_turns - len(env.agents)
            else:
                is_final_round = env.cnt_turn >= env.max_turns - len(env.agents)
            
            if is_final_round:
                self.final_prompt = self.final_prompt_to_use

        structured_prompt = self._fill_prompt_template(env_description, env)

        parsed_response = None
        should_break = False
        
        while True:
            for i in range(self.max_retry):
                try:
                    response = await self.llm.agenerate_response(structured_prompt, self.memory.messages)
                    
                    # Track memory tokens if available
                    if hasattr(response, 'memory_tokens'):
                        self.memory_token_usage["total_memory_tokens"] += response.memory_tokens
                        self.memory_token_usage["rounds"].append({
                            "round": env.cnt_turn if env else 0,
                            "memory_tokens": response.memory_tokens
                        })
                    
                    if env:
                        parsed_response = self.output_parser.parse(response, env.cnt_turn, env.max_turns, len(env.agents))
                    else:
                        parsed_response = self.output_parser.parse(response)
                    should_break = True
                    break
                except (KeyboardInterrupt, bdb.BdbQuit):
                    raise
                except Exception as e:
                    if isinstance(e, RateLimitError):
                        logging.error(e)
                        logging.warning("Retrying Until rate limit error disappear...")
                        import time
                        time.sleep(5)  # Add 5-second delay before retry
                        break
                    else:
                        logging.error(e)
                        logging.warning("Retrying...")
                        continue
            else:
                logging.error(f"After {self.max_retry} failed try, end the loop")
                break
            if should_break:
                break
            else:
                continue

        if parsed_response is None:
            logging.error(f"{self.name} failed to generate valid response.")

        # Save final_answer if available
        if parsed_response and hasattr(parsed_response, 'return_values'):
            self.final_answer = parsed_response.return_values.get("final_answer", "")

        message = Message(
            content=""
            if parsed_response is None
            else parsed_response.return_values["output"],
            sender=self.name,
            receiver=self.get_receiver(),
        )
        return message

    def reset(self) -> None:
        """Reset the agent for next instance"""
        super().reset()
        # Don't reset predict and reasoning - these are instance data from solvers
        # that should persist throughout the conversation
        # self.predict = ""     # Keep solver prediction
        # self.reasoning = ""   # Keep solver reasoning
        # Don't reset options - it's instance data that should persist
        # self.options = ""  # Remove this line - options should not be reset
        self.final_answer = ""  # Reset final_answer for new conversation
        # Reset memory token tracking
        self.memory_token_usage = {
            "total_memory_tokens": 0,
            "rounds": []
        } 