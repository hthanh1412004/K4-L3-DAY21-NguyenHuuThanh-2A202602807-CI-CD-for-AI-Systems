import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from src.serve import app


class ThresholdModel:
    decision_threshold_ = 0.35

    def predict_proba(self, X):
        return np.array([[0.6, 0.4]])


@pytest.fixture
def client(tmp_path, monkeypatch):
    path = tmp_path / "model.joblib"
    joblib.dump(ThresholdModel(), path)
    monkeypatch.setenv("MODEL_PATH", str(path))
    monkeypatch.delenv("ARTIFACT_BUCKET", raising=False)
    with TestClient(app) as client:
        yield client


def test_api_health_and_threshold(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    response = client.post("/score", json={"features": [28, 2, 14, 2, 11, 0, 1, 0, 0, 45]})
    assert response.status_code == 200
    assert response.json() == {"prediction": 1, "label": "thu_nhap_cao"}


def test_api_rejects_wrong_feature_count(client):
    assert client.post("/score", json={"features": [1, 2]}).status_code == 400
    assert client.post("/score", json={"features": ["bad"] * 10}).status_code == 422
