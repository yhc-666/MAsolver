# 本地LLM支持使用说明

## 概述

本系统现已支持本地LLM推理，通过vLLM引擎实现高效的本地模型推理。您可以在API调用和本地LLM之间自由切换。

## 功能特点

- ✅ **支持多种本地模型**：Deepseek、Qwen、ChatGLM、Llama等
- ✅ **自动chat template适配**：利用模型自带的chat_template将OpenAI格式messages转换为模型期望的格式
- ✅ **Think token过滤**：自动过滤模型输出中的思考标记（如`<think>...</think>`）
- ✅ **共享模型实例**：多个agent共享同一个模型实例，节省GPU内存
- ✅ **灵活配置**：支持temperature、top_p、top_k、max_tokens等参数配置

## 安装依赖

确保安装了以下依赖包：

```bash
pip install vllm transformers torch
```

## 配置文件

### 统一配置文件（推荐）

现在支持在一个配置文件中切换API和本地LLM模式：

```yaml
# agentverse/tasks/llm_eval/lxconfig.yaml

# LLM Configuration - 选择使用API还是本地LLM
llm_config:
  # 模式选择: 'api' 使用API调用, 'local' 使用本地LLM
  mode: 'local'  # 可选: 'api' 或 'local'
  
  # API模式配置
  api_settings:
    model: "deepseek-chat"
    llm_type: "deepseek-chat"
    temperature: 0
    max_tokens: 512
    
  # 本地LLM模式配置  
  local_settings:
    model_path: "/mnt/sdb/ssuser/llm_models/Deepseek-14B"
    llm_type: "deepseek-local"
    temperature: 0.7
    top_p: 0.9
    top_k: 50
    max_tokens: 512
    tensor_parallel_size: 1
    gpu_memory_utilization: 0.9
    max_model_len: 4096
    trust_remote_code: true

# agents配置会自动使用上面llm_config中选择的模式
agents:
  -
    agent_type: llm_eval_multi
    name: 弱智
    # ... 其他配置 ...
    # llm配置会被自动替换
```

### 旧版配置文件（兼容）

如果您希望继续使用旧版配置格式，也完全支持：

```yaml
# 本地LLM配置示例
agents:
  -
    agent_type: llm_eval_multi
    name: 弱智
    llm:
      model_path: "/mnt/sdb/ssuser/llm_models/Deepseek-14B"
      llm_type: "deepseek-local"
      temperature: 0.7
      # ... 其他参数

# API配置示例  
agents:
  -
    agent_type: llm_eval_multi
    name: 弱智
    llm:
      model: "deepseek-chat"
      llm_type: "deepseek-chat"
      temperature: 0
```

## 支持的模型类型

| 模型类型 | llm_type | 默认模型路径 |
|----------|----------|-------------|
| Deepseek | `deepseek-local` | `/mnt/sdb/ssuser/llm_models/Deepseek-14B` |
| Qwen | `qwen-local` | `/mnt/sdb/ssuser/llm_models/Qwen-14B` |
| ChatGLM | `chatglm-local` | `/mnt/sdb/ssuser/llm_models/ChatGLM-6B` |
| Llama | `llama-local` | `/mnt/sdb/ssuser/llm_models/Llama-2-7b-chat-hf` |

## 使用方法

### 1. 使用新的统一配置文件（推荐）

```bash
# 使用lxconfig.yaml，默认为本地LLM模式
python llm_eval.py --config agentverse/tasks/llm_eval/lxconfig.yaml
```

### 2. 切换API/本地LLM模式

只需修改`lxconfig.yaml`中的`mode`参数：

```yaml
# 使用本地LLM
llm_config:
  mode: 'local'

# 使用API
llm_config:
  mode: 'api'
```

### 3. 使用传统配置文件

仍然支持使用原始的config.yaml：

```bash
# 使用config.yaml（本地LLM模式）
python llm_eval.py --config agentverse/tasks/llm_eval/config.yaml

# 使用config_original.yaml（API模式）
python llm_eval.py --config agentverse/tasks/llm_eval/config_original.yaml
```

## 配置参数说明

### 模型配置参数

- `model_path`: 本地模型路径
- `llm_type`: 模型类型，决定使用哪个模型类
- `temperature`: 控制生成的随机性，0-1之间
- `top_p`: 核采样参数，0-1之间
- `top_k`: 选择前k个最可能的tokens
- `max_tokens`: 最大生成token数量
- `tensor_parallel_size`: 张量并行大小（用于多GPU推理）
- `gpu_memory_utilization`: GPU内存利用率，0-1之间
- `max_model_len`: 模型支持的最大序列长度
- `trust_remote_code`: 是否信任远程代码

### 性能优化建议

1. **GPU内存**：根据GPU内存调整`gpu_memory_utilization`参数
2. **序列长度**：根据需要设置`max_model_len`，较短的长度可以节省内存
3. **并行推理**：如果有多个GPU，可以设置`tensor_parallel_size > 1`

## 特殊功能

### Think Token过滤

系统会自动过滤以下think token模式：
- `<think>...</think>`
- `<thinking>...</thinking>`
- `[think]...[/think]`
- `[thinking]...[/thinking]`

### 共享模型实例

多个agent使用相同的模型配置时，会自动共享同一个vLLM实例，节省GPU内存。

## 故障排除

### 常见问题

1. **GPU内存不足**：
   - 降低`gpu_memory_utilization`参数
   - 减少`max_model_len`参数
   - 使用更小的模型

2. **模型加载失败**：
   - 检查模型路径是否正确
   - 确认模型文件完整性
   - 检查是否有足够的磁盘空间

3. **依赖包问题**：
   - 确认vllm、transformers、torch等包已正确安装
   - 检查CUDA版本兼容性

### 日志查看

系统会输出详细的日志信息，包括：
- 模型加载进度
- GPU内存使用情况
- 推理性能统计
- 错误信息

## 扩展支持

### 添加新模型

要添加新的本地模型支持，请：

1. 在`agentverse/llms/local_llm.py`中添加新的模型类：

```python
@llm_registry.register("your-model-local")
class YourModelLocalLLM(BaseLocalLLM):
    def __init__(self, max_retry: int = 3, **kwargs):
        if 'model_path' not in kwargs:
            kwargs['model_path'] = "/path/to/your/model"
        super().__init__(max_retry=max_retry, **kwargs)
```

2. 在`agentverse/llms/__init__.py`中添加导入：

```python
from .local_llm import YourModelLocalLLM
```

3. 在配置文件中使用新的模型类型：

```yaml
llm:
  llm_type: "your-model-local"
  model_path: "/path/to/your/model"
```

## 测试验证

成功运行后，您应该能看到：

1. 模型加载日志
2. agents之间的对话
3. 输出文件生成在指定目录

示例成功输出：
```
================================instance 0====================================
弱智: [agent的回复内容]
*****************************
天才: [agent的回复内容]
*****************************
```

## 注意事项

1. 首次运行时模型加载可能需要较长时间
2. 确保有足够的GPU内存
3. 不同模型的chat template可能不同，系统会自动处理
4. 建议在生产环境中先进行充分测试 