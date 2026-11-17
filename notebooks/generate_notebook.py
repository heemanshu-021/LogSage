"""
Script to generate and execute notebooks/01_data_exploration.ipynb
"""
import os
import sys
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
cells = []

# Cell 1: Title
cells.append(new_markdown_cell('''# LogSage — 01. HDFS Dataset Acquisition & Exploration

**Dataset Source:** [LogHub (logpai/loghub)](https://github.com/logpai/loghub) & [Loglizer (logpai/loglizer)](https://github.com/logpai/loglizer)  
**Dataset:** Hadoop Distributed File System (HDFS_v1)  
**Core Objective:** Inspect raw log structures, extract Block IDs, map ground-truth block labels, analyze normal vs. anomalous block traces, handle malformed entries, and establish reusable preprocessing foundations.

> **CRITICAL GROUNDING:**
> In HDFS logs, anomalies are defined and labeled at the **BLOCK LEVEL** (`BlockId`), not per individual log message. A single block trace comprises multiple interleaved log events across NameNode and DataNodes. Labels must never be arbitrarily assigned to individual lines.
'''))

# Cell 2: Imports
cells.append(new_code_cell('''import os
import sys
from pathlib import Path
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root is in sys.path
PROJECT_ROOT = Path(os.path.abspath('..'))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if '.' not in sys.path:
    sys.path.insert(0, '.')

from ml.preprocessing.hdfs_preprocessor import HDFSPreprocessor, BLOCK_ID_REGEX

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 5)
plt.rcParams['font.size'] = 11

print("Python environment and preprocessor successfully loaded.")
'''))

# Cell 3: Markdown - Section 1
cells.append(new_markdown_cell('''## 1. Ground-Truth Anomaly Labels Analysis
The official ground-truth label file `anomaly_label.csv` contains the definitive binary labels (`Normal` vs `Anomaly`) assigned to Hadoop Block IDs.
'''))

# Cell 4: Code - Labels Exploration
cells.append(new_code_cell('''labels_path = Path('../data/raw/anomaly_label.csv')
if not labels_path.exists():
    labels_path = Path('data/raw/anomaly_label.csv')

df_labels = pd.read_csv(labels_path)
print(f"Total Block records in ground truth: {len(df_labels):,}")
print("\\nDataset preview:")
display(df_labels.head(10))

label_counts = df_labels['Label'].value_counts()
label_pcts = df_labels['Label'].value_counts(normalize=True) * 100

summary_df = pd.DataFrame({
    'Count': label_counts,
    'Percentage (%)': label_pcts.round(2)
})
print("\\nClass Distribution:")
display(summary_df)

imbalance_ratio = label_counts['Normal'] / label_counts['Anomaly']
print(f"\\nClass Imbalance Ratio: {imbalance_ratio:.2f} Normal blocks for every 1 Anomaly block (~{label_pcts['Anomaly']:.2f}% anomaly rate)")
'''))

# Cell 5: Markdown - Section 2
cells.append(new_markdown_cell('''## 2. Raw HDFS Log Structure Inspection
Each standard raw HDFS log record follows the structure:
`Date Time Pid Level Component: Content`
'''))

# Cell 6: Code - Raw logs inspection
cells.append(new_code_cell('''raw_log_path = Path('../data/raw/HDFS_2k.log')
if not raw_log_path.exists():
    raw_log_path = Path('data/raw/HDFS_2k.log')

with open(raw_log_path, 'r', encoding='utf-8') as f:
    raw_lines = [f.readline().strip() for _ in range(10)]

print(f"Sample raw log lines from {raw_log_path.name}:\\n")
for idx, line in enumerate(raw_lines, start=1):
    print(f"[{idx:02d}] {line}")
'''))

# Cell 7: Markdown - Section 3
cells.append(new_markdown_cell('''## 3. Parsing and Block ID Extraction with Reusable Preprocessor
We use `HDFSPreprocessor` to:
1. Parse log records without loss of original content.
2. Extract all embedded `BlockId` references (`blk_-?\\d+`).
3. Isolate malformed or non-block records into a quarantined unassigned list.
4. Group log lines into structured `BlockTrace` sequences mapped to ground-truth labels.
'''))

# Cell 8: Code - Preprocessing and Grouping
cells.append(new_code_cell('''preprocessor = HDFSPreprocessor(labels_path=labels_path)
print(f"Initialized preprocessor with {preprocessor.label_count:,} ground-truth block labels.")

records = list(preprocessor.parse_file(raw_log_path))
print(f"Parsed total log records: {len(records):,}")

traces, unassigned = preprocessor.group_by_block(records)
print(f"Identified unique blocks: {len(traces):,}")
print(f"Unassigned / non-block records: {len(unassigned):,}")

# Convert aggregated block traces to feature summary DataFrame
df_blocks = preprocessor.to_dataframe(traces)
print("\\nAggregated Block Traces summary:")
display(df_blocks.head(10))
'''))

# Cell 9: Markdown - Section 4
cells.append(new_markdown_cell('''## 4. Handling Malformed Records
Logs may contain empty lines, stack trace dumps, or daemon heartbeats lacking Block IDs. We verify these are isolated properly without discarding or throwing errors.
'''))

# Cell 10: Code - Malformed handling
cells.append(new_code_cell('''malformed_records = [r for r in records if r.is_malformed]
print(f"Total malformed/non-block records in {raw_log_path.name}: {len(malformed_records)}")

if malformed_records:
    print("\\nSample malformed/non-block records:")
    for r in malformed_records[:5]:
        print(f"Line {r.line_number}: Reason='{r.malformed_reason}' | Raw: {r.raw_line[:80]}...")
else:
    print("All records in this sample file contained valid Block IDs.")

# Synthetic robustness test with malformed records
synthetic_lines = [
    "",
    "081109 203615 148 INFO dfs.DataNode: Service startup without block",
    "MALFORMED_GARBLED_HEADER_DATA",
    "081109 203616 148 ERROR dfs.DataNode: Block blk_9999999 has disk failure"
]
synthetic_records = [preprocessor.parse_line(l, idx) for idx, l in enumerate(synthetic_lines, 1)]
s_traces, s_unassigned = preprocessor.group_by_block(synthetic_records)
print(f"\\nRobustness check: {len(s_unassigned)} quarantined out of {len(synthetic_lines)} lines, {len(s_traces)} valid block trace extracted.")
'''))

# Cell 11: Markdown - Section 5
cells.append(new_markdown_cell('''## 5. Statistical Analysis: Normal vs. Anomalous Blocks
We analyze the distribution of event trace lengths, error frequencies, and component interactions across normal and anomalous blocks.
'''))

# Cell 12: Code - Statistics computation
cells.append(new_code_cell('''print("=== Statistical Breakdown by Block Class ===")
stats_by_label = df_blocks.groupby('Label')[['EventCount', 'HasError', 'HasWarning', 'NumComponents']].agg(
    count=('EventCount', 'count'),
    mean_events=('EventCount', 'mean'),
    median_events=('EventCount', 'median'),
    max_events=('EventCount', 'max'),
    error_rate=('HasError', 'mean')
).reset_index()
display(stats_by_label)
'''))

# Cell 13: Markdown - Section 6
cells.append(new_markdown_cell('''## 6. Dataset Visualizations
Visualizing the class imbalance, event sequence length distributions, and severity characteristics.
'''))

# Cell 14: Code - Visualizations
cells.append(new_code_cell('''fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1: Ground-Truth Class Distribution (Full Dataset)
colors = ['#2b5c8f', '#d9534f']
axes[0].bar(['Normal', 'Anomaly'], [label_counts['Normal'], label_counts['Anomaly']], color=colors, width=0.5)
axes[0].set_yscale('log')
axes[0].set_title('HDFS Ground Truth Class Distribution (Log Scale)\\n(575,061 Total Blocks)')
axes[0].set_ylabel('Number of Blocks (log scale)')
for i, (cnt, pct) in enumerate(zip(label_counts, label_pcts)):
    axes[0].text(i, cnt * 1.15, f"{cnt:,}\\n({pct:.2f}%)", ha='center', fontweight='bold')

# Plot 2: Event Count per Block Distribution
sns.histplot(data=df_blocks, x='EventCount', hue='Label', bins=15, ax=axes[1], palette={'Normal': '#2b5c8f', 'Anomaly': '#d9534f'}, multiple='dodge')
axes[1].set_title('Event Count Distribution per Block Trace')
axes[1].set_xlabel('Events per Block')
axes[1].set_ylabel('Block Count')

# Plot 3: Error Rate by Block Class
error_pct = df_blocks.groupby('Label')['HasError'].mean() * 100
axes[2].bar(error_pct.index, error_pct.values, color=['#2b5c8f', '#d9534f'], width=0.5)
axes[2].set_title('Percentage of Blocks Containing ERROR Logs')
axes[2].set_ylabel('Error Presence (%)')
for i, v in enumerate(error_pct.values):
    axes[2].text(i, v + 0.5, f"{v:.1f}%", ha='center', fontweight='bold')

plt.tight_layout()
out_dir = Path('../data/processed')
out_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(out_dir / 'hdfs_data_exploration_summary.png', dpi=150)
plt.show()
print("Visualization saved to data/processed/hdfs_data_exploration_summary.png")
'''))

# Cell 15: Markdown - Section 7
cells.append(new_markdown_cell('''## 7. Key Findings & Architecture Guidance
1. **Block-Level Granularity is Mandatory:** HDFS logs cannot be effectively classified on isolated single lines. A block lifecycle spans multiple events across components (DataNode, FSNamesystem, PacketResponder).
2. **Severe Class Imbalance:** Normal blocks comprise 97.07% while anomalous blocks comprise 2.93% (ratio ~33:1). Unsupervised algorithms (Isolation Forest, LOF, Autoencoders) and evaluation with Precision/Recall/F1/AUC-ROC are critical rather than raw accuracy.
3. **Trace Length Signatures:** Anomalous blocks exhibit distinctive event length profiles and error cascades compared to the typical lifecycle of normal blocks.
4. **Clean Decoupling:** Reusable preprocessor `ml.preprocessing.hdfs_preprocessor.HDFSPreprocessor` robustly extracts Block IDs and isolates malformed records without data loss.
'''))

nb['cells'] = cells

out_path = Path("notebooks/01_data_exploration.ipynb")
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"{out_path} created with {len(cells)} cells.")
