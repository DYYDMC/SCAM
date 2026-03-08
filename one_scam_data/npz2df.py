#!/usr/bin/env python3
# Turn an npz into a DataFrame without hardcoding keys.
import argparse
from typing import Any

import numpy as np
import pandas as pd


def npz_to_df(npz_path: str) -> pd.DataFrame:
    z = np.load(npz_path, allow_pickle=True)
    keys = list(z.keys())
    if not keys:
        raise ValueError(f"NPZ has no keys: {npz_path}")

    lengths = {}
    for k in keys:
        arr = z[k]
        lengths[k] = int(arr.shape[0]) if arr.ndim > 0 else 1
    n_rows = max(lengths.values())

    data: dict[str, Any] = {}
    for k in keys:
        arr = z[k]
        if arr.ndim == 0:
            data[k] = [arr.item()] * n_rows
        elif arr.shape[0] == n_rows and arr.ndim == 1:
            data[k] = arr
        elif arr.shape[0] == n_rows:
            data[k] = list(arr)
        else:
            data[k] = [arr] * n_rows
    return pd.DataFrame(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load any .npz into a DataFrame by discovering keys.")
    parser.add_argument("npz_path", nargs="?", default="scan_data.npz")
    args = parser.parse_args()

    df = npz_to_df(args.npz_path)
    print("keys:", df.columns.tolist())
    print("rows:", len(df))


if __name__ == "__main__":
    main()
