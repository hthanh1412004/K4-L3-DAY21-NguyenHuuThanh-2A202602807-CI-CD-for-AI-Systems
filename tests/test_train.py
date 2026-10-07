import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import f1_score

from src.train import FEATURE_NAMES, check_drift, train


def _make_temp_data(tmp_path):
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.random((200, len(FEATURE_NAMES))), columns=FEATURE_NAMES)
    df["target"] = rng.integers(0, 2, size=200)
    train_path, eval_path = tmp_path / "train.csv", tmp_path / "holdout.csv"
    df.iloc[:160].to_csv(train_path, index=False)
    df.iloc[160:].to_csv(eval_path, index=False)
    return str(train_path), str(eval_path)


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    root = tmp_path_factory.mktemp("train")
    train_path, eval_path = _make_temp_data(root)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{(root / 'mlflow.db').as_posix()}")
        monkeypatch.setenv("MLFLOW_ARTIFACT_ROOT", str(root / "mlartifacts"))
        result = train({"n_estimators": 10, "learning_rate": 0.1, "max_depth": 2},
                       train_path, eval_path, root / "outputs", root / "models")
    return root, result, eval_path


def test_train_returns_float(trained):
    assert isinstance(trained[1], float)
    assert 0 <= trained[1] <= 1


def test_report_file_created(trained):
    report = json.loads((trained[0] / "outputs/report.json").read_text())
    assert report["f1_score"] == trained[1]
    assert 0 <= report["accuracy"] <= 1
    assert len(report["threshold_sweep"]) == 17
    assert report["best_f1_score"] >= report["f1_default"]
    assert report["train_rows"] == 160 and report["eval_rows"] == 40
    assert "precision" in (trained[0] / "outputs/detail.txt").read_text()


def test_model_file_created(trained):
    model = joblib.load(trained[0] / "models/model.joblib")
    df = pd.read_csv(trained[2])
    preds = model.predict_proba(df[FEATURE_NAMES])[:, 1] >= model.decision_threshold_
    assert f1_score(df["target"], preds) == trained[1]
    assert list(model.feature_names_in_) == FEATURE_NAMES


def test_drift_warning_and_reference(capsys):
    assert check_drift(pd.DataFrame({"target": [1] * 248 + [0] * 752})) == (0.248, False)
    assert check_drift(pd.DataFrame({"target": [1] * 400 + [0] * 600})) == (0.4, True)
    assert "WARNING: DATA DRIFT" in capsys.readouterr().out
