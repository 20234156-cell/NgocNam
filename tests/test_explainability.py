"""
Unit Tests for Explainability Module (tests/test_explainability.py).
Kiểm thử SHAP Waterfall Plot, làm sạch tên biến tiếng Việt, và kiểm chứng toán học không gian Log-odds vs Probability.
"""

import pytest
import numpy as np
import pandas as pd
import joblib
import matplotlib.figure
from src.explainability import (
    get_clean_feature_names,
    create_shap_waterfall_figure,
    extract_top_shap_reasons
)
from src.decision import decision_engine


def test_get_clean_feature_names():
    """Kiểm tra làm sạch tiền tố kỹ thuật sang tiếng Việt chuẩn ngân hàng."""
    raw_names = [
        "num__diem_tin_dung_cic",
        "num__so_lan_tre_han_2_nam",
        "cat__nhom_no_cic_Nhóm 1 (Đủ tiêu chuẩn)",
        "cat__lich_su_no_xau_Không",
        "cat__loai_hinh_nghe_nghiep_Nhân viên văn phòng"
    ]
    clean = get_clean_feature_names(raw_names)
    assert clean[0] == "Điểm tín dụng CIC"
    assert clean[1] == "Số lần trễ hạn (2 năm)"
    assert clean[2] == "CIC: Nhóm 1 (Đủ tiêu chuẩn)"
    assert clean[3] == "Nợ xấu: Không"
    assert clean[4] == "Nghề nghiệp: Nhân viên văn phòng"


def test_shap_waterfall_math_and_figure():
    """Kiểm tra sinh biểu đồ Waterfall và ánh xạ chính xác từ Log-odds sang Xác suất."""
    decision_engine.ensure_artifacts_loaded()
    explainer = decision_engine.tree_explainer
    pipeline = decision_engine.complete_pipeline

    sample_app = {
        "ma_ho_so": "HS-SHAP-TEST",
        "ho_ten": "Trần Thử Nghiệm",
        "tuoi": 35,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 1,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
        "thu_nhap_thang_vnd": 40000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 15000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 2000000000.0,
        "muc_dich_vay": "Vay mua nhà / đất",
        "so_tien_vay_vnd": 800000000.0,
        "thoi_han_vay_thang": 120,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 750,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 25.0
    }

    result = decision_engine.assess_application(
        application_data=sample_app,
        use_optimal_threshold=True,
        client_source="unit_test"
    )

    shap_vals = result["shap_values"]
    X_prep = result["X_prep"][0]
    names = result["feature_names"]

    # Tạo biểu đồ Waterfall
    fig, exp_val, fx_log_odds, p_map = create_shap_waterfall_figure(
        explainer=explainer,
        shap_values_row=shap_vals,
        X_prep_row=X_prep,
        feature_names=names,
        max_display=8
    )

    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(exp_val, float)
    assert isinstance(fx_log_odds, float)
    assert 0.0 <= p_map <= 1.0

    # Kiểm chứng toán học: Sigmoid(f(x)) khớp với predict_proba đến 1e-5
    actual_prob = result["prob_approved"]
    assert abs(p_map - actual_prob) < 1e-5
    assert abs(p_map - (1.0 / (1.0 + np.exp(-fx_log_odds)))) < 1e-7
