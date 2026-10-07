"""Block regressions, back up active artifacts and restore failed deployments."""
import argparse
import json
import math
import os
from pathlib import Path

from src import cloud

F1_THRESHOLD = 0.65
CURRENT = "artifacts/current/"
FILES = {"model.joblib": "models/model.joblib", "report.json": "outputs/report.json"}


def validate_f1(report):
    value = float(report["f1_score"])
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid f1_score")
    return value


def should_release(new, old=None):
    score = validate_f1(new)
    if score < F1_THRESHOLD:
        raise ValueError(f"FAILED: f1_score {score:.4f} < {F1_THRESHOLD}")
    if old is not None and score < validate_f1(old):
        print(f"BLOCKED regression: new F1={score:.4f} < current F1={old['f1_score']:.4f}")
        return False
    print(f"PASSED: new F1={score:.4f}; previous={old['f1_score'] if old else 'none'}")
    return True


def promote():
    new = json.loads(Path("outputs/report.json").read_text())
    old = None
    if cloud.exists(CURRENT + "report.json"):
        cloud.download(CURRENT + "report.json", "outputs/previous-report.json")
        old = json.loads(Path("outputs/previous-report.json").read_text())
    if not should_release(new, old):
        accepted = False
    else:
        state = {name: cloud.exists(CURRENT + name) for name in FILES}
        Path("outputs/rollback.json").write_text(json.dumps(state))
        for name, present in state.items():
            if present:
                cloud.download(CURRENT + name, Path("outputs/backup", name))
                cloud.upload(Path("outputs/backup", name), "artifacts/previous/" + name)
        cloud.upload("outputs/rollback.json", "artifacts/previous/rollback.json")
        version = os.getenv("GITHUB_SHA", new["run_id"])
        try:
            for name, path in FILES.items():
                cloud.upload(path, f"artifacts/versions/{version}/{name}")
                cloud.upload(path, CURRENT + name)
        except Exception:
            rollback()
            raise
        accepted = True
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"deploy={str(accepted).lower()}\n")
    return accepted


def rollback():
    cloud.download("artifacts/previous/rollback.json", "outputs/rollback.json")
    state = json.loads(Path("outputs/rollback.json").read_text())
    for name, present in state.items():
        if present:
            path = Path("outputs/backup", name)
            cloud.download("artifacts/previous/" + name, path)
            cloud.upload(path, CURRENT + name)
        elif cloud.exists(CURRENT + name):
            cloud.delete(CURRENT + name)
    print("Restored previous cloud artifacts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["promote", "rollback"])
    args = parser.parse_args()
    promote() if args.action == "promote" else rollback()
