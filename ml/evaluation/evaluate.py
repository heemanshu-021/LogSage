"""
LogSage Anomaly Detection Evaluation Module.

Computes standard ML classification metrics and generates evaluation visualizations:
- Precision, Recall, F1-score, Support
- Confusion Matrix (TP, FP, TN, FN)
- AUC-ROC and Average Precision (PR-AUC)
- Evaluation plots (Confusion Matrix, ROC Curve, PR Curve, Score Distributions)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from backend.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationReport:
    """Rigorous evaluation metrics container without fabricated values."""
    total_samples: int
    normal_count: int
    anomaly_count: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    specificity: float
    accuracy: float
    auc_roc: Optional[float] = None
    pr_auc: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def print_summary(self) -> None:
        print("=" * 65)
        print("LOGSAGE ANOMALY DETECTION EVALUATION REPORT")
        print("=" * 65)
        print(f"Total Evaluated Blocks : {self.total_samples:,}")
        print(f"  - Normal Blocks      : {self.normal_count:,}")
        print(f"  - Anomalous Blocks   : {self.anomaly_count:,} ({self.anomaly_count/self.total_samples*100:.2f}%)")
        print("-" * 65)
        print(f"Confusion Matrix:")
        print(f"  TP: {self.true_positives:<6} | FP: {self.false_positives:<6}")
        print(f"  FN: {self.false_negatives:<6} | TN: {self.true_negatives:<6}")
        print("-" * 65)
        print(f"Precision              : {self.precision:.4f}")
        print(f"Recall (Sensitivity)   : {self.recall:.4f}")
        print(f"F1-Score               : {self.f1:.4f}")
        print(f"Specificity            : {self.specificity:.4f}")
        print(f"Accuracy               : {self.accuracy:.4f}")
        if self.auc_roc is not None:
            print(f"AUC-ROC                : {self.auc_roc:.4f}")
        if self.pr_auc is not None:
            print(f"PR-AUC (Avg Precision) : {self.pr_auc:.4f}")
        print("=" * 65)


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: Optional[np.ndarray] = None,
) -> EvaluationReport:
    """
    Compute rigorous binary classification metrics for anomaly detection.

    Args:
        y_true: Ground truth binary labels (1 = Anomaly, 0 = Normal).
        y_pred: Predicted binary labels (1 = Anomaly, 0 = Normal).
        scores: Continuous anomaly scores in [0, 1]. Optional.
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    accuracy = float((tp + tn) / max(len(y_true), 1))

    auc_roc_val = None
    pr_auc_val = None
    if scores is not None and len(np.unique(y_true)) > 1:
        try:
            auc_roc_val = float(roc_auc_score(y_true, scores))
            p_curve, r_curve, _ = precision_recall_curve(y_true, scores)
            pr_auc_val = float(auc(r_curve, p_curve))
        except Exception:
            pass

    return EvaluationReport(
        total_samples=len(y_true),
        normal_count=int(np.sum(y_true == 0)),
        anomaly_count=int(np.sum(y_true == 1)),
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        precision=precision,
        recall=recall,
        f1=f1,
        specificity=specificity,
        accuracy=accuracy,
        auc_roc=auc_roc_val,
        pr_auc=pr_auc_val,
    )


def generate_evaluation_plots(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: Optional[np.ndarray] = None,
    output_path: Optional[str | Path] = None,
    title_suffix: str = "Isolation Forest",
) -> None:
    """
    Generates a 4-panel evaluation dashboard:
    1. Confusion Matrix Heatmap
    2. Anomaly Score Distribution (Normal vs Anomaly)
    3. ROC Curve
    4. Precision-Recall Curve
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle(f"LogSage Anomaly Detection Evaluation — {title_suffix}", fontsize=14, fontweight="bold")

    # 1. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    sns.heatmap(
        cm,
        annot=True,
        fmt=",d",
        cmap="Blues",
        cbar=False,
        ax=axes[0, 0],
        xticklabels=["Predicted Normal", "Predicted Anomaly"],
        yticklabels=["Actual Normal", "Actual Anomaly"],
        annot_kws={"size": 13, "weight": "bold"},
    )
    axes[0, 0].set_title("Confusion Matrix", fontsize=12)

    # 2. Score Distribution
    if scores is not None:
        normal_scores = scores[y_true == 0]
        anomaly_scores = scores[y_true == 1]
        axes[0, 1].hist(normal_scores, bins=30, alpha=0.6, color="#2b5c8f", label=f"Normal (n={len(normal_scores):,})", density=True)
        axes[0, 1].hist(anomaly_scores, bins=30, alpha=0.6, color="#d9534f", label=f"Anomaly (n={len(anomaly_scores):,})", density=True)
        axes[0, 1].set_title("Anomaly Score Distribution by Class", fontsize=12)
        axes[0, 1].set_xlabel("Normalised Anomaly Score [0, 1]")
        axes[0, 1].set_ylabel("Density")
        axes[0, 1].legend()

    # 3. ROC Curve
    if scores is not None and len(np.unique(y_true)) > 1:
        fpr, tpr, _ = roc_curve(y_true, scores)
        roc_auc_val = auc(fpr, tpr)
        axes[1, 0].plot(fpr, tpr, color="#2b5c8f", lw=2, label=f"ROC curve (AUC = {roc_auc_val:.4f})")
        axes[1, 0].plot([0, 1], [0, 1], color="grey", linestyle="--")
        axes[1, 0].set_xlim([0.0, 1.0])
        axes[1, 0].set_ylim([0.0, 1.05])
        axes[1, 0].set_xlabel("False Positive Rate")
        axes[1, 0].set_ylabel("True Positive Rate (Recall)")
        axes[1, 0].set_title("Receiver Operating Characteristic (ROC)", fontsize=12)
        axes[1, 0].legend(loc="lower right")

    # 4. Precision-Recall Curve
    if scores is not None and len(np.unique(y_true)) > 1:
        p_vals, r_vals, _ = precision_recall_curve(y_true, scores)
        pr_auc_val = auc(r_vals, p_vals)
        axes[1, 1].plot(r_vals, p_vals, color="#d9534f", lw=2, label=f"PR curve (AUC = {pr_auc_val:.4f})")
        base_rate = np.mean(y_true == 1)
        axes[1, 1].axhline(y=base_rate, color="grey", linestyle="--", label=f"Random Prior ({base_rate:.3f})")
        axes[1, 1].set_xlim([0.0, 1.0])
        axes[1, 1].set_ylim([0.0, 1.05])
        axes[1, 1].set_xlabel("Recall")
        axes[1, 1].set_ylabel("Precision")
        axes[1, 1].set_title("Precision-Recall Curve", fontsize=12)
        axes[1, 1].legend(loc="lower left")

    plt.tight_layout()
    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_p, dpi=150)
        logger.info("Saved evaluation plots", path=str(out_p))
    plt.close()
