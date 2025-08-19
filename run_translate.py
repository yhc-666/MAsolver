import os


import json
from tqdm import tqdm
from eval_helper.get_evaluation import get_evaluation
from translation_output_helper.get_translation_output import get_translation_output

from agentverse.agentverse import AgentVerse
from argparse import ArgumentParser
from typing import Dict, List


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


parser = ArgumentParser()

parser.add_argument("--config", type=str, default="agentverse/tasks/nl_sl_translation/translate_config.yaml")
parser.add_argument("--reverse_input", default=False, action="store_true")


args = parser.parse_args()

agentverse, args_data_path, args_output_dir = AgentVerse.from_task(args.config)

print(args)

os.makedirs(args_output_dir, exist_ok=True)
with open(os.path.join(args_output_dir, "args.txt"), "w") as f:
    f.writelines(str(args))

# uncomment this line if you don't want to overwrite your output_dir
# if os.path.exists(args_output_dir) and len(os.listdir(args_output_dir)) > 1 :
#
#     raise ValueError("the output_dir is not empty, check if is expected.")

with open(args_data_path) as f:
    data = json.load(f)

if "ruozhiba" in args_data_path:
    pair_comparison_output = []

    for num, ins in enumerate(tqdm(data, desc="Processing ruozhiba", unit="instance")):

        print(f"================================instance {num}====================================")

        # reassign the text to agents, and set final_prompt to null for debate at first round
        for agent_id in range(len(agentverse.agents)):
            agentverse.agents[agent_id].question = ins["instruction"]

            # if args.reverse_input:
            #     agentverse.agents[agent_id].compared_text_one = ins["response"]["vicuna"]
            #     agentverse.agents[agent_id].compared_text_two = ins["response"]["gpt35"]
            # else:
            #     agentverse.agents[agent_id].compared_text_one = ins["response"]["gpt35"]
            #     agentverse.agents[agent_id].compared_text_two = ins["response"]["vicuna"]

            agentverse.agents[agent_id].final_prompt = ""
        agentverse.run()

        evaluation = get_evaluation(setting="every_agent", messages=agentverse.agents[0].memory.messages, agent_nums=len(agentverse.agents))

        pair_comparison_output.append({"question": ins["instruction"],
                                       "evaluation": evaluation})

        os.makedirs(args_output_dir, exist_ok=True)
        with open(os.path.join(args_output_dir, "pair_comparison_results.json"), "w") as f:
            json.dump(pair_comparison_output, f, indent=4)
    # with open(os.path.join(args_output_dir, "gt_origin_results.json"), "w") as f:
    #     json.dump(gt_origin_output, f, indent=4)

elif "ProofWriter" in args_data_path:
    # 处理ProofWriter数据集
    proof_writer_output = []

    for num, ins in enumerate(tqdm(data[:30], desc="Processing ProofWriter", unit="instance")):
        print(f"================================instance {num}====================================")

        for agent_id in range(len(agentverse.agents)):
            agentverse.agents[agent_id].context = ins["context"]  # 赋值prompt template中的${context}字段
            agentverse.agents[agent_id].question = ins["question"].strip()  # 赋值prompt template中的${question}字段
            agentverse.agents[agent_id].final_prompt = ""

        agentverse.run()

        # Get chat history from environment's centralized logging
        chat_history = agentverse.environment.get_chat_history()
        # Get translations using the existing helper (only for translation-specific logic)
        _, translations = get_translation_output(setting="every_agent", messages=agentverse.agents[0].memory.messages,
                                    agent_nums=len(agentverse.agents))
        
        # Extract memory token usage
        memory_usage = extract_memory_token_usage(agentverse.agents)

        proof_writer_output.append({
            "id": ins["id"],
            "context": ins["context"],
            "question": ins["question"],
            "options": ins["options"],
            "answer": ins["answer"],
            "chat_history": chat_history,
            "translation": translations,
            "memory_token_usage": memory_usage
        })
        
        # Reset agents for next instance
        for agent in agentverse.agents:
            agent.reset()

        os.makedirs(args_output_dir, exist_ok=True)
        with open(os.path.join(args_output_dir, "translation_results.json"), "w") as f:
            json.dump(proof_writer_output, f, indent=4)

elif "FOLIO" in args_data_path:
# 处理ProofWriter数据集
    smoketest_output = []

    for num, ins in enumerate(tqdm(data, desc="Processing FOLIO", unit="instance")):
        print(f"================================instance {num}====================================")

        for agent_id in range(len(agentverse.agents)):
            agentverse.agents[agent_id].context = ins["context"]  # 赋值prompt template中的${context}字段
            agentverse.agents[agent_id].question = ins["question"].strip()  # 赋值prompt template中的${question}字段
            agentverse.agents[agent_id].final_prompt = ""

        agentverse.run()

        # Get chat history from environment's centralized logging
        chat_history = agentverse.environment.get_chat_history()
        # Get translations using the existing helper (only for translation-specific logic)
        _, translations = get_translation_output(setting="every_agent", messages=agentverse.agents[0].memory.messages,
                                    agent_nums=len(agentverse.agents))
        
        # Extract memory token usage
        memory_usage = extract_memory_token_usage(agentverse.agents)

        smoketest_output.append({
            "id": ins["id"],
            "context": ins["context"],
            "question": ins["question"],
            "options": ins["options"],
            "answer": ins["answer"],
            "chat_history": chat_history,
            "translation": translations,
            "memory_token_usage": memory_usage
        })
        
        # Reset agents for next instance
        for agent in agentverse.agents:
            agent.reset()

        os.makedirs(args_output_dir, exist_ok=True)
        with open(os.path.join(args_output_dir, "translation_results.json"), "w") as f:
            json.dump(smoketest_output, f, indent=4)

elif "LogicalDeduction" in args_data_path:
    # 处理LogicalDeduction数据集
    logical_deduction_output = []

    for num, ins in enumerate(tqdm(data, desc="Processing LogicalDeduction", unit="instance")):
        print(f"================================instance {num}====================================")

        # 将options数组转换为格式化的字符串
        options_str = "\n".join(ins["options"])

        for agent_id in range(len(agentverse.agents)):
            agentverse.agents[agent_id].context = ins["context"]  # 赋值prompt template中的${context}字段
            agentverse.agents[agent_id].question = ins["question"].strip()  # 赋值prompt template中的${question}字段
            agentverse.agents[agent_id].options = options_str  # 赋值prompt template中的${options}字段
            agentverse.agents[agent_id].final_prompt = ""

        agentverse.run()

        # Get chat history from environment's centralized logging
        chat_history = agentverse.environment.get_chat_history()
        # Get translations using the existing helper (only for translation-specific logic)
        _, translations = get_translation_output(setting="every_agent", messages=agentverse.agents[0].memory.messages,
                                    agent_nums=len(agentverse.agents))
        
        # Extract memory token usage
        memory_usage = extract_memory_token_usage(agentverse.agents)

        logical_deduction_output.append({
            "id": ins["id"],
            "context": ins["context"],
            "question": ins["question"],
            "options": ins["options"],
            "answer": ins["answer"],
            "chat_history": chat_history,
            "translation": translations,
            "memory_token_usage": memory_usage
        })
        
        # Reset agents for next instance
        for agent in agentverse.agents:
            agent.reset()

        os.makedirs(args_output_dir, exist_ok=True)
        with open(os.path.join(args_output_dir, "translation_results.json"), "w") as f:
            json.dump(logical_deduction_output, f, indent=4)

else:
    raise ValueError(f"Unsupported dataset in run_translate.py: {args_data_path}")

    