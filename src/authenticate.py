"""Export cloud credentials safely from a secret to GitHub Actions environment."""
import json
import os
from pathlib import Path


def authenticate():
    raw = os.environ["STORAGE_CREDENTIALS"]
    if not raw:
        raise ValueError("STORAGE_CREDENTIALS is missing")
    provider = os.getenv("CLOUD_PROVIDER", "gcp")
    if provider == "gcp":
        json.loads(raw)
        path = Path(os.environ["RUNNER_TEMP"], "income-sa-key.json")
        path.write_text(raw, encoding="utf-8")
        path.chmod(0o600)
        values = {"GOOGLE_APPLICATION_CREDENTIALS": str(path)}
    elif provider == "aws":
        credentials = json.loads(raw)
        values = {
            "AWS_ACCESS_KEY_ID": credentials["aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": credentials["aws_secret_access_key"],
        }
        if credentials.get("aws_session_token"):
            values["AWS_SESSION_TOKEN"] = credentials["aws_session_token"]
    else:
        raise ValueError("CLOUD_PROVIDER must be gcp or aws")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
        for name, value in values.items():
            if "\n" in value or "\r" in value:
                raise ValueError("Credential environment values must be single-line")
            print(f"::add-mask::{value}")
            f.write(f"{name}={value}\n")


if __name__ == "__main__":
    authenticate()
