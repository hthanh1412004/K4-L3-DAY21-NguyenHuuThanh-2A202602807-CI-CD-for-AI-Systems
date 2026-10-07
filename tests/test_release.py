import json
from pathlib import Path
import pytest
from src import release


@pytest.mark.parametrize("new,old,expected", [(0.7, None, True), (0.7, 0.7, True), (0.7, 0.8, False)])
def test_release_comparison(new, old, expected):
    assert release.should_release({"f1_score": new}, {"f1_score": old} if old else None) is expected


@pytest.mark.parametrize("f1", [0.64, float("nan"), float("inf"), 1.1, -0.1])
def test_quality_gate_rejects_invalid_or_low_f1(f1):
    with pytest.raises(ValueError):
        release.should_release({"f1_score": f1})


def mock_storage(monkeypatch, objects):
    monkeypatch.setattr(release.cloud, "exists", lambda key: key in objects)
    def download(key, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(objects[key])
    monkeypatch.setattr(release.cloud, "download", download)
    monkeypatch.setattr(release.cloud, "upload", lambda path, key: objects.__setitem__(key, Path(path).read_bytes()))
    monkeypatch.setattr(release.cloud, "delete", lambda key: objects.pop(key))


def make_candidate(tmp_path, monkeypatch, score):
    monkeypatch.chdir(tmp_path)
    Path("outputs").mkdir()
    Path("models").mkdir()
    Path("outputs/report.json").write_text(json.dumps({"f1_score": score, "run_id": "test"}))
    Path("models/model.joblib").write_bytes(b"new-model")


def test_regression_does_not_touch_production(tmp_path, monkeypatch):
    make_candidate(tmp_path, monkeypatch, 0.7)
    objects = {release.CURRENT + "report.json": b'{"f1_score": 0.8}',
               release.CURRENT + "model.joblib": b"old-model"}
    before = objects.copy()
    mock_storage(monkeypatch, objects)
    assert release.promote() is False
    assert objects == before


@pytest.mark.parametrize("first_release", [False, True])
def test_promote_and_rollback(tmp_path, monkeypatch, first_release):
    make_candidate(tmp_path, monkeypatch, 0.8)
    objects = {} if first_release else {
        release.CURRENT + "report.json": b'{"f1_score": 0.7}',
        release.CURRENT + "model.joblib": b"old-model"}
    before = objects.copy()
    mock_storage(monkeypatch, objects)
    assert release.promote() is True
    assert objects[release.CURRENT + "model.joblib"] == b"new-model"
    release.rollback()
    assert {k: v for k, v in objects.items() if k.startswith(release.CURRENT)} == before


def test_partial_upload_failure_restores_matching_model_and_report(tmp_path, monkeypatch):
    make_candidate(tmp_path, monkeypatch, 0.8)
    objects = {release.CURRENT + "report.json": b'{"f1_score": 0.7}',
               release.CURRENT + "model.joblib": b"old-model"}
    before = objects.copy()
    mock_storage(monkeypatch, objects)
    original_upload = release.cloud.upload
    def fail_new_report(path, key):
        if key == release.CURRENT + "report.json" and str(path) == "outputs/report.json":
            raise OSError("Simulated interrupted upload")
        original_upload(path, key)
    monkeypatch.setattr(release.cloud, "upload", fail_new_report)
    with pytest.raises(OSError, match="interrupted"):
        release.promote()
    assert {k: v for k, v in objects.items() if k.startswith(release.CURRENT)} == before
