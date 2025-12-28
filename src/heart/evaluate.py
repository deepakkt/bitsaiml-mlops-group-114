"""Evaluation helpers for model metrics and plotting."""

from __future__ import annotations

from typing import Dict, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

# Use headless backend for CI/servers
matplotlib.use("Agg")


def compute_classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray
) -> Dict[str, float]:
    """Compute standard binary classification metrics."""
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
    }
    try:
        metrics["roc_auc"] = roc_auc_score(y_true, y_proba)
    except ValueError:
        metrics["roc_auc"] = 0.5
    return metrics


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray):
    """Return a matplotlib figure with the confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(4, 3))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    return fig


def plot_roc_curve(y_true: np.ndarray, y_proba: np.ndarray):
    """Return a matplotlib figure with the ROC curve."""
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot(fpr, tpr, label="ROC curve")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Chance")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.4)
    return fig


def evaluate_predictions(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """
    Compute metrics and return figures for downstream logging.

    Returns a tuple of (metrics_dict, figures_dict).
    """
    metrics = compute_classification_metrics(y_true, y_pred, y_proba)
    figures = {
        "confusion_matrix": plot_confusion_matrix(y_true, y_pred),
        "roc_curve": plot_roc_curve(y_true, y_proba),
    }
    return metrics, figures
