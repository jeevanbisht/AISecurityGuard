# CBDB Model Training Examples

This directory contains optional dataset extraction and model-training examples
based on the public [China Biographical Database SQLite dataset](https://huggingface.co/datasets/cbdb/cbdb-sqlite).
Review the upstream dataset terms before downloading or redistributing data.
Database files, extracted datasets, and trained models are not included in this
repository.

## Setup

```bash
cd model_training
python -m venv .venv
python -m pip install -r requirements.txt
```

Download the CBDB SQLite file from the upstream dataset and place it in this
directory, or pass its path with `--db_path`.

## Commands

Extract 10,000 samples:

```bash
python main.py --task extract --samples 10000
```

Train the dynasty classifier:

```bash
python main.py --task classify
```

Train graph embeddings:

```bash
python main.py --task graph --epochs 5
```

Fine-tune a compatible causal language model:

```bash
python main.py --task llm --samples 1000 --epochs 1
```

The scripts print metrics for each local run. Results depend on the dataset
snapshot, sample limits, model version, hardware, and random initialization.
