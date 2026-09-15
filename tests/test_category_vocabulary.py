"""
Unit Tests for Category Vocabulary and Schema Alignment (tests/test_category_vocabulary.py).
Kiểm tra tính đồng bộ 100% giữa OneHotEncoder categories, FIELD_CONSTRAINTS,
Pydantic Schemas (chặn HTTP 422 khi gặp category lạ), và 14 hồ sơ mẫu /queue.
"""

import os
import sys
import joblib
import pytest
from fastapi.testclient import TestClient
from api.main import app, get_loan_queue
from api.schemas import LoanApplicationInput
from src.decision import FIELD_CONSTRAINTS
from src.preprocessing import VietnameseCreditFeatureExtractor, Winsorizer

# Thiết lập tương thích unpickle
sys.modules['__main__'].VietnameseCreditFeatureExtractor = VietnameseCreditFeatureExtractor
sys.modules['__main__'].Winsorizer = Winsorizer

client = TestClient(app)


@pytest.fixture(scope="module")
def trained_ohe_categories():
    """Trích xuất từ điển danh mục thực tế mà OneHotEncoder đã được huấn luyện."""
    prep_path = os.path.join("models", "preprocessor.joblib")
    assert os.path.exists(prep_path), "preprocessor.joblib không tồn tại!"
    prep = joblib.load(prep_path)
    ct = prep.named_steps["col_transformer"]
    cat_pipe = ct.named_transformers_["cat"]
    ohe = cat_pipe.named_steps["onehot"]
    cat_cols = ct.transformers_[1][2]
    
    vocab = {}
    for col, cats in zip(cat_cols, ohe.categories_):
        vocab[col] = set(cats.tolist())
    return vocab


def test_field_constraints_match_trained_ohe(trained_ohe_categories):
    """Kiểm tra mọi options trong FIELD_CONSTRAINTS phải khớp 100% với OneHotEncoder."""
    for field, cfg in FIELD_CONSTRAINTS.items():
        if "options" in cfg:
            assert field in trained_ohe_categories, f"Trường {field} không có trong OneHotEncoder!"
            field_options = set(cfg["options"])
            trained_cats = trained_ohe_categories[field]
            assert field_options == trained_cats, (
                f"Lệch từ điển trường '{field}':\n"
                f"  FIELD_CONSTRAINTS: {field_options}\n"
                f"  Trained OneHot:    {trained_cats}"
            )


def test_api_rejects_unknown_categories_with_422():
    """Kiểm tra Pydantic Schema chặn đứng giá trị ngoài từ điển và trả về HTTP 422."""
    valid_payload = {
        "ma_ho_so": "HS-VOCAB-01",
        "ho_ten": "Nguyễn Văn Test",
        "tuoi": 30,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 1,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
        "thu_nhap_thang_vnd": 30000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 0.0,
        "gia_tri_tai_san_dam_bao_vnd": 1000000000.0,
        "muc_dich_vay": "Vay mua nhà / đất",
        "so_tien_vay_vnd": 500000000.0,
        "thoi_han_vay_thang": 60,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 720,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 25.0
    }

    # 1. Thử giá trị "Chuyên gia / Quản lý" (không tồn tại trong từ điển huấn luyện)
    invalid_job = valid_payload.copy()
    invalid_job["loai_hinh_nghe_nghiep"] = "Chuyên gia / Quản lý"
    res = client.post("/predict", json=invalid_job)
    assert res.status_code == 422, f"Kỳ vọng 422 nhưng nhận {res.status_code}: {res.text}"

    # 2. Thử giá trị "Trung cấp / Nghề"
    invalid_edu = valid_payload.copy()
    invalid_edu["trinh_do_hoc_van"] = "Trung cấp / Nghề"
    res = client.post("/predict", json=invalid_edu)
    assert res.status_code == 422

    # 3. Thử giá trị "Vay tiêu dùng" (thiếu chữ 'sinh hoạt')
    invalid_purpose = valid_payload.copy()
    invalid_purpose["muc_dich_vay"] = "Vay tiêu dùng"
    res = client.post("/predict", json=invalid_purpose)
    assert res.status_code == 422

    # 4. Thử giá trị "Ngoại thành" (thiếu '/ Bán đô thị')
    invalid_area = valid_payload.copy()
    invalid_area["khu_vuc_sinh_song"] = "Ngoại thành"
    res = client.post("/predict", json=invalid_area)
    assert res.status_code == 422


def test_queue_profiles_are_100_percent_valid():
    """Kiểm tra toàn bộ 14 hồ sơ mẫu trong /queue phải hợp lệ 100% theo Pydantic Schema."""
    profiles = get_loan_queue()
    assert len(profiles) == 14
    for i, profile in enumerate(profiles):
        # Validate trực tiếp qua schema Pydantic
        clean_profile = {k: v for k, v in profile.items() if k != "trang_thai_so_bo"}
        validated = LoanApplicationInput(**clean_profile)
        assert validated.ma_ho_so == profile["ma_ho_so"]
        assert validated.loai_hinh_nghe_nghiep in FIELD_CONSTRAINTS["loai_hinh_nghe_nghiep"]["options"]
        assert validated.trinh_do_hoc_van in FIELD_CONSTRAINTS["trinh_do_hoc_van"]["options"]
        assert validated.muc_dich_vay in FIELD_CONSTRAINTS["muc_dich_vay"]["options"]
        assert validated.khu_vuc_sinh_song in FIELD_CONSTRAINTS["khu_vuc_sinh_song"]["options"]


def test_ui_config_options_match_trained_vocabulary(trained_ohe_categories):
    response = client.get("/config")
    assert response.status_code == 200
    fields = response.json()["fields"]
    for name, cfg in fields.items():
        if "options" in cfg:
            assert set(cfg["options"]) == trained_ohe_categories[name]
    assert response.json()["optimal_threshold"] == 0.73
