import os
import sys

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

sys.stdout.reconfigure(encoding="utf-8")


def train_dynasty_classifier(
    data_path="cbdb_dynasty_dataset.csv", model_output="dynasty_classifier.joblib"
):
    if not os.path.exists(data_path):
        print(f"Data file {data_path} not found. Running extractor first...")
        from cbdb_extractor import CBDBDataExtractor

        extractor = CBDBDataExtractor()
        extractor.extract_dynasty_classification_data(data_path)
        extractor.close()

    print(f"Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)

    # Filter out minor dynasties with very few samples
    counts = df["dynasty_name"].value_counts()
    major_dynasties = counts[counts >= 100].index
    df = df[df["dynasty_name"].isin(major_dynasties)].copy()

    print(f"Top Dynasties included ({len(major_dynasties)} classes):")
    for d, c in counts[counts >= 100].items():
        print(f"  - {d}: {c} records")

    # Feature Engineering
    feature_cols = [
        "c_female",
        "c_ethnicity_code",
        "c_index_year",
        "c_birthyear",
        "c_deathyear",
        "office_count",
        "kinship_count",
        "assoc_count",
    ]

    # Fill missing values
    for col in feature_cols:
        df[col] = df[col].fillna(0)

    X = df[feature_cols].values
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["dynasty_name"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("\nTraining Random Forest & Gradient Boosting Classifiers...")
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=15, random_state=42, n_jobs=-1
    )
    clf.fit(X_train_scaled, y_train)

    y_pred = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nRandom Forest Accuracy: {acc:.4f} ({acc * 100:.2f}%)")

    print("\nDetailed Classification Report:")
    target_names = label_encoder.classes_
    print(classification_report(y_test, y_pred, target_names=target_names))

    # Save model and metadata
    saved_bundle = {
        "model": clf,
        "scaler": scaler,
        "label_encoder": label_encoder,
        "feature_cols": feature_cols,
    }
    joblib.dump(saved_bundle, model_output)
    print(f"Model saved to {model_output}")

    # Feature importance
    print("\nFeature Importances:")
    importances = clf.feature_importances_
    for col, imp in sorted(
        zip(feature_cols, importances), key=lambda x: x[1], reverse=True
    ):
        print(f"  {col:20s}: {imp:.4f}")

    return clf, acc


if __name__ == "__main__":
    train_dynasty_classifier()
