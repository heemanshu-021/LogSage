"""
Generate and execute notebooks/02_anomaly_detection.ipynb
"""
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from nbclient import NotebookClient

nb = new_notebook()
cells = []

# Title
cells.append(new_markdown_cell('''# LogSage — 02. ML Anomaly Detection Pipeline

**Dataset:** HDFS LogHub Events (Aggregated by Block ID)  
**Algorithm:** Scikit-learn Isolation Forest Ensemble  
**Objective:** End-to-end unsupervised log anomaly detection with zero data leakage, reproducible block-level evaluation against ground-truth labels, and explainable feature attributions.

---

### Core Pipeline Architecture:
1. **Block Trace Aggregation:** Group raw log events into ordered traces per `BlockId`.
2. **Feature Engineering:** Total events, unique templates, template frequency vector, rare event ratio, Shannon entropy, error/warning counts.
3. **Data Leakage Prevention:** 80/20 stratified split by Block ID. Feature extractor vocabulary and scaler fitted exclusively on training blocks.
4. **Ensemble Isolation Forest:** Unsupervised partition trees isolating abnormal operational patterns.
5. **Evaluation:** Precision, Recall, F1-Score, Confusion Matrix, AUC-ROC, PR-AUC.
6. **Inference & Explanation:** Scoring new block streams with feature attribution.
'''))

# Cell 2: Imports & Environment
cells.append(new_code_cell('''import os
import sys
from pathlib import Path
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(os.path.abspath('..'))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.preprocessing.feature_extraction import BlockFeatureExtractor
from ml.models.isolation_forest import IsolationForestDetector
from ml.evaluation.evaluate import evaluate_predictions, generate_evaluation_plots

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 5)

print("Environment and LogSage ML modules successfully imported.")
'''))

# Cell 3: Data Loading
cells.append(new_markdown_cell('''## 1. Data Ingestion & Block Trace Aggregation
Loading structured log events and official ground-truth labels.
'''))

cells.append(new_code_cell('''data_path = Path('../data/raw/HDFS_100k.log_structured.csv')
if not data_path.exists():
    data_path = Path('data/raw/HDFS_100k.log_structured.csv')

labels_path = Path('../data/raw/anomaly_label.csv')
if not labels_path.exists():
    labels_path = Path('data/raw/anomaly_label.csv')

df_logs = pd.read_csv(data_path)
df_labels = pd.read_csv(labels_path)
labels_map = dict(zip(df_labels["BlockId"], df_labels["Label"]))

print(f"Total structured log events: {len(df_logs):,}")
print(f"Total ground-truth block labels: {len(labels_map):,}")

# Extract Block IDs and aggregate
block_regex = re.compile(r"(blk_-?\d+)")
df_logs["BlockId"] = df_logs["Content"].apply(lambda x: (block_regex.findall(str(x)) or [None])[0])
df_valid = df_logs.dropna(subset=["BlockId"]).copy()

block_events = BlockFeatureExtractor.group_events_by_block(df_valid)
print(f"Identified unique blocks with events: {len(block_events):,}")

block_ids = []
labels = []
for b_id in block_events.keys():
    lbl = labels_map.get(b_id)
    if lbl in ("Normal", "Anomaly"):
        block_ids.append(b_id)
        labels.append(1 if lbl == "Anomaly" else 0)

y = np.array(labels, dtype=int)
print(f"\\nDataset Class Distribution:")
print(f"  - Normal blocks  : {int(np.sum(y == 0)):,} ({np.mean(y == 0)*100:.2f}%)")
print(f"  - Anomaly blocks : {int(np.sum(y == 1)):,} ({np.mean(y == 1)*100:.2f}%)")
'''))

# Cell 4: Train/Test Split
cells.append(new_markdown_cell('''## 2. Reproducible Train / Test Split by Block ID
To **prevent data leakage**, splitting is performed strictly at the **Block ID level** using stratified sampling. Events belonging to the same block never appear in both training and test sets.
'''))

cells.append(new_code_cell('''train_bids, test_bids, y_train, y_test = train_test_split(
    block_ids,
    y,
    test_size=0.20,
    stratify=y,
    random_state=42,
)

train_dict = {b_id: block_events[b_id] for b_id in train_bids}
test_dict = {b_id: block_events[b_id] for b_id in test_bids}

print(f"Training set: {len(train_bids):,} blocks ({int(np.sum(y_train == 1))} anomalies, {np.mean(y_train == 1)*100:.2f}%)")
print(f"Test set    : {len(test_bids):,} blocks ({int(np.sum(y_test == 1))} anomalies, {np.mean(y_test == 1)*100:.2f}%)")
'''))

# Cell 5: Feature Extraction
cells.append(new_markdown_cell('''## 3. Feature Extraction (Fitted Exclusively on Training Data)
Extracting numerical representations:
- Total event count per block
- Unique template count
- Template frequencies
- Rare event count & ratio (< 1% training frequency)
- Shannon entropy of template distributions
- Error and warning indicators
- Standard scaling (mean & variance fitted on train only)
'''))

cells.append(new_code_cell('''extractor = BlockFeatureExtractor(rare_threshold=0.01, scale_features=True)
X_train, _ = extractor.fit_transform(train_dict)
X_test, _ = extractor.transform(test_dict)

print(f"Extracted {len(extractor.feature_names_)} numerical features.")
print(f"Learned template vocabulary size : {len(extractor.vocab_templates)}")
print(f"Identified rare templates        : {len(extractor.rare_templates)}")
print(f"X_train shape: {X_train.shape}")
print(f"X_test shape : {X_test.shape}")

print("\\nFeature Names:")
print(extractor.feature_names_)
'''))

# Cell 6: Model Training
cells.append(new_markdown_cell('''## 4. Isolation Forest Training
### Contamination & Threshold Explanation:
- In unsupervised Isolation Forest, `contamination` sets the expected proportion of outliers to calibrate the decision boundary offset.
- Based on training distribution prior, `contamination = 0.0394 (~3.94%)`.
- Random isolation trees partition anomalous points in fewer recursive splits.
'''))

cells.append(new_code_cell('''contamination_prior = float(np.mean(y_train == 1))
print(f"Configuring IsolationForest with contamination = {contamination_prior:.4f}...")

detector = IsolationForestDetector(
    n_estimators=150,
    contamination=contamination_prior,
    random_state=42,
)
detector.fit(X_train)

print(f"Trained IsolationForest ensemble with {detector.n_estimators} trees.")
print(f"Calibrated score span: [{detector.score_min_:.4f}, {detector.score_max_:.4f}]")
'''))

# Cell 7: Model Evaluation
cells.append(new_markdown_cell('''## 5. Model Evaluation on Held-Out Test Set
Evaluating against actual ground-truth labels on the test split.
'''))

cells.append(new_code_cell('''test_scores = detector.score(X_test)
test_preds = detector.predict(X_test)

report = evaluate_predictions(y_test, test_preds, scores=test_scores)
report.print_summary()
'''))

# Cell 8: Visualization
cells.append(new_markdown_cell('''## 6. Evaluation Visualizations
Plotting Confusion Matrix, Anomaly Score Distribution, ROC Curve, and Precision-Recall Curve.
'''))

cells.append(new_code_cell('''plot_out = Path('../data/processed/isolation_forest_evaluation.png')
if not plot_out.parent.exists():
    plot_out = Path('data/processed/isolation_forest_evaluation.png')

generate_evaluation_plots(y_test, test_preds, scores=test_scores, output_path=plot_out)

from IPython.display import Image, display
display(Image(filename=str(plot_out)))
'''))

# Cell 9: Reloadable Inference
cells.append(new_markdown_cell('''## 7. Model Persistence & Reusable Inference
Demonstrating that the trained pipeline can be reloaded and applied to arbitrary event sequences with explainable feature contributions.
'''))

cells.append(new_code_cell('''save_dir = Path('../ml/models/saved')
if not save_dir.exists():
    save_dir = Path('ml/models/saved')

model_file = save_dir / "isolation_forest.joblib"
config_file = save_dir / "feature_extractor.json"

detector.save(model_file)
extractor.save(config_file)

# Reload from disk
reloaded_model = IsolationForestDetector.load(model_file)
reloaded_extractor = BlockFeatureExtractor.load(config_file)

# Test inference on sample anomaly and normal blocks
test_bids_arr = np.array(test_bids)
sample_anom = test_bids_arr[y_test == 1][0]
sample_norm = test_bids_arr[y_test == 0][0]

res_a = reloaded_model.predict_block(sample_anom, test_dict[sample_anom], reloaded_extractor)
res_n = reloaded_model.predict_block(sample_norm, test_dict[sample_norm], reloaded_extractor)

print("=== Inference Demonstration ===")
print(f"\\nAnomaly Block ({sample_anom}):")
print(f"  Prediction    : {res_a['label']} (is_anomaly={res_a['is_anomaly']})")
print(f"  Anomaly Score : {res_a['anomaly_score']}")
print(f"  Top Features  : {res_a['top_features']}")

print(f"\\nNormal Block ({sample_norm}):")
print(f"  Prediction    : {res_norm['label']} (is_anomaly={res_norm['is_anomaly']})")
print(f"  Anomaly Score : {res_norm['anomaly_score']}")
print(f"  Top Features  : {res_norm['top_features']}")
'''))

nb['cells'] = cells
nb_path = Path("notebooks/02_anomaly_detection.ipynb")
with open(nb_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Created {nb_path}. Executing notebook cells...")
client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": "notebooks/"}})
client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook {nb_path} executed and saved successfully!")
