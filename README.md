# Multi-Agent Debate System

A multi-agent debate system built on the AgentVerse framework, designed to facilitate structured debates between AI agents with different roles and perspectives.

## Overview

This system enables multiple AI agents to engage in structured debates on various topics. The agents are assigned different roles and personas, allowing them to present diverse viewpoints and engage in meaningful discussions. The system is particularly useful for exploring complex questions and analyzing problems from multiple angles.

## Features

- **Multi-Agent Architecture**: Built on the AgentVerse framework for scalable agent management
- **Flexible LLM Support**: Compatible with both API-based LLMs (DeepSeek, OpenAI) and local models
- **Role-Based Debates**: Agents with distinct personas and debate strategies
- **Configurable Debate Rules**: Customizable turn limits, communication patterns, and evaluation criteria
- **Multiple Data Formats**: TODO
- **Comprehensive Logging**: TODO

## Quick Start

### Prerequisites

- Python 3.8+
- Required packages listed in `requirements.txt`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API credentials (if using API mode):
```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_BASE_URL="your_api_base_url"
```

### Basic Usage

Run a debate session with the default configuration:

```bash
python llm_eval.py --config agentverse/tasks/llm_eval/lxconfig.yaml
```

## 📁 Project Structure

```
├── llm_eval.py                    # Main entry point
├── requirements.txt               
├── agentverse/                    # AgentVerse framework
│   ├── agents/                    # Agent implementations
│   ├── environments/              # Environment configurations
│   ├── llms/                      # LLM integrations
│   ├── memory/                    
│   └── tasks/                     # Task definitions
│       └── llm_eval/              # LLM evaluation tasks
│           ├── lxconfig.yaml      # Main configuration file
│           └── data/              # Dataset storage
├── eval_helper/                   # Evaluation utilities
│   └── get_evaluation.py          # Evaluation logic
└── outputs/                       # Generated results
```

## ⚙️ Configuration

The system is configured through YAML files. The main configuration file is located at `agentverse/tasks/llm_eval/lxconfig.yaml`.

### Key Configuration Sections

#### 1. Task Configuration
```yaml
task: llmeval
data_path: ./agentverse/tasks/llm_eval/data/faireval/preprocessed_data/ruozhiba_qa2449_gpt4o.json
output_dir: ./outputs/llm_eval/multi_role/...
```

#### 2. LLM Configuration
Choose between API or local LLM deployment:

**API Mode:**
```yaml
llm_config:
  mode: 'api'
  api_settings:
    model: "deepseek-chat"
    llm_type: "deepseek-chat"
    temperature: 0
    max_tokens: 512
```

**Local Mode:**
```yaml
llm_config:
  mode: 'local'
  local_settings:
    model_path: "/path/to/your/model"
    llm_type: "deepseek-local"
    temperature: 0.7
    max_tokens: 5120
    tensor_parallel_size: 1
    gpu_memory_utilization: 0.9
```

#### 3. Environment Settings
```yaml
environment:
  env_type: llm_eval
  max_turns: 8
  rule:
    order:
      type: sequential
    visibility:
      type: all
```

#### 4. Agent Configuration
Define agents with distinct roles and personas:

```yaml
agents:
  - agent_type: llm_eval_multi
    name: Agent1
    role_description: "Your agent's persona and behavior description"
    final_prompt_to_use: "Instructions for the final response"
    memory:
      memory_type: chat_history
```

## 📊 Data Format

### Input Data Structure

The system supports multiple data formats:

**FairEval Format:**
```json
[
  {
    "instruction": "Your question or topic for debate",
    "response": {
      "model1": "Response from model 1",
      "model2": "Response from model 2"
    }
  }
]
```


### Output Results

Results are saved in JSON format with detailed debate logs and evaluations:

```json
[
  {
    "question": "Debate topic",
    "evaluation": [
      {
        "agent": "Agent Name",
        "response": "Agent's final evaluation and reasoning"
      }
    ]
  }
]
```

## Advanced Usage

### Custom Agent Roles

### Running with Different Configurations

```bash
# Use a specific configuration file
python llm_eval.py --config path/to/your/config.yaml

# Reverse input order for comparison studies
python llm_eval.py --config agentverse/tasks/llm_eval/lxconfig.yaml --reverse_input
```

### Local LLM Setup

For detailed instructions on setting up local LLMs, refer to `LOCAL_LLM_USAGE.md`.


## For Coding agent

Use data stored at `agentverse/tasks/llm_eval/data/faireval/preprocessed_data/ruozhiba_qa2449_gpt4o.json` and run `llm_eval.py` for testing.

