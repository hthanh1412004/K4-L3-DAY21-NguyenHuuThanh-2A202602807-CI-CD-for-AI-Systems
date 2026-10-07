"""FastAPI inference using the decision threshold saved during evaluation."""
from contextlib import asynccontextmanager
import math
import os
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

FEATURE_NAMES = [
    "age", "workclass", "education_num", "marital_status", "occupation",
    "relationship", "sex", "capital_gain", "capital_loss", "hours_per_week",
]
MODEL_KEY = "artifacts/current/model.joblib"


def download_model():
    path = Path(os.getenv("MODEL_PATH", "models/model.joblib")).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.getenv("ARTIFACT_BUCKET"):
        try:
            from src.cloud import download
        except ModuleNotFoundError:
            from cloud import download
        download(MODEL_KEY, path)
        print("Model downloaded from cloud storage.")
    elif not path.is_file():
        raise RuntimeError("Set ARTIFACT_BUCKET or provide a local MODEL_PATH")
    return path


@asynccontextmanager
async def lifespan(app):
    app.state.model = joblib.load(download_model())
    yield


app = FastAPI(lifespan=lifespan)


class ScoreRequest(BaseModel):
    features: list[float]


@app.get("/healthz")
def healthz():
    if getattr(app.state, "model", None) is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    if len(req.features) != 10 or not all(math.isfinite(x) for x in req.features):
        raise HTTPException(status_code=400, detail="Expected 10 finite features (adult income)")
    model = getattr(app.state, "model", None)
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    X = pd.DataFrame([req.features], columns=FEATURE_NAMES)
    pred = int(model.predict_proba(X)[0, 1] >= getattr(model, "decision_threshold_", 0.5))
    return {"prediction": pred, "label": "thu_nhap_cao" if pred else "thu_nhap_thap"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
