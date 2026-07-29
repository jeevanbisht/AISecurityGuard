import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

sys.stdout.reconfigure(encoding="utf-8")


class SocialGraphEmbeddingModel(nn.Module):
    def __init__(self, num_nodes, embedding_dim=64):
        super().__init__()
        self.node_embeddings = nn.Embedding(num_nodes, embedding_dim)
        # Initialize embeddings uniformly
        nn.init.uniform_(self.node_embeddings.weight, -0.1, 0.1)

    def forward(self, source_ids, target_ids):
        src_emb = self.node_embeddings(source_ids)
        tgt_emb = self.node_embeddings(target_ids)
        # Dot product similarity score for link prediction
        score = torch.sum(src_emb * tgt_emb, dim=1)
        return score


def train_graph_embeddings(
    data_path="cbdb_social_graph.csv",
    embedding_dim=64,
    epochs=5,
    batch_size=256,
    lr=0.01,
    max_edges=50000,
):
    if not os.path.exists(data_path):
        print(f"Data file {data_path} not found. Running extractor first...")
        from cbdb_extractor import CBDBDataExtractor

        extractor = CBDBDataExtractor()
        extractor.extract_social_graph_edges(data_path, limit=max_edges)
        extractor.close()

    print(f"Loading social graph edges from {data_path}...")
    df = pd.read_csv(data_path).head(max_edges)

    # Remap node IDs to contiguous 0..N-1 indices
    unique_nodes = np.unique(
        np.concatenate([df["source_id"].values, df["target_id"].values])
    )
    node2idx = {node: i for i, node in enumerate(unique_nodes)}
    idx2node = {i: node for i, node in enumerate(unique_nodes)}
    num_nodes = len(unique_nodes)

    print(
        f"Graph stats: {num_nodes} unique person nodes, {len(df)} relationship edges."
    )

    src_indices = torch.tensor(
        [node2idx[s] for s in df["source_id"].values], dtype=torch.long
    )
    tgt_indices = torch.tensor(
        [node2idx[t] for t in df["target_id"].values], dtype=torch.long
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SocialGraphEmbeddingModel(num_nodes, embedding_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()

    print(f"Training Knowledge Graph / Link Prediction Embeddings on {device}...")

    num_samples = len(df)
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        permutation = torch.randperm(num_samples)

        for i in range(0, num_samples, batch_size):
            optimizer.zero_grad()
            batch_idx = permutation[i : i + batch_size]

            pos_src = src_indices[batch_idx].to(device)
            pos_tgt = tgt_indices[batch_idx].to(device)

            # Generate negative samples (random target nodes)
            neg_tgt = torch.randint(0, num_nodes, pos_src.shape, dtype=torch.long).to(
                device
            )

            pos_scores = model(pos_src, pos_tgt)
            neg_scores = model(pos_src, neg_tgt)

            scores = torch.cat([pos_scores, neg_scores])
            labels = torch.cat(
                [torch.ones_like(pos_scores), torch.zeros_like(neg_scores)]
            ).to(device)

            loss = criterion(scores, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(
            f"Epoch {epoch + 1}/{epochs} Loss: {total_loss / (num_samples // batch_size + 1):.4f}"
        )

    print("\nExtraction & Training complete. Node embeddings learned successfully!")

    # Save embeddings
    embeddings = model.node_embeddings.weight.detach().cpu().numpy()
    np.savez("cbdb_person_embeddings.npz", embeddings=embeddings, idx2node=idx2node)
    print("Saved learned embeddings to cbdb_person_embeddings.npz")

    return model, idx2node


if __name__ == "__main__":
    train_graph_embeddings()
