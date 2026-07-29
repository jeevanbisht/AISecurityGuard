import json
import os
import sys

import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8")


class CBDBDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_length=256):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    text = f"User: {item['instruction']}\nAssistant: {item['output']}"
                    self.data.append(text)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text = self.data[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"].squeeze(0)
        attention_mask = encoding["attention_mask"].squeeze(0)

        # Causal LM labels are input_ids shifted
        labels = input_ids.clone()
        labels[attention_mask == 0] = -100  # Ignore padding in loss

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }


def train_cbdb_llm(
    data_path="cbdb_instruction_qa.jsonl",
    model_name="Qwen/Qwen2.5-0.5B-Instruct",
    output_dir="./cbdb_llm_model",
    epochs=1,
    batch_size=4,
    lr=5e-5,
    max_samples=2000,
):
    """
    Fine-tunes a causal language model (e.g., Qwen2.5 / TinyLlama) on CBDB biographical QA dataset.
    """
    if not os.path.exists(data_path):
        print(f"Data file {data_path} not found. Running extractor first...")
        from cbdb_extractor import CBDBDataExtractor

        extractor = CBDBDataExtractor()
        extractor.extract_instruction_qa(data_path, limit=max_samples)
        extractor.close()

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as e:
        print(f"Hugging Face transformers package import error: {e}")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using compute device: {device}")
    print(f"Loading pretrained tokenizer & model: {model_name}...")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.to(device)

    dataset = CBDBDataset(data_path, tokenizer, max_length=256)
    if len(dataset) > max_samples:
        indices = torch.randperm(len(dataset))[:max_samples].tolist()
        dataset = torch.utils.data.Subset(dataset, indices)

    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    print(f"\nStarting fine-tuning for {epochs} epoch(s) on {len(dataset)} samples...")
    model.train()

    for epoch in range(epochs):
        total_loss = 0
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{epochs}")

        for batch in progress_bar:
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            progress_bar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch + 1} Average Loss: {avg_loss:.4f}")

    print(f"\nSaving fine-tuned model to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Model saved successfully!")

    # Test Generation
    print("\n--- Testing Model Inference ---")
    model.eval()
    test_prompt = (
        "User: 请介绍一下中国历史人物【安惇】的生平背景、朝代及官职。\nAssistant:"
    )
    inputs = tokenizer(test_prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs, max_new_tokens=128, temperature=0.7, do_sample=True, top_p=0.9
        )
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print("Generated Text:\n", generated_text)


if __name__ == "__main__":
    train_cbdb_llm(epochs=1, batch_size=2, max_samples=500)
