import pandas as pd
import pytest
from append_batch import append_batch


def test_append_once(tmp_path):
    train, batch = tmp_path / "train.csv", tmp_path / "batch.csv"
    pd.DataFrame({"x": [1, 2], "target": [0, 1]}).to_csv(train, index=False)
    pd.DataFrame({"x": [3, 4], "target": [1, 0]}).to_csv(batch, index=False)
    assert append_batch(train, batch) == 4
    assert append_batch(train, batch) == 4
    assert pd.read_csv(train)["x"].tolist() == [1, 2, 3, 4]
