"""
Unit Tests for Credit Dataset Integrity (tests/test_data.py).
Kiểm tra tính toàn vẹn của tập dữ liệu raw và các phân vùng train/val/test.
"""

import os
import pandas as pd
import pytest


def test_processed_splits_exist():
    """Kiểm tra sự tồn tại của các tập train, val, test."""
    for split in ["train.csv", "val.csv", "test.csv"]:
        path = os.path.join("data", "processed", split)
        assert os.path.exists(path), f"Thiếu phân vùng dữ liệu: {path}"


def test_processed_splits_leakage_and_shape():
    """Kiểm tra kích thước các tập và không có trùng lặp ID giữa train, val và test."""
    train_df = pd.read_csv("data/processed/train.csv", encoding="utf-8-sig")
    val_df = pd.read_csv("data/processed/val.csv", encoding="utf-8-sig")
    test_df = pd.read_csv("data/processed/test.csv", encoding="utf-8-sig")

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    # Kiểm tra nhãn mục tiêu tồn tại và không rỗng
    target_col = "phe_duyet_khoan_vay"
    for df, name in [(train_df, "train"), (val_df, "val"), (test_df, "test")]:
        assert target_col in df.columns, f"Thiếu cột mục tiêu trong tập {name}"
        assert df[target_col].isnull().sum() == 0, f"Cột mục tiêu có null trong tập {name}"
        assert set(df[target_col].unique()).issubset({0, 1}), f"Giá trị nhãn không hợp lệ trong tập {name}"

    # Kiểm tra không có rò rỉ mã hồ sơ (ID leakage) giữa các tập
    if "ma_ho_so" in train_df.columns:
        train_ids = set(train_df["ma_ho_so"])
        val_ids = set(val_df["ma_ho_so"])
        test_ids = set(test_df["ma_ho_so"])

        assert len(train_ids.intersection(val_ids)) == 0, "Rò rỉ ID giữa train và val!"
        assert len(train_ids.intersection(test_ids)) == 0, "Rò rỉ ID giữa train và test!"
        assert len(val_ids.intersection(test_ids)) == 0, "Rò rỉ ID giữa val và test!"
