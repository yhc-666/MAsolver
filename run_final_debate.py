import os
import json
import yaml
from argparse import ArgumentParser
from typing import Dict, List
from tqdm import tqdm


from agentverse.agentverse import AgentVerse


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
        final_answer = agent.final_answer
        final_predictions[agent.name] = {
            "predict": final_answer
        }
    
    return final_predictions


def collect_original_predictions(agents) -> Dict:
    """
    收集所有agent在辩论前的原始预测
    
    Args:
        agents: List of agent instances
        
    Returns:
        Dictionary of original predictions by agent name
    """
    original_predictions = {}
    
    for agent in agents:
        # 使用agent.predict属性（来自solver results）
        original_predictions[agent.name] = {
            "predict": agent.predict
        }
    
    return original_predictions


# extract_answer_from_content function removed - now using agent.final_answer directly


def main():
    """Main execution function"""
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, 
                       default="agentverse/tasks/final_debate/final_debate_config.yaml")
    parser.add_argument("--max_instances", type=int, default=0, help="Maximum number of instances to process (0 for all)")
    args = parser.parse_args()
    
    print("Starting Final Debate Stage")
    print("=" * 50)
    
    # Load configuration
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize AgentVerse
    agentverse, _, _ = AgentVerse.from_task(args.config)
    
    # Load and merge solver results
    print("📁 Loading and merging solver results...")
    merged_data = load_solver_results(
        config['symbolic_slover_results_path'],
        config['llm_solver_results_path']
    )
    
    # Prepare output
    final_debate_output = []
    output_dir = config['output_dir']
    
    # Determine how many instances to process
    instances_to_process = merged_data if args.max_instances == 0 else merged_data[:args.max_instances]

    
    # Process each instance
    for num, merged_instance in enumerate(tqdm(instances_to_process, desc="Processing instances", unit="instance")):
        print(f"\n{'='*20} Instance {num} (ID: {merged_instance['id']}) {'='*20}")
        
        # Assign agent data
        assign_agent_data(agentverse, merged_instance)
        
        # Collect original predictions before debate
        original_predictions = collect_original_predictions(agentverse.agents)
        
        # Run debate
        agentverse.run()
        
        # Get chat history from environment's centralized logging
        chat_history = agentverse.environment.get_chat_history()
        final_predictions = collect_final_predictions(agentverse.agents)
        
        # Extract memory token usage
        memory_usage = extract_memory_token_usage(agentverse.agents)
        
        result = {
            "id": merged_instance["id"],
            "context": merged_instance["context"],
            "question": merged_instance["question"],
            "options": merged_instance["options"],
            "chat_history": chat_history,
            "gold_answer": merged_instance["gold_answer"],
            "Original predictions": original_predictions,
            "Final predictions": final_predictions,
            "memory_token_usage": memory_usage
        }
        
        final_debate_output.append(result)
        
        # Save intermediate results
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "final_debate_results.json"), "w", encoding='utf-8') as f:
            json.dump(final_debate_output, f, indent=2, ensure_ascii=False)
        
        # Reset agents for next instance
        for agent in agentverse.agents:
            agent.reset()


if __name__ == "__main__":
    main()
