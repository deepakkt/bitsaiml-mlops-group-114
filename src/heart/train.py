"""Model training entrypoint for the Heart Disease project."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import mlflow
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from .config import settings
from .data import FEATURE_COLUMNS, load_processed, load_sample, train_test_split_data
from .evaluate import evaluate_predictions
from .features import build_model_pipeline
from .mlflow_utils import export_model, log_figures, log_params_and_metrics, start_run


@dataclass
class ModelSpec:
    """Container describing a model search space."""

    name: str
    estimator: object
    param_grid: Dict[str, List[object]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train heart disease models with MLflow tracking.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a reduced search (fewer folds/params) suitable for CI.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split size for hold-out evaluation (default: 0.2).",
    )
    return parser.parse_args()


def load_training_dataframe() -> Tuple[object, str]:
    """Load the processed dataset, falling back to the committed sample if needed."""
    try:
        df = load_processed()
        source = "processed"
    except FileNotFoundError:
        df = load_sample()
        source = "sample"
    return df, source


def model_search_spaces(quick: bool) -> List[ModelSpec]:
    """Return the set of models and parameter grids for exploration."""
    logistic_params = {
        "model__C": [0.1, 1.0, 10.0] if not quick else [1.0],
        "model__penalty": ["l2"],
        "model__solver": ["liblinear", "lbfgs"] if not quick else ["liblinear"],
        "model__max_iter": [500],
    }

    rf_params = {
        "model__n_estimators": [150, 250] if not quick else [120],
        "model__max_depth": [None, 8, 12] if not quick else [None, 8],
        "model__min_samples_split": [2, 5],
        "model__min_samples_leaf": [1, 2],
    }

    return [
        ModelSpec(
            name="dummy",
            estimator=DummyClassifier(strategy="most_frequent"),
            param_grid={"model__strategy": ["most_frequent"]},
        ),
        ModelSpec(
            name="log_reg",
            estimator=LogisticRegression(n_jobs=1, random_state=settings.random_seed),
            param_grid=logistic_params,
        ),
        ModelSpec(
            name="random_forest",
            estimator=RandomForestClassifier(
                random_state=settings.random_seed, n_jobs=1
            ),
            param_grid=rf_params,
        ),
    ]


def save_figures_locally(figures: Dict[str, object], prefix: str) -> Dict[str, Path]:
    """Persist plots to the artifacts/plots directory for quick inspection."""
    saved_paths: Dict[str, Path] = {}
    settings.plots_dir.mkdir(parents=True, exist_ok=True)
    for name, fig in figures.items():
        path = settings.plots_dir / f"{prefix}_{name}.png"
        fig.savefig(path, bbox_inches="tight")
        saved_paths[name] = path
        fig.clf()
    return saved_paths


def train_single_model(
    spec: ModelSpec,
    X_train,
    y_train,
    X_test,
    y_test,
    cv: StratifiedKFold,
    data_source: str,
    quick: bool,
) -> Dict[str, object]:
    """Fit a model spec, evaluate on the hold-out set, and log to MLflow."""
    pipeline = build_model_pipeline(spec.estimator)
    search = GridSearchCV(
        estimator=pipeline,
        param_grid=spec.param_grid,
        cv=cv,
        scoring="roc_auc",
        n_jobs=1,
        refit=True,
    )
    search.fit(X_train, y_train)

    best_estimator = search.best_estimator_
    y_pred = best_estimator.predict(X_test)
    y_proba = best_estimator.predict_proba(X_test)[:, 1]

    metrics, figures = evaluate_predictions(y_test, y_pred, y_proba)
    metrics["best_cv_score"] = float(search.best_score_)

    run_details = {
        "best_params": search.best_params_,
        "feature_columns": FEATURE_COLUMNS,
        "data_source": data_source,
        "quick_mode": quick,
    }

    with start_run(run_name=spec.name) as run:
        log_params_and_metrics(search.best_params_, metrics)
        mlflow.log_dict(run_details, "run_details.json")
        log_figures(figures, prefix=f"{spec.name}_")
        mlflow.sklearn.log_model(best_estimator, artifact_path="model")
        run_id = run.info.run_id

    local_plots = save_figures_locally(figures, spec.name)
    for fig in figures.values():
        try:
            import matplotlib.pyplot as plt

            plt.close(fig)
        except Exception:
            pass

    return {
        "name": spec.name,
        "estimator": best_estimator,
        "metrics": metrics,
        "params": search.best_params_,
        "run_id": run_id,
        "plots": local_plots,
    }


def select_best_model(results: List[Dict[str, object]]) -> Dict[str, object]:
    """Pick the model with the highest ROC-AUC (tie-breaker: accuracy)."""
    def score_key(res):
        metrics = res["metrics"]
        return (metrics.get("roc_auc", 0.0), metrics.get("accuracy", 0.0))

    return sorted(results, key=score_key)[-1]


def write_training_summary(results: List[Dict[str, object]]) -> Path:
    """Write a JSON summary of all model runs to artifacts."""
    summary_path = Path(settings.artifacts_dir) / "training_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = []
    for res in results:
        serializable.append(
            {
                "name": res["name"],
                "metrics": res["metrics"],
                "params": res["params"],
                "run_id": res["run_id"],
                "plots": {k: str(v) for k, v in res.get("plots", {}).items()},
            }
        )
    summary_path.write_text(json.dumps(serializable, indent=2))
    return summary_path


def main() -> None:
    args = parse_args()
    df, data_source = load_training_dataframe()

    X_train, X_test, y_train, y_test = train_test_split_data(
        df, test_size=args.test_size, random_state=settings.random_seed
    )

    folds = 3 if args.quick else 5
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=settings.random_seed)

    results: List[Dict[str, object]] = []
    for spec in model_search_spaces(args.quick):
        res = train_single_model(
            spec=spec,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            cv=cv,
            data_source=data_source,
            quick=args.quick,
        )
        results.append(res)
        print(
            f"[{spec.name}] test metrics "
            + ", ".join(f"{k}={v:.3f}" for k, v in res["metrics"].items())
        )

    best = select_best_model(results)
    export_path = export_model(best["estimator"], best["run_id"], best["name"])
    summary_path = write_training_summary(results)

    print(
        f"Best model: {best['name']} (run_id={best['run_id']}) "
        f"ROC-AUC={best['metrics'].get('roc_auc', 0):.3f}"
    )
    print(f"Exported MLflow model to {export_path}")
    print(f"Training summary written to {summary_path}")


if __name__ == "__main__":
    main()
