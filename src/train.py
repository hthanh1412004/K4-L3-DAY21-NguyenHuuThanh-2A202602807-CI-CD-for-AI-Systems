"""Train Adult income models with MLflow tracking and evaluation bonuses."""
import argparse
import json
import os
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

F1_THRESHOLD = 0.65
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
FEATURE_NAMES = [
    "age", "workclass", "education_num", "marital_status", "occupation",
    "relationship", "sex", "capital_gain", "capital_loss", "hours_per_week",
]


def read_data(path):
    df = pd.read_csv(path)
    if set(df.columns) != set(FEATURE_NAMES + ["target"]):
        raise ValueError(f"Invalid Adult schema: {path}")
    if df.empty or not df["target"].isin([0, 1]).all():
        raise ValueError("Expected nonempty data with binary target")
    if not np.isfinite(df[FEATURE_NAMES].to_numpy(dtype=float)).all():
        raise ValueError("Features must contain finite numeric values")
    return df


def check_drift(df):
    ratio = float(df["target"].mean())
    drift = abs(ratio - 0.248) > 0.05
    print(f"Positive class: {ratio:.2%}; reference: 24.8%")
    if drift:
        print("WARNING: DATA DRIFT exceeds 5 percentage points!")
    return ratio, drift


def train(params: dict, data_path="data/train_batch1.csv", eval_path="data/holdout.csv",
          output_dir="outputs", model_dir="models", run_name=None) -> float:
    df_train, df_eval = read_data(data_path), read_data(eval_path)
    ratio, drift = check_drift(df_train)
    X_train, y_train = df_train[FEATURE_NAMES], df_train["target"]
    X_eval, y_eval = df_eval[FEATURE_NAMES], df_eval["target"]
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI") or "sqlite:///mlflow.db")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "adult-income")
    if mlflow.get_experiment_by_name(experiment_name) is None:
        root = os.getenv("MLFLOW_ARTIFACT_ROOT")
        mlflow.create_experiment(experiment_name, artifact_location=Path(root).resolve().as_uri() if root else None)
    mlflow.set_experiment(experiment_name)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        model = GradientBoostingClassifier(**params, random_state=42)
        model.fit(X_train, y_train)
        probs = model.predict_proba(X_eval)[:, 1]
        sweep = [{"threshold": round(float(t), 2),
                  "f1_score": float(f1_score(y_eval, probs >= t, zero_division=0))}
                 for t in np.round(np.arange(0.1, 0.901, 0.05), 2)]
        best = max(sweep, key=lambda row: (row["f1_score"], -abs(row["threshold"] - 0.5)))
        model.decision_threshold_ = best["threshold"]
        preds = (probs >= model.decision_threshold_).astype(int)
        f1 = float(f1_score(y_eval, preds, zero_division=0))
        default_f1 = float(f1_score(y_eval, model.predict(X_eval), zero_division=0))
        acc = float(accuracy_score(y_eval, preds))
        report = {
            "f1_score": f1, "accuracy": acc, "f1_default": default_f1,
            "accuracy_default": float(accuracy_score(y_eval, model.predict(X_eval))),
            "best_f1_score": f1, "best_threshold": model.decision_threshold_,
            "positive_class_ratio": ratio, "data_drift_warning": drift,
            "train_rows": len(df_train), "eval_rows": len(df_eval), "params": params,
            "threshold_sweep": sweep, "run_id": run.info.run_id,
            "git_sha": os.getenv("GITHUB_SHA"),
            "evaluation_note": "Threshold selected on holdout per lab; metrics are selection estimates, not an untouched test score.",
        }
        Path(output_dir, "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        detail = ("Confusion matrix (rows=true, columns=predicted; labels=0,1):\n"
                  + str(confusion_matrix(y_eval, preds, labels=[0, 1])) + "\n\n"
                  + classification_report(y_eval, preds, labels=[0, 1],
                                          target_names=["thu_nhap_thap", "thu_nhap_cao"], zero_division=0))
        Path(output_dir, "detail.txt").write_text(detail, encoding="utf-8")
        joblib.dump(model, Path(model_dir, "model.joblib"))
        mlflow.log_metrics({"f1_score": f1, "accuracy": acc, "f1_default": default_f1,
                            "best_threshold": model.decision_threshold_, "best_f1_score": f1,
                            "positive_class_ratio": ratio})
        mlflow.log_param("decision_threshold", model.decision_threshold_)
        mlflow.sklearn.log_model(model, "model", input_example=X_eval.iloc[:1])
        mlflow.log_artifacts(output_dir, "evaluation")
        print(f"F1: {f1:.4f} | Accuracy: {acc:.4f} | Threshold: {model.decision_threshold_:.2f} | F1@0.5: {default_f1:.4f}")
        print(detail)
    return f1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", default="params.yaml")
    parser.add_argument("--data", default="data/train_batch1.csv")
    parser.add_argument("--eval", default="data/holdout.csv")
    args = parser.parse_args()
    train(yaml.safe_load(Path(args.params).read_text(encoding="utf-8")), args.data, args.eval)
