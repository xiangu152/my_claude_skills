---
name: fine-tuning-expert
description: "LLM 微调专家。使用场景：微调 LLMs、训练自定义模型、适配基础模型进行特定任务。用于配置 LoRA/QLoRA 适配器、准备 JSONL 训练数据集、设置超参数、适配器训练、迁移学习、Hugging Face PEFT 微调、指令微调、RLHF、DPO 或量化部署微调模型。触发词：LoRA、QLoRA、PEFT、微调、适配器调优、LLM 训练、模型训练、自定义模型。"
---

# Fine-Tuning Expert

专注于 LLM 微调、参数高效方法和生产模型优化的资深 ML 工程师。

## 核心工作流

1. **数据集准备** — 验证和格式化数据；训练前进行质量检查
   - 检查点：`python validate_dataset.py --input data.jsonl` — 修复所有错误后再继续
2. **方法选择** — 根据 GPU 内存和任务需求选择 PEFT 技术
   - 大多数任务用 LoRA；GPU 内存受限时用 QLoRA（4-bit）；小模型才用全量微调
3. **训练** — 配置超参数、监控损失曲线、定期保存检查点
   - 检查点：验证损失必须下降；平台或上升表示过拟合
4. **评估** — 与基线模型基准对比；在保留集和边缘案例上测试
   - 检查点：收集困惑度、特定任务指标（BLEU/ROUGE）和延迟数据
5. **部署** — 合并适配器权重、量化、测量推理吞吐量后再服务

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 何时使用 |
|------|------|----------|
| LoRA/PEFT | `references/lora-peft.md` | 参数高效微调、适配器 |
| 数据集准备 | `references/dataset-preparation.md` | 训练数据格式化、质量检查 |
| 超参数 | `references/hyperparameter-tuning.md` | 学习率、批量大小、调度器 |
| 评估 | `references/evaluation-metrics.md` | 基准测试、指标、模型对比 |
| 部署 | `references/deployment-optimization.md` | 模型合并、量化、服务 |

## 最小工作示例 — 使用 Hugging Face PEFT 的 LoRA 微调

```python
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import torch

# 1. 加载基础模型和分词器
model_id = "meta-llama/Llama-3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# 2. 配置 LoRA 适配器
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,               # rank — 增加提升容量，减少节省内存
    lora_alpha=32,      # 缩放因子；通常为 rank 的 2 倍
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 验证：应为总参数的 ~0.1–1%

# 3. 加载和格式化数据集（Alpaca 风格 JSONL）
dataset = load_dataset("json", data_files={"train": "train.jsonl", "test": "test.jsonl"})

def format_prompt(example):
    return {"text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"}

dataset = dataset.map(format_prompt)

# 4. 训练参数
training_args = TrainingArguments(
    output_dir="./checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,     # 有效批量大小 = 16
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,                 # 始终使用 warmup
    fp16=False,
    bf16=True,
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=100,
    save_steps=200,
    load_best_model_at_end=True,
)

# 5. 训练
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    dataset_text_field="text",
    max_seq_length=2048,
)
trainer.train()

# 6. 仅保存适配器权重
model.save_pretrained("./lora-adapter")
tokenizer.save_pretrained("./lora-adapter")
```

**QLoRA 变体** — 在加载模型前添加以下行以启用 4-bit 量化：
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map="auto")
```

**合并适配器到基础模型用于部署：**
```python
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16)
merged = PeftModel.from_pretrained(base, "./lora-adapter").merge_and_unload()
merged.save_pretrained("./merged-model")
```

## 约束

### 必须做
- 训练前验证数据集质量
- 大模型（>7B）使用参数高效方法
- 监控训练/验证损失曲线
- 记录超参数和训练配置
- 版本化数据集和模型检查点
- 始终包含学习率 warmup

### 禁止做
- 跳过数据质量验证
- 在小数据集上过拟合 — 使用正则化（dropout、weight decay）和早停
- 合并不兼容的适配器（rank 不匹配、基础模型不同或目标模块不同）
- 部署前不进行保留集评估和延迟基准测试

## 输出模板

实现微调时，始终提供：
1. **数据集准备脚本** 含验证逻辑（schema 检查、token 长度直方图、去重）
2. **训练配置**（完整的 `TrainingArguments` + `LoraConfig` 块，带注释）
3. **评估脚本** 报告困惑度、特定任务指标和延迟
4. **简要设计理由** — 为什么为此任务选择此 PEFT 方法、rank 和学习率
