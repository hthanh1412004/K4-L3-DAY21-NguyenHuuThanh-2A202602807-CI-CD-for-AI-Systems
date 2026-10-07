"""Reproduce three MLflow runs and local step-2/step-3 comparison."""
import json
import shutil
from pathlib import Path

import pandas as pd
import yaml

from append_batch import append_batch
from src.train import train


def main():
    if len(pd.read_csv("data/train_batch1.csv")) != 22361:
        raise ValueError("Experiments require the original 22361-row batch1; restore its DVC version first")
    evidence = Path("nop-bai/ket-qua")
    evidence.mkdir(parents=True, exist_ok=True)
    configs = [
        {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3},
        {"n_estimators": 50, "learning_rate": 0.05, "max_depth": 2},
        {"n_estimators": 200, "learning_rate": 0.1, "max_depth": 5},
    ]
    reports = []
    for i, params in enumerate(configs, 1):
        train(params, output_dir=f"outputs/experiment-{i}", model_dir=f"models/experiment-{i}",
              run_name=f"experiment-{i}-batch1")
        report = json.loads(Path(f"outputs/experiment-{i}/report.json").read_text())
        reports.append(report)
    best_index = max(range(len(reports)), key=lambda i: reports[i]["f1_score"])
    best = reports[best_index]
    Path("params.yaml").write_text(yaml.safe_dump(best["params"], sort_keys=False))
    for name in ("report.json", "detail.txt"):
        shutil.copyfile(f"outputs/experiment-{best_index + 1}/{name}", evidence / f"buoc-2-{name}")
    # Use a separate copy, keeping batch1 ready for the first cloud CI run.
    combined = Path("outputs/train_combined.csv")
    shutil.copyfile("data/train_batch1.csv", combined)
    append_batch(combined)
    train(best["params"], data_path=str(combined), output_dir="outputs/step3",
          model_dir="models/step3", run_name="continuous-training-batch1-plus-batch2")
    for name in ("report.json", "detail.txt"):
        shutil.copyfile(f"outputs/step3/{name}", evidence / f"buoc-3-{name}")
    (evidence / "experiments.json").write_text(json.dumps(reports, indent=2))
    # The local API serves the step-2 candidate, matching the initial DVC version.
    Path("models").mkdir(exist_ok=True)
    shutil.copyfile(f"models/experiment-{best_index + 1}/model.joblib", "models/model.joblib")
    shutil.copyfile(evidence / "buoc-2-report.json", "outputs/report.json")
    shutil.copyfile(evidence / "buoc-2-detail.txt", "outputs/detail.txt")
    print("Best parameters:", best["params"])


if __name__ == "__main__":
    main()
