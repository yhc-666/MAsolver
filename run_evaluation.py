import json
import os
import argparse
from tqdm import tqdm
import re
from collections import Counter, defaultdict
import numpy as np

def normalize_answer(answer):
    """
    Normalize answer format to handle variations like 'A) True' vs 'A'
    """
    if not answer:
        return ""
    
    # Convert to string and strip whitespace
    answer = str(answer).strip()
    
    # Extract the option letter (A, B, C, etc.)
    match = re.match(r'^([A-Z])', answer.upper())
    if match:
        return match.group(1)
    
    # If no letter found, return the original answer in uppercase
    return answer.upper()


def get_last_speaker(chat_history):
    """
    Get the role of the last speaker from chat history
    """
    if not chat_history:
        return None
    
    # Find the last message that contains actual content (not just answer tags)
    for message in reversed(chat_history):
        if message.get('content') and not message['content'].startswith('<answer>'):
            return message['role']
    
    # If all messages are answer tags, return the last one
    return chat_history[-1]['role']


def get_majority_vote_prediction(final_predictions):
    """
    Get prediction using majority vote from all supporters
    """
    if not final_predictions:
        return None, {}
    
    # Collect all valid predictions
    predictions = []
    for role, prediction_data in final_predictions.items():
        if isinstance(prediction_data, dict) and 'predict' in prediction_data:
            predict = prediction_data['predict']
            normalized_predict = normalize_answer(predict)
            if normalized_predict:
                predictions.append(normalized_predict)
    
    if not predictions:
        return None, {}
    
    # Count votes
    vote_counts = Counter(predictions)
    
    # Get the majority vote (most common answer)
    most_common = vote_counts.most_common(1)
    majority_answer = most_common[0][0] if most_common else None
    
    # Create stats dictionary
    stats = {
        'total_voters': len(predictions),
        'vote_counts': dict(vote_counts),
        'majority_answer': majority_answer,
        'majority_count': most_common[0][1] if most_common else 0
    }
    
    return majority_answer, stats


def extract_sparse_statistics(item):
    """
    Extract sparse communication statistics from a question item.
    
    Args:
        item: Question item from the JSON data
        
    Returns:
        dict: Dictionary containing sparse statistics or None if not sparse communication
    """
    gate_stats = item.get('gate_statistics', {})
    memory_usage = item.get('memory_token_usage', {})
    
    if not gate_stats:
        return None
    
    # Calculate total closed/open gates for question-level sparsity
    total_closed = 0
    total_gates_count = 0
    round_sparsity_data = {}
    
    # Process gate statistics by round (rounds 1-6 only, exclude round 7)
    for key, round_info in gate_stats.items():
        if key.startswith('round_') and isinstance(round_info, dict):
            round_num = int(key.split('_')[1])
            # Skip round 7 as it has no corresponding debate round
            if round_num > 6:
                continue
                
            sparsity = round_info.get('sparsity', 0.0)
            open_gates = round_info.get('open_gates', 0)
            total_gates = round_info.get('total_gates', 0)
            
            total_closed += (total_gates - open_gates)
            total_gates_count += total_gates
            round_sparsity_data[round_num] = sparsity
    
    # Calculate question-level sparsity
    question_sparsity = total_closed / total_gates_count if total_gates_count > 0 else 0.0
    
    # Extract per-round memory tokens (starting from round 0)
    round_memory_data = {}
    per_agent = memory_usage.get('per_agent', {})
    
    if per_agent:
        # Get all rounds from any agent
        max_rounds = 0
        for agent_data in per_agent.values():
            rounds = agent_data.get('rounds', [])
            max_rounds = max(max_rounds, len(rounds))
        
        # Sum memory tokens across agents for each round
        for round_idx in range(max_rounds):
            round_total = 0
            for agent_data in per_agent.values():
                rounds = agent_data.get('rounds', [])
                if round_idx < len(rounds):
                    round_total += rounds[round_idx].get('memory_tokens', 0)
            round_memory_data[round_idx] = round_total
    
    # Add round 0 sparsity (always 0.0 - no gates closed initially)
    if 0 not in round_sparsity_data:
        round_sparsity_data[0] = 0.0
    
    return {
        'question_sparsity': question_sparsity,
        'sparsity_per_round': round_sparsity_data,
        'memory_per_round': round_memory_data,
        'total_memory_tokens': memory_usage.get('total_memory_tokens_all_agents', 0),
        'num_rounds': len(round_memory_data)
    }


def get_aggregated_prediction(item, strategy):
    """
    Get aggregated prediction based on strategy
    """
    final_predictions = item.get('Final predictions', {})
    
    if strategy == 'last_speaker':
        # Get the last speaker from chat history
        chat_history = item.get('chat_history', [])
        last_speaker = get_last_speaker(chat_history)
        
        if not last_speaker:
            return None, {'error': 'No valid speaker found'}
        
        if last_speaker not in final_predictions:
            return None, {'error': f'No prediction found for speaker {last_speaker}'}
        
        predicted_answer = final_predictions[last_speaker].get('predict', '')
        normalized_predicted = normalize_answer(predicted_answer)
        
        return normalized_predicted, {'strategy': 'last_speaker', 'speaker': last_speaker}
    
    elif strategy == 'majority_vote':
        predicted_answer, stats = get_majority_vote_prediction(final_predictions)
        stats['strategy'] = 'majority_vote'
        return predicted_answer, stats
    
    else:
        return None, {'error': f'Unknown strategy: {strategy}'}


def evaluate_final_debate(json_path, aggregation_strategy='last_speaker'):
    """
    Evaluate the final debate results and calculate accuracy
    """
    # Check if file exists
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        return None
    
    # Read JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    correct_count = 0
    total_count = len(data)
    error_count = 0
    tie_count = 0  # For majority vote ties
    
    # Analytics data collection
    sparse_questions = []
    round_sparsity_data = defaultdict(list)  # round_num -> [sparsity_values]
    round_memory_data = defaultdict(list)     # round_num -> [memory_tokens]
    memory_tokens_data = []  # Memory tokens for all questions (sparse and non-sparse)
    
    print(f"Starting evaluation of {total_count} questions using '{aggregation_strategy}' strategy...")
    
    for item in tqdm(data, desc="Evaluating"):
        try:
            # Get gold answer
            gold_answer = item.get('gold_answer', '')
            normalized_gold = normalize_answer(gold_answer)
            
            # Always collect memory token data if available
            memory_usage = item.get('memory_token_usage', {})
            total_memory_tokens = memory_usage.get('total_memory_tokens_all_agents', 0)
            if total_memory_tokens > 0:
                memory_tokens_data.append(total_memory_tokens)
            
            # Collect per-round memory data for all questions
            per_agent = memory_usage.get('per_agent', {})
            if per_agent:
                # Sum across agents for each round
                agent_rounds = {}
                for agent_data in per_agent.values():
                    for round_info in agent_data.get('rounds', []):
                        round_num = round_info['round']
                        if round_num not in agent_rounds:
                            agent_rounds[round_num] = 0
                        agent_rounds[round_num] += round_info['memory_tokens']
                
                for round_num, total in agent_rounds.items():
                    round_memory_data[round_num].append(total)
            
            # Extract sparse statistics if available
            sparse_stats = extract_sparse_statistics(item)
            if sparse_stats:
                sparse_questions.append(sparse_stats)
                
                # Collect round-by-round sparsity data for convergence analysis
                for round_num, sparsity in sparse_stats['sparsity_per_round'].items():
                    round_sparsity_data[round_num].append(sparsity)
            
            # Get aggregated prediction
            predicted_answer, stats = get_aggregated_prediction(item, aggregation_strategy)
            
            if predicted_answer is None:
                if 'error' in stats:
                    print(f"Warning: {stats['error']} for question {item.get('id', 'unknown')}")
                error_count += 1
                continue
            
            # Track ties for majority vote
            if aggregation_strategy == 'majority_vote' and 'majority_count' in stats:
                total_voters = int(stats.get('total_voters', 0))
                majority_count = int(stats.get('majority_count', 0))
                if total_voters > 1 and majority_count <= total_voters // 2:
                    tie_count += 1
            
            # Check if answers match
            if normalized_gold == predicted_answer:
                correct_count += 1
            
        except Exception as e:
            print(f"Error processing question {item.get('id', 'unknown')}: {e}")
            error_count += 1
    
    # Calculate accuracy
    valid_questions = total_count - error_count
    if valid_questions == 0:
        print("Error: No valid questions found")
        return None
    
    accuracy = correct_count / valid_questions
    
    # Calculate communication statistics
    using_sparse = len(sparse_questions) > 0
    has_memory_data = len(memory_tokens_data) > 0
    
    print(f"\n{'='*50}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*50}")
    print(f"Aggregation strategy: {aggregation_strategy}")
    print(f"Total questions: {total_count}")
    print(f"Valid questions: {valid_questions}")
    print(f"Correct answers: {correct_count}")
    print(f"Errors encountered: {error_count}")
    if aggregation_strategy == 'majority_vote' and tie_count > 0:
        print(f"Tie cases (no clear majority): {tie_count}")
    print(f"Overall accuracy: {accuracy:.2%}")
    
    # Memory usage analytics for all debate types
    if has_memory_data:
        print(f"\n{'='*50}")
        print(f"MEMORY USAGE ANALYTICS")
        print(f"{'='*50}")
        
        # Average prefilling memory tokens per round
        if round_memory_data:
            print(f"\nAverage prefilling memory tokens per round:")
            for round_num in sorted(round_memory_data.keys()):
                avg_tokens = np.mean(round_memory_data[round_num])
                print(f"  Round {round_num}: {avg_tokens:.0f} tokens")
        
        # Average total memory tokens per question
        avg_memory_tokens = np.mean(memory_tokens_data)
        print(f"\nAverage total memory tokens per question: {avg_memory_tokens:.0f}")
        print(f"Memory tokens std deviation: {np.std(memory_tokens_data):.0f}")
        print(f"Memory tokens range: [{min(memory_tokens_data)}, {max(memory_tokens_data)}]")
    
    # Sparse communication specific analytics
    if using_sparse:
        print(f"\n{'='*50}")
        print(f"SPARSE COMMUNICATION ANALYTICS")
        print(f"{'='*50}")
        
        # Average sparsity per question (using correct calculation)
        question_sparsities = [q['question_sparsity'] for q in sparse_questions]
        avg_sparsity = np.mean(question_sparsities)
        
        print(f"\nAverage sparsity per question: {avg_sparsity:.3f}")
        print(f"Sparsity std deviation: {np.std(question_sparsities):.3f}")
        print(f"Sparsity range: [{min(question_sparsities):.3f}, {max(question_sparsities):.3f}]")
        
        # Average sparse rate per round
        print(f"\nAverage sparse rate per round:")
        sorted_rounds = sorted(round_sparsity_data.keys())
        # Filter out rounds that don't have corresponding memory data
        max_memory_round = max(round_memory_data.keys()) if round_memory_data else 6
        for round_num in sorted_rounds:
            if round_num <= max_memory_round:  # Only show rounds with actual debate
                round_sparsities = round_sparsity_data[round_num]
                avg_round_sparsity = np.mean(round_sparsities)
                print(f"  Round {round_num}: {avg_round_sparsity:.3f}")
    
    print(f"{'='*50}")
    
    return accuracy


def main():
    parser = argparse.ArgumentParser(description='Evaluate final debate results')
    parser.add_argument(
        '--input_path', 
        type=str,
        default='outputs/deepseek/ProofWriter/final_debate/final_debate_results.json',
        help='Path to the final debate results JSON file'
    )
    parser.add_argument(
        '--aggregation_strategy',
        type=str,
        choices=['last_speaker', 'majority_vote'],
        default='majority_vote',
        help='Strategy for aggregating predictions: last_speaker (default) or majority_vote'
    )
    
    args = parser.parse_args()
    
    accuracy = evaluate_final_debate(args.input_path, args.aggregation_strategy)
    
    if accuracy is not None:
        print(f"\nEvaluation completed successfully!")
    else:
        print(f"\nEvaluation failed!")
        exit(1)

if __name__ == "__main__":
    main()
