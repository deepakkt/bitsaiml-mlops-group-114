"""Generate EDA artifacts for the heart disease dataset."""

from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import seaborn as sns  # noqa: E402

from .data import FEATURE_COLUMNS, NUMERIC_FEATURES, TARGET_COLUMN, load_processed


def _ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_target_balance(df, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(4, 3))
    sns.countplot(data=df, x=TARGET_COLUMN, ax=ax, palette="viridis")
    ax.set_title("Target Balance (0=no disease, 1=disease)")
    ax.set_xlabel("Target")
    ax.set_ylabel("Count")
    output_path = output_dir / "target_balance.png"
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_numeric_distributions(df, output_dir: Path) -> Path:
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    for ax, col in zip(axes.flat, NUMERIC_FEATURES):
        sns.histplot(data=df, x=col, hue=TARGET_COLUMN, multiple="stack", kde=False, ax=ax)
        ax.set_title(col)
    fig.tight_layout()
    output_path = output_dir / "numeric_distributions.png"
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_correlation_heatmap(df, output_dir: Path) -> Path:
    corr = df[NUMERIC_FEATURES + [TARGET_COLUMN]].corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, mask=mask, annot=True, cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Correlation Heatmap")
    output_path = output_dir / "correlation_heatmap.png"
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_missingness(df, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(df[FEATURE_COLUMNS].isna(), cbar=False, yticklabels=False, ax=ax)
    ax.set_title("Feature Missingness")
    output_path = output_dir / "missingness.png"
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def run_eda(output_dir: Path | None = None) -> List[Path]:
    """Generate EDA figures and return their paths."""
    figures_dir = _ensure_output_dir(output_dir or Path("report/figures"))
    df = load_processed()
    generated = [
        plot_target_balance(df, figures_dir),
        plot_numeric_distributions(df, figures_dir),
        plot_correlation_heatmap(df, figures_dir),
        plot_missingness(df, figures_dir),
    ]
    return generated


def main() -> None:
    generated = run_eda()
    print("EDA artifacts generated:")
    for path in generated:
        print(f" - {path}")


if __name__ == "__main__":
    main()
