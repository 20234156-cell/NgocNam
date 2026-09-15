"""
Unit tests for preprocessing pipeline and feature extraction.
"""

import pytest
import numpy as np
import pandas as pd
from src.feature_engineering import add_engineered_features
from src.preprocessing import build_preprocessing_pipeline, Winsorizer


def test_engineered_features_creation():
    """Kiểm tra các đặc trưng tài chính mới được tính toán chính xác."""
    sample_df = pd.DataFrame([{
        "thu_nhap_thang_vnd": 20000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 10000000.0,
        "so_tien_vay_vnd": 600000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 1200000000.0,
        "thoi_han_vay_thang": 60,
        "diem_tin_dung_cic": 720,
        "tuoi": 35,
        "ty_le_dti": 30.0,
        "so_lan_tre_han_2_nam": 0,
        "lich_su_no_xau": "Không"
    }])

    feat_df = add_engineered_features(sample_df)

    # 1. Tổng thu nhập
    assert feat_df["tong_thu_nhap_thang_vnd"].iloc[0] == 30000000.0
    # 2. LTI: 600tr / (30tr * 12) = 1.6667
    assert np.isclose(feat_df["ty_le_vay_tren_thu_nhap_nam"].iloc[0], 600e6 / (30e6 * 12))
    # 3. LTV: 600tr / 1.2 tỷ = 0.5
    assert np.isclose(feat_df["ty_le_vay_tren_tai_san_ltv"].iloc[0], 0.5)
    # 4. Phân nhóm CIC
    assert feat_df["nhom_diem_cic"].iloc[0] == "Khá (670-739)"
    # 5. Phân nhóm tuổi
    assert feat_df["nhom_tuoi"].iloc[0] == "26-35"


def test_winsorizer_capping():
    """Kiểm tra transformer Winsorizer giới hạn ngoại lai thành công."""
    arr = np.array([1, 2, 3, 4, 5, 1000]).reshape(-1, 1)
    winsor = Winsorizer(lower_quantile=0.05, upper_quantile=0.90)
    winsor.fit(arr)
    capped = winsor.transform(arr)
    
    assert capped[-1, 0] < 1000


def test_preprocessing_pipeline_transform():
    """Kiểm tra toàn bộ pipeline tiền xử lý chạy không lỗi trên mẫu dữ liệu."""
    pipeline = build_preprocessing_pipeline()

    sample_raw = pd.DataFrame([{
        "tuoi": 30,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 1.0,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
        "thu_nhap_thang_vnd": 25000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 10000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 1000000000.0,
        "muc_dich_vay": "Vay mua nhà / đất",
        "so_tien_vay_vnd": 500000000.0,
        "thoi_han_vay_thang": 60,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 700.0,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 2,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 32.0
    }])

    pipeline.fit(sample_raw)
    transformed = pipeline.transform(sample_raw)

    assert isinstance(transformed, np.ndarray)
    assert transformed.shape[0] == 1
    assert transformed.shape[1] > 20
    assert not np.isnan(transformed).any()
