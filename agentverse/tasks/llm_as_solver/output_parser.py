from __future__ import annotations

import re
from typing import Union

from agentverse.parser import OutputParser, LLMResult
from agentverse.utils import AgentAction, AgentFinish
from agentverse.parser import OutputParserError, output_parser_registry


@output_parser_registry.register("llm_solver")
class LLMSolverParser(OutputParser):
    """
    Enhanced output parser for LLM Solver that extracts answer and reasoning
    from structured LLM responses.
    
    Expected format:
    <answer>A<reason>Your reasoning here...
    """
    
    def parse(self, output: LLMResult) -> Union[AgentAction, AgentFinish]:
        """
        Parse LLM output to extract answer and reasoning
        
        Args:
            output: LLM result containing the response content
            
        Returns:
            AgentFinish with parsed answer and reasoning
        """
        text = output.content
        cleaned_output = text.strip()
        answer, reasoning = self._extract_answer_and_reasoning(cleaned_output)
        validated_answer = self._validate_answer(answer)
        
        return AgentFinish(
            return_values={
                "answer": validated_answer,
                "reasoning": reasoning,
                "output": cleaned_output
            },
            log=cleaned_output
        )
    
    def _extract_answer_and_reasoning(self, text: str) -> tuple[str, str]:
        """
        Extract answer and reasoning from text using <answer>...<reason>... format
        
        Args:
            text: Raw text from LLM
            
        Returns:
            Tuple of (answer, reasoning)
        """
        pattern = r'<answer>\s*(.*?)\s*<reason>\s*(.*?)(?:\n|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            answer = match.group(1).strip()
            reasoning = match.group(2).strip()
            return answer, reasoning
        
        # If no match found, return empty answer with full text as reasoning
        return "", text.strip()
    
    def _validate_answer(self, answer: str) -> str:
        """
        Validate and normalize answer format
        
        Args:
            answer: Raw answer extracted from text
            
        Returns:
            Validated answer string
        """
        if not answer:
            return ""
        
        # Convert to uppercase for consistency
        answer = answer.upper()
        
        # Valid single letter answers
        if answer in ['A', 'B', 'C', 'D', 'E']:
            return answer
        
        # Valid True/False/Unknown answers
        answer_lower = answer.lower()
        if answer_lower in ['true', 'false', 'unknown']:
            return answer_lower.capitalize()
        
        # Handle common variations
        if answer.startswith('TRUE'):
            return 'true'
        elif answer.startswith('FALSE'):
            return 'false'
        elif answer.startswith('UNKNOWN'):
            return 'unknown'
        
        # Return as-is if not recognized (for flexibility)
        return answer
    
    def _clean_reasoning(self, reasoning: str) -> str:
        if not reasoning:
            return ""
        
        # Remove excessive whitespace
        reasoning = re.sub(r'\s+', ' ', reasoning)
        
        # Remove common prefixes
        reasoning = re.sub(r'^(Reasoning|REASONING|Reason|REASON)\s*:?\s*', '', reasoning)
        
        return reasoning.strip()
