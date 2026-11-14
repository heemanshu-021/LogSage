"""Evaluation metrics for anomaly detection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class DetectionMetrics:
    precision: float
    recall: float
    f1: float
    auc_roc: Optional[float]
    tp: int
    fp: int
    tn: int
    fn: int

    def __str__(self) -> str:
        lines = [
            "── Anomaly Detection Metrics ──────────────────",
            f"  Precision : {self.precision:.4f}",
            f"  Recall    : {self.recall:.4f}",
            f"  F1        : {self.f1:.4f}",
        ]
        if self.auc_roc is not None:
            lines.append(f"  AUC-ROC   : {self.auc_roc:.4f}")
        lines += [
            f"  TP={self.tp}  FP={self.fp}  TN={self.tn}  FN={self.fn}",
            "────────────────────────────────────────────────",
        ]
        return "\n".join(lines)


def evaluate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: Optional[np.ndarray] = None,
) -> DetectionMetrics:
    """
    Compute anomaly detection metrics.

    Args:
        y_true:  Ground-truth binary labels (1=anomaly, 0=normal).
        y_pred:  Predicted binary labels.
        scores:  Raw anomaly scores (for AUC-ROC). Optional.

    Returns:
        DetectionMetrics dataclass.
    """
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

    auc = None
    if scores is not None and len(np.unique(y_true)) > 1:
        try:
            auc = roc_auc_score(y_true, scores)
        except Exception:
            auc = None

    return DetectionMetrics(
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        auc_roc=auc,
        tp=int(tp),
        fp=int(fp),
        tn=int(tn),
        fn=int(fn),
    )
