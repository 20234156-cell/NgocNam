"""
Inference Consistency Test (tests/test_inference_consistency.py).
Kiểm tra tính nhất quán 100% giữa Training Pipeline, complete_pipeline.joblib,
FastAPI REST API và DecisionEngine (Probability, Decision, Risk Tier).
"""

import os
import pytest
import joblib
import pandas as pd
from fastapi.testclient import TestClient
from api.main import app
from src.decision import decision_engine
from src.preprocessing import VietnameseCreditFeatureExtractor, Winsorizer

client = TestClient(app)

# Hồ sơ thử nghiệm đối chiếu (Benchmark Profiles)
TEST_PROFILES = [
    {
        "name": "Khách hàng tốt (Prime Applicant)",
        "payload": {
            "ma_ho_so": "HS-CONSIST-01",
            "ho_ten": "Nguyễn Hoàng Nam",
            "tuoi": 36,
            "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn",
            "so_nguoi_phu_thuoc": 1,
            "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
            "thu_nhap_thang_vnd": 45000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 20000000.0,
            "gia_tri_tai_san_dam_bao_vnd": 2500000000.0,
            "muc_dich_vay": "Vay mua nhà / đất",
            "so_tien_vay_vnd": 900000000.0,
            "thoi_han_vay_thang": 120,
            "khu_vuc_sinh_song": "Nội thành / Đô thị",
            "diem_tin_dung_cic": 760,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
            "so_lan_tre_han_2_nam": 0,
            "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không",
            "ty_le_dti": 24.5
        }
    },
    {
        "name": "Khách hàng nợ xấu (Subprime / High Risk)",
        "payload": {
            "ma_ho_so": "HS-CONSIST-02",
            "ho_ten": "Trần Đình Khang",
            "tuoi": 42,
            "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Độc thân",
            "so_nguoi_phu_thuoc": 0,
            "trinh_do_hoc_van": "Trung học phổ thông",
            "loai_hinh_nghe_nghiep": "Kinh doanh tự do",
            "thu_nhap_thang_vnd": 15000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 0.0,
            "gia_tri_tai_san_dam_bao_vnd": 300000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt",
            "so_tien_vay_vnd": 600000000.0,
            "thoi_han_vay_thang": 60,
            "khu_vuc_sinh_song": "Nông thôn",
            "diem_tin_dung_cic": 520,
            "nhom_no_cic": "Nhóm 4 (Nghi ngờ)",
            "so_lan_tre_han_2_nam": 3,
            "so_khoan_vay_hien_tai": 4,
            "lich_su_no_xau": "Có",
            "ty_le_dti": 58.0
        }
    },
    {
        "name": "Khách hàng cận biên (Borderline Case)",
        "payload": {
            "ma_ho_so": "HS-CONSIST-03",
            "ho_ten": "Lê Thị Mai",
            "tuoi": 29,
            "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Đã kết hôn",
            "so_nguoi_phu_thuoc": 1,
            "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
            "thu_nhap_thang_vnd": 22000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 10000000.0,
            "gia_tri_tai_san_dam_bao_vnd": 800000000.0,
            "muc_dich_vay": "Vay mua ô tô",
            "so_tien_vay_vnd": 500000000.0,
            "thoi_han_vay_thang": 60,
            "khu_vuc_sinh_song": "Ngoại thành / Bán đô thị",
            "diem_tin_dung_cic": 650,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
            "so_lan_tre_han_2_nam": 1,
            "so_khoan_vay_hien_tai": 2,
            "lich_su_no_xau": "Không",
            "ty_le_dti": 39.0
        }
    }
]


@pytest.fixture(scope="module")
def complete_pipeline():
    pipeline_path = os.path.join("models", "complete_pipeline.joblib")
    assert os.path.exists(pipeline_path), "complete_pipeline.joblib không tồn tại!"
    return joblib.load(pipeline_path)


@pytest.mark.parametrize("profile", TEST_PROFILES)
def test_inference_pipeline_vs_api_consistency(profile, complete_pipeline):
    """
    Kiểm tra cùng một input, xác suất, quyết định và mức rủi ro
    từ complete_pipeline và API phản hồi phải đồng nhất tuyệt đối.
    """
    payload = profile["payload"]

    # 1. Dự đoán trực tiếp qua complete_pipeline + DecisionEngine
    df_raw = pd.DataFrame([payload])
    df_features = df_raw.drop(columns=["ma_ho_so", "ho_ten"], errors="ignore")
    pipeline_prob = float(complete_pipeline.predict_proba(df_features)[0, 1])
    
    decision_direct = decision_engine.evaluate(
        prob_approved=pipeline_prob,
        application_data=payload,
        use_optimal_threshold=True
    )

    # 2. Gọi qua API /predict
    response = client.post("/predict?use_optimal_threshold=true", json=payload)
    assert response.status_code == 200, f"API error: {response.text}"
    api_res = response.json()

    # 3. So sánh tính nhất quán
    # A. Xác suất dự đoán phải khớp (chính xác đến 2 chữ số %)
    expected_prob_pct = round(pipeline_prob * 100, 2)
    assert abs(api_res["xac_suat_phe_duyet"] - expected_prob_pct) < 0.05, (
        f"Lệch xác suất: Pipeline={expected_prob_pct}%, API={api_res['xac_suat_phe_duyet']}%"
    )

    # B. Mã kết quả (0/1) phải giống hệt
    assert api_res["ma_ket_qua"] == decision_direct["is_approved"], (
        f"Lệch mã quyết định: Pipeline={decision_direct['is_approved']}, API={api_res['ma_ket_qua']}"
    )

    # C. Quyết định (Approved/Rejected) phải giống hệt
    assert api_res["ket_qua"] == decision_direct["ket_qua"]

    # D. Mức độ rủi ro (Risk Tier) phải giống hệt
    assert api_res["muc_do_rui_ro"] == decision_direct["muc_do_rui_ro"]

    # E. Ngưỡng quyết định phải giống hệt
    assert api_res["nguong_quyet_dinh"] == decision_direct["nguong_quyet_dinh"]
