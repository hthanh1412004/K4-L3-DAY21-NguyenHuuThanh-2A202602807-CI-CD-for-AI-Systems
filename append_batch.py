"""Append the lab's second batch once, without duplicating it on reruns."""
import pandas as pd


def append_batch(train_path="data/train_batch1.csv", batch_path="data/train_batch2.csv"):
    df_train, df_new = pd.read_csv(train_path), pd.read_csv(batch_path)
    if list(df_train.columns) != list(df_new.columns):
        raise ValueError("Batch schemas do not match")
    if len(df_train) == 2 * len(df_new) and df_train.iloc[len(df_new):].reset_index(drop=True).equals(df_new):
        print("Batch 2 already appended; no change.")
        return len(df_train)
    if len(df_train) != len(df_new):
        raise ValueError("Unexpected batch sizes; refusing to append twice")
    updated = pd.concat([df_train, df_new], ignore_index=True)
    updated.to_csv(train_path, index=False)
    print(f"Cap nhat du lieu: {len(df_train)} -> {len(updated)} mau")
    return len(updated)


if __name__ == "__main__":
    append_batch()
