"""
Unit Tests for Multidimensional Fairness & Bias Audit (tests/test_fairness.py).
Kiểm thử tính toán chỉ số Disparate Impact Ratio (DIR), Equal Opportunity Difference (EOD)
trên 3 lát cắt nhân khẩu học: Giới tính, Độ tuổi (<30 vs >=30), và Khu vực cư trú.
"""

import os
import pytest
import numpy as np
import pandas as pd
import joblib

from src.explainability import (
    compute_multidimensional_fairness_audit,
    plot_multidimensional_fairness_audit
)


@pytest.fixture
def sample_fairness_data():
    """Tạo dữ liệu kiểm thử nhân khẩu học giả lập."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        "gioi_tinh": np.random.choice(["Nam", "Nữ"], size=n, p=[0.52, 0.48]),
        "tuoi": np.random.randint(18, 65, size=n),
        "khu_vuc_sinh_song": np.random.choice(
            ["Nội thành / Đô thị", "Ngoại thành / Bán đô thị", "Nông thôn"],
            size=n, p=[0.5, 0.3, 0.2]
        ),
        "phe_duyet_khoan_vay": np.random.choice([0, 1], size=n, p=[0.45, 0.55])
    })
    probs = np.random.uniform(0.05, 0.95, size=n)
    return df, probs


def test_compute_multidimensional_fairness_audit_structure(sample_fairness_data):
    """Kiểm tra cấu trúc trả về đầy đủ 3 lát cắt và các trường đo lường."""
    df, probs = sample_fairness_data
    res = compute_multidimensional_fairness_audit(df, probs, threshold=0.73)

    assert "threshold" in res
    assert res["threshold"] == 0.73
    assert "slices" in res
    assert len(res["slices"]) == 3

    dimensions = [s["dimension"] for s in res["slices"]]
    assert "Giới tính" in dimensions
    assert "Độ tuổi" in dimensions
    assert "Khu vực cư trú" in dimensions

    required_keys = [
        "dimension", "unprivileged_group", "privileged_group",
        "n_unprivileged", "n_privileged",
        "sr_unprivileged", "sr_privileged",
        "selection_rate_unprivileged_pct", "selection_rate_privileged_pct",
        "tpr_unprivileged_pct", "tpr_privileged_pct",
        "disparate_impact_ratio", "equal_opportunity_difference",
        "dir_status", "eod_status"
    ]
    for s in res["slices"]:
        for k in required_keys:
            assert k in s, f"Thiếu trường {k} trong lát cắt {s['dimension']}"


def test_fairness_values_range_and_sanity(sample_fairness_data):
    """Kiểm tra giá trị DIR và EOD nằm trong miền toán học hợp lệ."""
    df, probs = sample_fairness_data
    res = compute_multidimensional_fairness_audit(df, probs, threshold=0.73)

    for s in res["slices"]:
        dir_val = s["disparate_impact_ratio"]
        eod_val = s["equal_opportunity_difference"]
        sr_unp = s["sr_unprivileged"]
        sr_priv = s["sr_privileged"]

        assert dir_val >= 0.0, f"DIR phải không âm: {dir_val}"
        assert -1.0 <= eod_val <= 1.0, f"EOD phải trong [-1, 1]: {eod_val}"
        assert 0.0 <= sr_unp <= 1.0
        assert 0.0 <= sr_priv <= 1.0


def test_fairness_plot_generation(tmp_path, sample_fairness_data):
    """Kiểm tra sinh file biểu đồ kiểm toán công bằng đa chiều."""
    df, probs = sample_fairness_data
    res = compute_multidimensional_fairness_audit(df, probs, threshold=0.73)

    out_file = str(tmp_path / "test_fairness_plot.png")
    plot_multidimensional_fairness_audit(res, out_file)

    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 1000


def test_fairness_zero_denominator_resilience():
    """Kiểm tra khả năng chống lỗi chia cho 0 khi nhóm đối chứng hoặc ưu tiên không có mẫu."""
    df_empty = pd.DataFrame({
        "gioi_tinh": ["Nam"] * 20,
        "tuoi": [35] * 20,
        "khu_vuc_sinh_song": ["Nội thành / Đô thị"] * 20,
        "phe_duyet_khoan_vay": [1] * 20
    })
    probs = np.array([0.8] * 20)

    res = compute_multidimensional_fairness_audit(df_empty, probs, threshold=0.73)
    assert res is not None
    # Lát cắt giới tính không có nữ -> n_unprivileged = 0, dir = 0.0, không crash
    gender_slice = res["slices"][0]
    assert gender_slice["n_unprivileged"] == 0
    assert gender_slice["disparate_impact_ratio"] == 0.0
