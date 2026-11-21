"""
End-to-End Training, Evaluation, and Serialization for LogSage ML Pipeline.
"""
from pathlib import Path
import sys
import re
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.preprocessing.feature_extraction import BlockFeatureExtractor
from ml.models.isolation_forest import IsolationForestDetector
from ml.evaluation.evaluate import evaluate_predictions, generate_evaluation_plots
from backend.core.config import settings

def train_legacy():
    print("=" * 70)
    print("LOGSAGE ANOMALY DETECTION TRAINING & EVALUATION PIPELINE")
    print("=" * 70)

    # 1. Load Data
    raw_csv = Path("data/raw/HDFS_100k.log_structured.csv")
    labels_csv = Path("data/raw/anomaly_label.csv")

    if not raw_csv.exists() or not labels_csv.exists():
        raise FileNotFoundError("Missing raw HDFS or label data files in data/raw/")

    print(f"Loading structured logs from {raw_csv}...")
    df_logs = pd.read_csv(raw_csv)
    print(f"Loaded {len(df_logs):,} log events.")

    print(f"Loading ground truth labels from {labels_csv}...")
    df_labels = pd.read_csv(labels_csv)
    labels_map = dict(zip(df_labels["BlockId"], df_labels["Label"]))
    print(f"Loaded {len(labels_map):,} ground-truth block labels.")

    # 2. Extract Block IDs and Group
    print("\nExtracting Block IDs and aggregating event traces...")
    block_regex = re.compile(r"(blk_-?\d+)")
    df_logs["BlockId"] = df_logs["Content"].apply(lambda x: (block_regex.findall(str(x)) or [None])[0])
    df_valid = df_logs.dropna(subset=["BlockId"]).copy()

    block_events = BlockFeatureExtractor.group_events_by_block(df_valid)
    print(f"Identified {len(block_events):,} unique blocks with events.")

    # Assign labels to blocks
    block_ids = []
    labels = []
    for b_id in block_events.keys():
        lbl = labels_map.get(b_id)
        if lbl in ("Normal", "Anomaly"):
            block_ids.append(b_id)
            labels.append(1 if lbl == "Anomaly" else 0)

    y = np.array(labels, dtype=int)
    print(f"Blocks with valid ground-truth: {len(block_ids):,}")
    print(f"  - Normal blocks  : {int(np.sum(y == 0)):,} ({np.mean(y == 0)*100:.2f}%)")
    print(f"  - Anomaly blocks : {int(np.sum(y == 1)):,} ({np.mean(y == 1)*100:.2f}%)")

    # 3. Stratified Train / Test Split by Block ID (Preventing Data Leakage)
    print("\nPerforming 80/20 stratified train/test split by Block ID...")
    train_bids, test_bids, y_train, y_test = train_test_split(
        block_ids,
        y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )
    print(f"Training blocks: {len(train_bids):,} (Anomalies: {int(np.sum(y_train == 1))})")
    print(f"Testing blocks : {len(test_bids):,} (Anomalies: {int(np.sum(y_test == 1))})")

    train_dict = {b_id: block_events[b_id] for b_id in train_bids}
    test_dict = {b_id: block_events[b_id] for b_id in test_bids}

    # 4. Feature Extraction (Fitted Strictly on Training Data)
    print("\nFitting BlockFeatureExtractor on training split...")
    extractor = BlockFeatureExtractor(rare_threshold=0.01, scale_features=True)
    X_train, _ = extractor.fit_transform(train_dict)
    print(f"X_train shape: {X_train.shape} (Features: {len(extractor.feature_names_)})")

    print("Transforming test split...")
    X_test, _ = extractor.transform(test_dict)
    print(f"X_test shape : {X_test.shape}")

    # 5. Train Isolation Forest
    contamination_rate = float(np.mean(y_train == 1))
    print(f"\nTraining Isolation Forest with empirical contamination prior: {contamination_rate:.4f}...")
    detector = IsolationForestDetector(
        n_estimators=150,
        contamination=contamination_rate,
        random_state=42,
    )
    detector.fit(X_train)

    # 6. Inference and Evaluation on Test Split
    print("\nGenerating predictions on held-out test split...")
    test_scores = detector.score(X_test)
    test_preds = detector.predict(X_test)

    report = evaluate_predictions(y_test, test_preds, scores=test_scores)
    report.print_summary()

    # 7. Generate Evaluation Visualizations
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_path = out_dir / "isolation_forest_evaluation.png"
    print(f"\nGenerating evaluation plots to {plot_path}...")
    generate_evaluation_plots(y_test, test_preds, scores=test_scores, output_path=plot_path)

    # 8. Save Model and Preprocessor Configuration
    save_dir = Path(settings.MODEL_SAVE_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)

    model_path = save_dir / "isolation_forest.joblib"
    config_path = save_dir / "feature_extractor.json"

    print(f"Saving model to {model_path}...")
    detector.save(model_path)

    print(f"Saving feature extractor configuration to {config_path}...")
    extractor.save(config_path)

    # 9. Test Reusable Reloadable Inference
    print("\nTesting reloadable inference from disk...")
    reloaded_detector = IsolationForestDetector.load(model_path)
    reloaded_extractor = BlockFeatureExtractor.load(config_path)

    # Test on an actual anomalous test block and a normal test block
    test_bids_arr = np.array(test_bids)
    sample_anomaly_bid = test_bids_arr[y_test == 1][0]
    sample_normal_bid = test_bids_arr[y_test == 0][0]

    res_anom = reloaded_detector.predict_block(sample_anomaly_bid, test_dict[sample_anomaly_bid], reloaded_extractor)
    res_norm = reloaded_detector.predict_block(sample_normal_bid, test_dict[sample_normal_bid], reloaded_extractor)

    print(f"\nInference on Ground-Truth Anomaly Block ({sample_anomaly_bid}):")
    print(f"  Prediction    : {res_anom['label']} (is_anomaly={res_anom['is_anomaly']})")
    print(f"  Anomaly Score : {res_anom['anomaly_score']}")
    print(f"  Top Features  : {res_anom['top_features']}")

    print(f"\nInference on Ground-Truth Normal Block ({sample_normal_bid}):")
    print(f"  Prediction    : {res_norm['label']} (is_anomaly={res_norm['is_anomaly']})")
    print(f"  Anomaly Score : {res_norm['anomaly_score']}")
    print(f"  Top Features  : {res_norm['top_features']}")

    print("\n" + "=" * 70)
    print("PIPELINE TRAINING & EVALUATION COMPLETE!")
    print("=" * 70)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Train and evaluate LogSage on Logfit HDFS_v1.")
    parser.add_argument("--dataset", choices=("logfit", "legacy"), default="logfit",
                        help="Use the Logfit Parquet pipeline (default) or the historical CSV pipeline.")
    parser.add_argument("--max-rows", type=int, default=None,
                        help="Run a bounded Logfit smoke training pass and write separate smoke artifacts.")
    parser.add_argument("--batch-size", type=int, default=50_000)
    args = parser.parse_args()

    if args.dataset == "legacy":
        train_legacy()
        return

    from ml.logfit_training import train_logfit
    if args.max_rows is not None:
        train_logfit(
            artifact_dir=PROJECT_ROOT / "data" / "processed" / "logfit_smoke_artifacts",
            max_rows=args.max_rows,
            batch_size=args.batch_size,
        )
    else:
        train_logfit(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
