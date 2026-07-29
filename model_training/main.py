import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="CBDB Machine Learning & LLM Fine-Tuning Pipeline"
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=["extract", "classify", "graph", "llm", "all"],
        default="all",
        help="Task to run: 'extract', 'classify' (Dynasty Classifier), 'graph' (Graph Embeddings), 'llm' (Instruction Tuning), or 'all'",
    )
    parser.add_argument(
        "--db_path", type=str, default=None, help="Path to CBDB sqlite3 database file"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10000,
        help="Number of records/samples to process",
    )
    parser.add_argument(
        "--epochs", type=int, default=3, help="Number of training epochs"
    )

    args = parser.parse_args()

    print("=" * 60)
    print(" China Biographical Database (CBDB) Machine Learning Pipeline")
    print("=" * 60)

    # Step 1: Extract datasets if requested or needed
    if args.task in ["extract", "all"]:
        print("\n[Step 1/3] Extracting datasets from CBDB SQLite Database...")
        from cbdb_extractor import CBDBDataExtractor

        extractor = CBDBDataExtractor(db_path=args.db_path)
        extractor.extract_instruction_qa(limit=args.samples)
        extractor.extract_dynasty_classification_data(limit=args.samples * 3)
        extractor.extract_social_graph_edges(limit=args.samples * 5)
        extractor.close()
        print("Dataset extraction completed successfully.")

    # Step 2: Train Dynasty Classification Model
    if args.task in ["classify", "all"]:
        print("\n[Step 2/3] Training Dynasty Classifier Model...")
        from train_dynasty_classifier import train_dynasty_classifier

        train_dynasty_classifier(data_path="cbdb_dynasty_dataset.csv")

    # Step 3: Train Graph Embeddings
    if args.task in ["graph", "all"]:
        print("\n[Step 3/3] Training Social Graph & Kinship Embedding Model...")
        from train_graph_embeddings import train_graph_embeddings

        train_graph_embeddings(data_path="cbdb_social_graph.csv", epochs=args.epochs)

    # Step 4: LLM Fine-Tuning
    if args.task in ["llm"]:
        print("\n[Optional] Fine-tuning Language Model on CBDB QA Pairs...")
        from train_instruction_llm import train_cbdb_llm

        train_cbdb_llm(epochs=args.epochs, max_samples=args.samples)

    print("\nPipeline execution finished successfully!")


if __name__ == "__main__":
    main()
