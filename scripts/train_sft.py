# scripts/train_sft.py
"""
QLoRA fine-tuning Qwen2.5-Coder-1.5B-Instruct.
Стабильный Trainer API (совместим с transformers 5.x).
Оптимизирован для RTX 5060 (8 GB VRAM).
"""
import json
import sys
import torch
from dataclasses import dataclass
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)


@dataclass
class Config:
    model_name: str = "models_cache/qwen-base"
    train_file: str = "data/sft_train.jsonl"
    valid_file: str = "data/sft_valid.jsonl"
    output_dir: str = "models_cache/qwen-secret-scanner-lora"

    # QLoRA для RTX 5060 8GB
    use_4bit: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    # Обучение
    num_epochs: int = 3
    batch_size: int = 4
    grad_accum: int = 2          # эффективный batch = 8
    learning_rate: float = 2e-4
    max_seq_length: int = 1024
    logging_steps: int = 10
    save_steps: int = 200


def load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def format_prompt(example: dict, tokenizer) -> str:
    """Форматирует пример в ChatML-промпт Qwen."""
    messages = [
        {"role": "system", "content": example["instruction"]},
        {"role": "user", "content": example["input"]},
        {"role": "assistant", "content": example["output"]},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )


def main(dry_run: bool = False):
    cfg = Config()

    if dry_run:
        cfg.num_epochs = 1
        cfg.output_dir = "models_cache/dry_run"
        print("DRY-RUN режим: 10 шагов для проверки пайплайна")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Устройство: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # 1. Токенизатор
    print("[1/6] Загрузка токенизатора...")
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Модель
    print("[2/6] Загрузка модели (~3 ГБ, первый раз 3-5 минут)...")
    if cfg.use_4bit and device == "cuda":
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            cfg.model_name, quantization_config=bnb, device_map="auto"
        )
        model = prepare_model_for_kbit_training(model)
        print("QLoRA 4-bit активирован")
    else:
        model = AutoModelForCausalLM.from_pretrained(cfg.model_name)
        print("CPU/fp16-режим")

    # 3. LoRA
    print("[3/6] Применение LoRA адаптеров...")
    model = get_peft_model(model, LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        task_type=TaskType.CAUSAL_LM,
    ))
    model.print_trainable_parameters()

    # 4. Данные
    print("[4/6] Загрузка и токенизация данных...")
    train_data = Dataset.from_list(load_jsonl(cfg.train_file))
    valid_data = Dataset.from_list(load_jsonl(cfg.valid_file))
    print(f"   Train: {len(train_data)} | Valid: {len(valid_data)}")

    if dry_run:
        train_data = train_data.select(range(32))
        valid_data = valid_data.select(range(8))

    def to_text(ex):
        return {"text": format_prompt(ex, tokenizer)}

    def tokenize(ex):
        return tokenizer(ex["text"], truncation=True, max_length=cfg.max_seq_length)

    train_data = (train_data.map(to_text)
                  .map(tokenize, batched=True, remove_columns=train_data.column_names))
    valid_data = (valid_data.map(to_text)
                  .map(tokenize, batched=True, remove_columns=valid_data.column_names))

    # 5. Обучение
    print(f"[5/6] Обучение ({cfg.num_epochs} эпохи)...")
    args = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.num_epochs,
        per_device_train_batch_size=cfg.batch_size,
        per_device_eval_batch_size=cfg.batch_size,
        gradient_accumulation_steps=cfg.grad_accum,
        learning_rate=cfg.learning_rate,
        logging_steps=cfg.logging_steps,
        save_steps=cfg.save_steps,
        eval_strategy="steps",
        eval_steps=cfg.save_steps,
        save_strategy="steps",
        load_best_model_at_end=True,
        fp16=(device == "cuda"),
        report_to="none",
        max_steps=10 if dry_run else -1,
        gradient_checkpointing=True,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_data,
        eval_dataset=valid_data,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()

    # 6. Сохранение
    print("[6/6] Сохранение адаптеров...")
    Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)

    print()
    print("=" * 60)
    print(f"Адаптеры сохранены: {cfg.output_dir}")
    for f in Path(cfg.output_dir).iterdir():
        print(f"   {f.name}: {f.stat().st_size / 1e6:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)