import os
import json
import yaml
from argparse import ArgumentParser
from typing import Dict, List
from tqdm import tqdm
import numpy as np

from agentverse.agentverse import AgentVerse


def load_solver_results(symbolic_path: str, llm_path: str) -> List[Dict]:
    """
    Load and merge solver results from both symbolic and LLM solvers.
    
    Args:
        symbolic_path: Path to symbolic solver results
        llm_path: Path to LLM solver results
        
    Returns:
        List of merged data instances
    """
    print(f"Loading symbolic solver results from: {symbolic_path}")
    with open(symbolic_path, 'r', encoding='utf-8') as f:
        symbolic_results = json.load(f)
    
    print(f"Loading LLM solver results from: {llm_path}")
    with open(llm_path, 'r', encoding='utf-8') as f:
        llm_results = json.load(f)
    
    llm_results_by_id = {item['id']: item for item in llm_results}
    
    merged_data = []
    unmatched_ids = []
    
    for symbolic_item in symbolic_results:
        symbolic_id = symbolic_item['id']
        
        if symbolic_id not in llm_results_by_id:
            print(f"Warning: ID {symbolic_id} not found in llm_solver_results")
            unmatched_ids.append(symbolic_id)
            continue
        
        llm_item = llm_results_by_id[symbolic_id]
        
        # Merge data with symbolic results as primary source
        merged_item = {
            "id": symbolic_item["id"],
            "context": symbolic_item["context"], 
            "question": symbolic_item["question"],
            "options": symbolic_item["options"],
            "gold_answer": symbolic_item["answer"],  
            "symbolic_results": {
                "LP": symbolic_item["roles"].get("LP", {}),  
                "FOL": symbolic_item["roles"].get("FOL", {}), 
                "SAT": symbolic_item["roles"].get("SAT", {})
            },
            "llm_results": llm_item["roles"]  # COT Solver, Plan-and-Solve
        }
        
        merged_data.append(merged_item)
    
    print(f"Successfully loaded and matched {len(merged_data)} instances")
    if unmatched_ids:
        print(f"Unmatched IDs: {unmatched_ids}")
    
    return merged_data


def assign_agent_data(agentverse, merged_instance: Dict) -> None:
    """
    Assign predict and reasoning data to each agent based on solver results.
    
    Args:
        agentverse: AgentVerse instance
        merged_instance: Merged data instance with solver results
    """   
    # Agent mapping to solver results
    agent_mapping = {
        "LP supporter": ("symbolic", "LP"),
        "FOL supporter": ("symbolic", "FOL"), 
        "SAT supporter": ("symbolic", "SAT"),
        "COT Solver supporter": ("llm", "COT Solver"),
        "Plan-and-Solve supporter": ("llm", "Plan-and-Solve")
    }
    
    for agent in agentverse.agents:
        agent.context = merged_instance["context"]
        agent.question = merged_instance["question"]
        agent.options = '\n'.join(merged_instance["options"])
        agent.final_prompt = ""
        
        if agent.name in agent_mapping:
            result_type, solver_name = agent_mapping[agent.name]
            
            if result_type == "symbolic":
                solver_result = merged_instance["symbolic_results"].get(solver_name, {})
                agent.predict = solver_result.get("predict", "")
                agent.reasoning = solver_result.get("reasoning", "")
            else:  # llm
                solver_result = merged_instance["llm_results"].get(solver_name, {})
                agent.predict = solver_result.get("predict", "")
                agent.reasoning = solver_result.get("reasoning", "")
        else:
            print(f"Warning: No mapping found for agent: {agent.name}")




def extract_memory_token_usage(agents) -> Dict:
    """
    Extract ONLY memory token usage from agents.
    
    Args:
        agents: List of agent instances
        
    Returns:
        Dictionary with memory token usage statistics
    """
    total_memory_tokens = 0
    per_agent_memory = {}
    
    for agent in agents:
        if hasattr(agent, 'memory_token_usage'):
            agent_memory_tokens = agent.memory_token_usage.get("total_memory_tokens", 0)
            total_memory_tokens += agent_memory_tokens
            per_agent_memory[agent.name] = {
                "memory_tokens": agent_memory_tokens,
                "rounds": agent.memory_token_usage.get("rounds", [])
            }
    
    return {
        "total_memory_tokens_all_agents": total_memory_tokens,
        "average_memory_tokens_per_agent": total_memory_tokens / len(agents) if agents else 0,
        "per_agent": per_agent_memory
    }


def collect_final_predictions(agents) -> Dict:
    """
    Collect final predictions from all agents.
    Now uses the final_answer attribute directly from agents instead of re-parsing.
    
    Args:
        agents: List of agent instances
        
    Returns:
        Dictionary of final predictions by agent name
    """
    final_predictions = {}
    
    for agent in agents:
        # Use final_answer attribute directly from the agent (parsed by output_parser)
        final_answer = agent.final_answer if hasattr(agent, 'final_answer') else ""
        final_predictions[agent.name] = {
            "predict": final_answer
        }
    
    return final_predictions


def collect_original_predictions(agents) -> Dict:
    """
    Collect all agents' original predictions before debate.
    
    Args:
        agents: List of agent instances
        
    Returns:
        Dictionary of original predictions by agent name
    """
    original_predictions = {}
    
    for agent in agents:
        # Use agent.predict attribute (from solver results)
        original_predictions[agent.name] = {
            "predict": agent.predict
        }
    
    return original_predictions


def extract_gate_history(visibility_rule) -> Dict:
    """
    Extract gate matrices history from sparse visibility rule.
    
    Args:
        visibility_rule: The sparse visibility rule instance
        
    Returns:
        Dictionary with gate history and statistics
    """
    if not hasattr(visibility_rule, 'gates'):
        return {}
    
    gate_history = {}
    
    for round_num, gates in visibility_rule.gates.items():
        n_agents = gates.shape[0]
        # Convert numpy array to list for JSON serialization
        # Add 1 to round_num for human-readable display (Round 1, Round 2, etc.)
        gate_history[f"round_{round_num + 1}"] = {
            "gates": gates.tolist(),
            "open_gates": int(np.sum(gates) - n_agents),  # Exclude self-connections
            "total_gates": n_agents * (n_agents - 1),
            "sparsity": float(1 - (np.sum(gates) - n_agents) / (n_agents * (n_agents - 1)))
        }
    
    # Add cumulative sparse rate
    if hasattr(visibility_rule, 'get_cumulative_sparse_rate'):
        gate_history["cumulative_sparse_rate"] = visibility_rule.get_cumulative_sparse_rate()
        gate_history["cumulative_open_gates"] = visibility_rule.cumulative_open_gates
        gate_history["cumulative_total_gates"] = visibility_rule.cumulative_total_gates
    
    # Add confidence history if available
    if hasattr(visibility_rule, 'confidences'):
        confidence_history = {}
        for round_num, confidences in visibility_rule.confidences.items():
            # Add 1 to round_num for human-readable display
            confidence_history[f"round_{round_num + 1}"] = {
                f"agent_{i}": conf for i, conf in confidences.items()
            }
        gate_history["confidences"] = confidence_history
    
    return gate_history


def main():
    """Main execution function for sparse final debate"""
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, 
                       default="agentverse/tasks/final_debate/sparse_final_debate_config.yaml",
                       help="Path to sparse debate configuration file")
    parser.add_argument("--max_instances", type=int, default=0,
                       help="Maximum number of instances to process (0 for all)")
    parser.add_argument("--start_from", type=int, default=0,
                       help="Start processing from this instance index")
    args = parser.parse_args()
    
    print("=" * 50)
    print("Starting Sparse Communication Final Debate")
    print("=" * 50)
    
    # Load configuration
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize AgentVerse
    print("\n📋 Initializing AgentVerse with sparse communication...")
    agentverse, _, _ = AgentVerse.from_task(args.config)
    
    # Load and merge solver results
    print("📁 Loading and merging solver results...")
    merged_data = load_solver_results(
        config['symbolic_slover_results_path'],
        config['llm_solver_results_path']
    )
    
    # Determine instances to process
    end_idx = len(merged_data) if args.max_instances == 0 else min(args.start_from + args.max_instances, len(merged_data))
    instances_to_process = merged_data[args.start_from:end_idx]
    
    print(f"\n📊 Processing instances {args.start_from} to {end_idx-1} ({len(instances_to_process)} total)")
    
    # Prepare output
    sparse_debate_output = []
    output_dir = config['output_dir']
    
    # Process each instance
    for num, merged_instance in enumerate(tqdm(instances_to_process, desc="Processing instances", unit="instance")):
        actual_idx = args.start_from + num
        print(f"\n{'='*20} Instance {actual_idx} (ID: {merged_instance['id']}) {'='*20}")
        
        try:
            # Assign agent data from solver results
            assign_agent_data(agentverse, merged_instance)
            
            # Collect original predictions before debate
            original_predictions = collect_original_predictions(agentverse.agents)
            
            # Run sparse debate
            print("Running sparse debate...")
            agentverse.run()
            
            # Extract results
            chat_history = agentverse.environment.get_chat_history()  # Get centralized chat history
            final_predictions = collect_final_predictions(agentverse.agents)
            
            # Extract memory token usage
            memory_usage = extract_memory_token_usage(agentverse.agents)
            
            # Extract gate history from visibility rule
            gate_history = {}
            if hasattr(agentverse.environment.rule, 'visibility'):
                gate_history = extract_gate_history(agentverse.environment.rule.visibility)
            
            # Compile result
            result = {
                "id": merged_instance["id"],
                "context": merged_instance["context"],
                "question": merged_instance["question"],
                "options": merged_instance["options"],
                "chat_history": chat_history,
                "gold_answer": merged_instance["gold_answer"],
                "Original predictions": original_predictions,
                "Final predictions": final_predictions,
                "memory_token_usage": memory_usage,
                "gate_statistics": gate_history
            }
            
            sparse_debate_output.append(result)
            
            # Save intermediate results
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "sparse_final_debate_results.json"), "w", encoding='utf-8') as f:
                json.dump(sparse_debate_output, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Instance {actual_idx} completed")
            
        except Exception as e:
            print(f"❌ Error processing instance {actual_idx}: {e}")
            import traceback
            traceback.print_exc()
            
            # Add error result
            sparse_debate_output.append({
                "id": merged_instance.get("id", f"instance_{actual_idx}"),
                "error": str(e)
            })
        
        finally:
            # Reset agents for next instance
            for agent in agentverse.agents:
                agent.reset()
            # Reset visibility rule
            if hasattr(agentverse.environment.rule, 'visibility'):
                agentverse.environment.rule.visibility.reset()
    
    # Final summary
    print("\n" + "=" * 50)
    print("SPARSE FINAL DEBATE SUMMARY")
    print("=" * 50)
    print(f"Total instances processed: {len(sparse_debate_output)}")
    print(f"Results saved to: {os.path.join(output_dir, 'sparse_final_debate_results.json')}")
    
    # Calculate average sparsity and memory token usage
    total_sparsity = []
    cumulative_sparse_rates = []
    total_memory_tokens = 0
    
    for result in sparse_debate_output:
        # Collect sparsity data
        if "gate_statistics" in result:
            # Collect per-round sparsity
            for round_key, round_stats in result["gate_statistics"].items():
                if round_key.startswith("round_") and "sparsity" in round_stats:
                    total_sparsity.append(round_stats["sparsity"])
            
            # Collect cumulative sparse rate
            if "cumulative_sparse_rate" in result["gate_statistics"]:
                cumulative_sparse_rates.append(result["gate_statistics"]["cumulative_sparse_rate"])
        
        # Collect memory token usage
        if "memory_token_usage" in result:
            total_memory_tokens += result["memory_token_usage"].get("total_memory_tokens_all_agents", 0)
    
    if total_sparsity:
        avg_sparsity = np.mean(total_sparsity)
        print(f"Average per-round sparsity: {avg_sparsity:.2%}")
    
    if cumulative_sparse_rates:
        avg_cumulative_sparse_rate = np.mean(cumulative_sparse_rates)
        print(f"Average cumulative sparse rate per question: {avg_cumulative_sparse_rate:.2%}")
    
    if total_memory_tokens > 0:
        avg_memory_per_question = total_memory_tokens / len(sparse_debate_output)
        print(f"Total memory tokens: {total_memory_tokens:,}")
        print(f"Average memory tokens per question: {avg_memory_per_question:,.0f}")
    
    print("\n✅ Sparse final debate completed successfully!")
    print(f"You can now run evaluation using:")
    print(f"python run_evaluation.py --input_path {os.path.join(output_dir, 'sparse_final_debate_results.json')} --aggregation_strategy majority_vote")


if __name__ == "__main__":
    main()