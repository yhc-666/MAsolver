from __future__ import annotations

import re
import numpy as np
from typing import TYPE_CHECKING, Dict, Tuple, Optional, Any
from sentence_transformers import SentenceTransformer, util
import torch
import logging
from pydantic import Field

from . import visibility_registry as VisibilityRegistry
from .base import BaseVisibility

if TYPE_CHECKING:
    from agentverse.environments import BaseEnvironment

@VisibilityRegistry.register("sparse")
class SparseVisibility(BaseVisibility):
    """
    Sparse visibility rule implementing the gating mechanism from the multi-turn interaction algorithm.
    Controls which agents can see messages from other agents based on preference computation.
    """
    
    # Declare all fields for Pydantic compatibility
    bert_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    lambda_param: float = Field(default=0.5)
    alpha: float = Field(default=1.0)  # Sparsity control parameter
    model: Optional[Any] = Field(default=None)
    gates: Dict[int, Any] = Field(default_factory=dict)
    confidences: Dict[int, Dict[int, float]] = Field(default_factory=dict)
    previous_outputs: Dict[int, Dict[int, str]] = Field(default_factory=dict)
    current_preferences: Dict[int, Any] = Field(default_factory=dict)  # Pre_ij for each round
    historical_preferences: Dict[int, Any] = Field(default_factory=dict)  # Pre_ij_hat for each round
    agent_name_to_idx: Dict[str, int] = Field(default_factory=dict)
    # Cumulative statistics
    cumulative_total_gates: int = Field(default=0)
    cumulative_open_gates: int = Field(default=0)
    
    def __init__(self, bert_model: str = "sentence-transformers/all-MiniLM-L6-v2", lambda_param: float = 0.5, alpha: float = 1.0, **kwargs):
        """
        Initialize sparse visibility with BERT model for similarity computation.
        
        Args:
            bert_model: Name of the BERT model to use for similarity computation
            lambda_param: Hyperparameter λ from the algorithm for preference computation
            alpha: Sparsity control parameter (>1.0 for more sparse, <1.0 for less sparse)
        """
        super().__init__(
            bert_model=bert_model,
            lambda_param=lambda_param,
            alpha=alpha,
            **kwargs
        )
        
        try:
            self.model = SentenceTransformer(bert_model)
            logging.info(f"Loaded BERT model: {bert_model}")
        except Exception as e:
            logging.error(f"Failed to load BERT model {bert_model}: {e}")
            logging.warning("Falling back to random similarity scores")
            # model already None from field defaults
    
    def extract_confidence(self, message_content: str) -> float:
        """
        Extract confidence score from agent output.
        
        Args:
            message_content: The agent's message content
            
        Returns:
            Confidence score between 0 and 1
        """
        # Look for confidence in format "Confidence: X.X"
        match = re.search(r'Confidence:\s*([\d.]+)', message_content, re.IGNORECASE)
        if match:
            try:
                confidence = float(match.group(1))
                return max(0.0, min(1.0, confidence))
            except ValueError:
                pass
        
        # Default confidence if not found
        return 0.5
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts using sentence-transformers.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity score in range [-1, 1]
        """
        if self.model is None:
            # Fallback to random similarity if model not available
            return np.random.random()
        
        try:
            # Encode both texts with normalization for cosine similarity
            embeddings = self.model.encode([text1, text2], 
                                          convert_to_tensor=True, 
                                          normalize_embeddings=True)
            
            # Compute cosine similarity (returns value in [-1, 1])
            similarity = util.cos_sim(embeddings[0], embeddings[1]).item()

            print(f"Similarity by BERT: {similarity}")
            return similarity
            
        except Exception as e:
            logging.warning(f"Error computing similarity: {e}")
            return 0.5  # Default similarity
    
    def compute_preference(self, i: int, j: int, round: int) -> float:
        """
        Calculate current preference Pre_i→j for round.
        
        Args:
            i: Index of agent i
            j: Index of agent j
            round: Current round number (0-indexed)
            
        Returns:
            Pre_i→j: Current round preference value
        """
        if i == j:
            return float('inf')  # Agent always prefers itself
        
        # Get current confidences
        C_i = self.confidences[round].get(i, 0.5)
        C_j = self.confidences[round].get(j, 0.5)
        
        # Avoid division by zero
        if C_j == 0:
            C_j = 0.01
        
        # Get similarity between agent outputs
        if round in self.previous_outputs:
            output_i = self.previous_outputs[round].get(i, "")
            output_j = self.previous_outputs[round].get(j, "")
            similarity = self.compute_similarity(output_i, output_j)
        else:
            similarity = 0.5
        
        # Compute current round preference Pre_i→j
        # Pre_i→j = C_i/C_j + λ(1 - cos(A_j, A_i))
        preference = (C_i / C_j) + self.lambda_param * (1 - similarity)
        
        return preference
    
    def update_visible_agents(self, environment: BaseEnvironment) -> None:
        """
        Update the gate matrix based on preference comparisons.
        
        Args:
            environment: The environment containing agents and messages
        """
        # Get current round (0-indexed: round 0 is the first round)
        round = environment.cnt_turn
        n_agents = len(environment.agents)
        
        # Build agent name to index mapping if not done
        if not self.agent_name_to_idx:
            for idx, agent in enumerate(environment.agents):
                self.agent_name_to_idx[agent.name] = idx
        
        # Initialize gates for first round (all open)
        if round == 0 or round - 1 not in self.gates:
            self.gates[round] = np.ones((n_agents, n_agents))
        else:
            # Copy previous round's gates
            self.gates[round] = self.gates[round - 1].copy()
        
        # Initialize storage for this round
        self.confidences[round] = {}
        self.previous_outputs[round] = {}
        self.current_preferences[round] = np.zeros((n_agents, n_agents))
        self.historical_preferences[round] = np.zeros((n_agents, n_agents))
        
        # Extract confidences and outputs from messages
        for message in environment.last_messages:
            if message.sender in self.agent_name_to_idx:
                agent_idx = self.agent_name_to_idx[message.sender]
                self.confidences[round][agent_idx] = self.extract_confidence(message.content)
                self.previous_outputs[round][agent_idx] = message.content
        
        # Compute preferences and update gates
        for i in range(n_agents):
            for j in range(n_agents):
                if i != j:
                    # Compute current preference Pre_i→j
                    pre_ij = self.compute_preference(i, j, round)
                    self.current_preferences[round][i, j] = pre_ij
                    
                    # Compute historical average Pre_i→j_hat
                    if round == 0:
                        # First round: Pre_i→j_hat = Pre_i→j
                        pre_ij_hat = pre_ij
                    else:
                        # Subsequent rounds: weighted average
                        # Pre_i→j_hat(round) = (1/(round+1)) * (Pre_i→j_hat(round-1) * round + Pre_i→j(round))
                        prev_hat = self.historical_preferences[round - 1][i, j]
                        pre_ij_hat = (1 / (round + 1)) * (prev_hat * round + pre_ij)
                    
                    self.historical_preferences[round][i, j] = pre_ij_hat
                    
                    # Update gate: Close if current preference < alpha * previous round's historical average
                    if round > 0:
                        prev_round_hat = self.historical_preferences[round - 1][i, j]
                        if pre_ij < self.alpha * prev_round_hat:
                            # Close the gate (set O_i→j = 0)
                            self.gates[round][i, j] = 0
                            logging.info(f"Round {round}: Closing gate from agent {i} to agent {j} (Pre={pre_ij:.3f} < α*Pre_hat_prev={self.alpha*prev_round_hat:.3f}, α={self.alpha})")
        
        # Store current round gates for updater to access
        # We'll access this through the visibility object itself
        
        # Log gate statistics
        open_gates = np.sum(self.gates[round]) - n_agents  # Exclude self-connections
        total_gates = n_agents * (n_agents - 1)
        logging.info(f"Round {round}: {open_gates}/{total_gates} gates open ({100*open_gates/total_gates:.1f}%)")
        
        # Update cumulative statistics
        self.cumulative_total_gates += total_gates
        self.cumulative_open_gates += int(open_gates)
    
    def get_cumulative_sparse_rate(self) -> float:
        """Calculate the cumulative sparse rate across all rounds.
        
        Returns:
            Sparse rate (proportion of closed gates): 1 - (open gates / total gates)
        """
        if self.cumulative_total_gates == 0:
            return 0.0
        return 1 - (self.cumulative_open_gates / self.cumulative_total_gates)
    
    def reset(self) -> None:
        """Reset visibility state for new instance"""
        self.gates.clear()
        self.confidences.clear()
        self.previous_outputs.clear()
        self.current_preferences.clear()
        self.historical_preferences.clear()
        self.agent_name_to_idx.clear()
        # Reset cumulative statistics
        self.cumulative_total_gates = 0
        self.cumulative_open_gates = 0