"""
Integration and Unit Tests for FastAPI Loan Approval Service.
Kiểm thử các endpoints: /health, /predict với các ca hợp lệ, vi phạm validation, và giá trị biên.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Kiểm tra endpoint root trả về thông tin cấu hình hợp lệ."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "dich_vu" in data
    assert data["trang_thai"] == "Hoạt động"
    assert "nguong_toi_uu_ngan_hang" in data


def test_health_check_endpoint():
    """Kiểm tra endpoint sức khỏe mô hình."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["n_features"] > 0


def test_predict_approved_case():
    """Kiểm tra dự đoán hồ sơ khách hàng tốt đạt chuẩn phê duyệt."""
    payload = {
        "ma_ho_so": "HS-TEST-001",
        "ho_ten": "Nguyễn Hoàng Nam",
        "tuoi": 36,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 1,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
        "thu_nhap_thang_vnd": 50000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 25000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 3000000000.0,
        "muc_dich_vay": "Vay mua nhà / đất",
        "so_tien_vay_vnd": 800000000.0,
        "thoi_han_vay_thang": 120,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 780,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 20.0
    }
    response = client.post("/predict?use_optimal_threshold=false", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ma_ho_so"] == "HS-TEST-001"
    assert data["ma_ket_qua"] == 1
    assert data["ket_qua"] == "PHÊ DUYỆT KHOẢN VAY"
    assert data["xac_suat_phe_duyet"] > 50.0
    assert len(data["top_nhan_to_anh_huong"]) == 3


def test_predict_rejected_case():
    """Kiểm tra hồ sơ nợ xấu hoặc rủi ro cao bị từ chối chính xác."""
    payload = {
        "ma_ho_so": "HS-TEST-BAD",
        "ho_ten": "Trần Văn Tệ",
        "tuoi": 45,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Độc thân",
        "so_nguoi_phu_thuoc": 0,
        "trinh_do_hoc_van": "Trung học phổ thông",
        "loai_hinh_nghe_nghiep": "Kinh doanh tự do",
        "thu_nhap_thang_vnd": 12000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 0.0,
        "gia_tri_tai_san_dam_bao_vnd": 200000000.0,
        "muc_dich_vay": "Vay tiêu dùng sinh hoạt",
        "so_tien_vay_vnd": 500000000.0,
        "thoi_han_vay_thang": 36,
        "khu_vuc_sinh_song": "Nông thôn",
        "diem_tin_dung_cic": 460,
        "nhom_no_cic": "Nhóm 4 (Nghi ngờ)",
        "so_lan_tre_han_2_nam": 4,
        "so_khoan_vay_hien_tai": 5,
        "lich_su_no_xau": "Có",
        "ty_le_dti": 65.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ma_ket_qua"] == 0
    assert "TỪ CHỐI" in data["ket_qua"]
    assert data["xac_suat_phe_duyet"] < 50.0


def test_predict_hard_policy_rejection():
    """Kiểm tra quy tắc cứng: Khách hàng nhóm 4/5 nợ xấu bị từ chối chính sách tự động."""
    payload = {
        "ma_ho_so": "HS-TEST-POLICY",
        "ho_ten": "Lý Văn Xấu",
        "tuoi": 40,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 1,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Kinh doanh tự do",
        "thu_nhap_thang_vnd": 80000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 40000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 5000000000.0,
        "muc_dich_vay": "Vay sản xuất kinh doanh",
        "so_tien_vay_vnd": 500000000.0,
        "thoi_han_vay_thang": 60,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 700,
        "nhom_no_cic": "Nhóm 4 (Nghi ngờ)",
        "so_lan_tre_han_2_nam": 1,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 15.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ma_ket_qua"] == 0
    assert "VI PHẠM CHÍNH SÁCH" in data["ket_qua"]
    assert "Chính sách tín dụng" in data["khuyen_nghi_nghiep_vu"]


def test_predict_validation_error():
    """Kiểm tra khi gửi dữ liệu sai (ví dụ: tuổi < 18 hoặc thiếu thu nhập) trả về 422."""
    payload = {
        "ho_ten": "Khách hàng dưới tuổi",
        "tuoi": 15,  # Ràng buộc ge=18
        "thu_nhap_thang_vnd": -1000.0, # Ràng buộc gt=0
        "so_tien_vay_vnd": 10000000.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_reproducibility():
    """Kiểm tra mô hình đưa ra dự đoán nhất quán 100% khi chạy lại nhiều lần."""
    payload = {
        "ma_ho_so": "HS-REPRODUCIBLE",
        "ho_ten": "Lê Văn Ổn Định",
        "tuoi": 30,
        "gioi_tinh": "Nữ",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 1,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
        "thu_nhap_thang_vnd": 30000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 15000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 1500000000.0,
        "muc_dich_vay": "Vay mua ô tô",
        "so_tien_vay_vnd": 600000000.0,
        "thoi_han_vay_thang": 60,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 710,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 30.0
    }
    res1 = client.post("/predict", json=payload).json()
    res2 = client.post("/predict", json=payload).json()

    assert res1["xac_suat_phe_duyet"] == res2["xac_suat_phe_duyet"]
    assert res1["ma_ket_qua"] == res2["ma_ket_qua"]
    assert len(res1["top_nhan_to_anh_huong"]) == len(res2["top_nhan_to_anh_huong"])


def test_committee_decision_audit_endpoint(users, prime):
    assessment = users["officer"].post("/predict", json=prime).json()
    payload = {"assessment_id": assessment["request_id"], "idempotency_key": "committee-test-key",
               "final_decision": "PHÊ DUYỆT", "approved_limit_vnd": prime["so_tien_vay_vnd"], "interest_rate_pct": 8.5}
    response = users["chair"].post("/audit/committee-decision", json=payload)
    assert response.status_code == 200
    record = response.json()["audit_record"]
    assert record["is_official"] is True
    assert record["extra_metadata"]["officer_id"] == "chair"
    from src.storage import store
    assert len(store.recent_events()) == 2


def test_simulate_stress_endpoint():
    """Kiểm tra endpoint /simulate-stress tính toán kịch bản căng thẳng vĩ mô."""
    payload = {
        "application": {
            "ma_ho_so": "HS-STRESS-TEST",
            "ho_ten": "Võ Thị Chịu Tải",
            "tuoi": 33,
            "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Đã kết hôn",
            "so_nguoi_phu_thuoc": 1,
            "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
            "thu_nhap_thang_vnd": 40000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 15000000.0,
            "gia_tri_tai_san_dam_bao_vnd": 1800000000.0,
            "muc_dich_vay": "Vay mua nhà / đất",
            "so_tien_vay_vnd": 500000000.0,
            "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Nội thành / Đô thị",
            "diem_tin_dung_cic": 750,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
            "so_lan_tre_han_2_nam": 0,
            "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không",
            "ty_le_dti": 25.0
        },
        "income_drop_pct": 20.0,
        "rate_hike_pct": 3.0,
        "collateral_drop_pct": 15.0,
        "cic_drop_pts": 30
    }

    res = client.post("/simulate-stress", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "baseline" in data
    assert "stressed" in data
    assert "delta_prob" in data
    assert "khuyen_nghi_chieu_tai" in data
    assert data["baseline"]["xac_suat"] >= data["stressed"]["xac_suat"]


def test_batch_assess_endpoint():
    """Kiểm tra endpoint /queue/batch-assess thẩm định theo lô đồng thời."""
    payload = {
        "applications": [
            {
                "ma_ho_so": "HS-BATCH-01",
                "ho_ten": "Lê Văn Tốt",
                "tuoi": 32,
                "gioi_tinh": "Nam",
                "tinh_trang_hon_nhan": "Đã kết hôn",
                "so_nguoi_phu_thuoc": 1,
                "trinh_do_hoc_van": "Cao đẳng / Đại học",
                "loai_hinh_nghe_nghiep": "Cán bộ / Công chức",
                "thu_nhap_thang_vnd": 45000000.0,
                "thu_nhap_nguoi_dong_vay_vnd": 20000000.0,
                "gia_tri_tai_san_dam_bao_vnd": 2000000000.0,
                "muc_dich_vay": "Vay mua nhà / đất",
                "so_tien_vay_vnd": 500000000.0,
                "thoi_han_vay_thang": 48,
                "khu_vuc_sinh_song": "Nội thành / Đô thị",
                "diem_tin_dung_cic": 760,
                "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
                "so_lan_tre_han_2_nam": 0,
                "so_khoan_vay_hien_tai": 1,
                "lich_su_no_xau": "Không",
                "ty_le_dti": 22.0
            },
            {
                "ma_ho_so": "HS-BATCH-02",
                "ho_ten": "Hoàng Nợ Xấu",
                "tuoi": 40,
                "gioi_tinh": "Nam",
                "tinh_trang_hon_nhan": "Độc thân",
                "so_nguoi_phu_thuoc": 0,
                "trinh_do_hoc_van": "Trung học phổ thông",
                "loai_hinh_nghe_nghiep": "Kinh doanh tự do",
                "thu_nhap_thang_vnd": 15000000.0,
                "thu_nhap_nguoi_dong_vay_vnd": 0.0,
                "gia_tri_tai_san_dam_bao_vnd": 300000000.0,
                "muc_dich_vay": "Vay tiêu dùng sinh hoạt",
                "so_tien_vay_vnd": 400000000.0,
                "thoi_han_vay_thang": 36,
                "khu_vuc_sinh_song": "Nông thôn",
                "diem_tin_dung_cic": 470,
                "nhom_no_cic": "Nhóm 4 (Nghi ngờ)",
                "so_lan_tre_han_2_nam": 3,
                "so_khoan_vay_hien_tai": 3,
                "lich_su_no_xau": "Có",
                "ty_le_dti": 60.0
            }
        ],
        "use_optimal_threshold": True
    }

    res = client.post("/queue/batch-assess", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "results" in data
    summary = data["summary"]
    assert summary["tong_so_ho_so"] == 2
    assert summary["so_luong_duyet"] == 1
    assert summary["so_luong_tu_choi"] == 1
    assert summary["so_ca_vi_pham_chinh_sach"] == 1
    assert len(data["results"]) == 2


def test_edge_cases_strict_validation_rejected_with_422():
    """Kiểm tra toàn bộ ma trận Edge Cases của Lãnh đạo: age=15/75, income=-1, loan=0/-100, CIC ngoài 400-850, DTI âm/vượt 100."""
    valid_base = {
        "ma_ho_so": "HS-EDGE-VAL",
        "ho_ten": "Nguyễn Kiểm Thử",
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

    # 1. Tuổi = 15 (< 18)
    case_age_15 = valid_base.copy()
    case_age_15["tuoi"] = 15
    res = client.post("/predict", json=case_age_15)
    assert res.status_code == 422, f"Expected 422 for age=15, got {res.status_code}"
    assert "Độ tuổi" in res.json().get("message", "")

    # 2. Tuổi = 75 (> 70)
    case_age_75 = valid_base.copy()
    case_age_75["tuoi"] = 75
    res = client.post("/predict", json=case_age_75)
    assert res.status_code == 422, f"Expected 422 for age=75, got {res.status_code}"

    # 3. Thu nhập chính = -1.000.000
    case_neg_income = valid_base.copy()
    case_neg_income["thu_nhap_thang_vnd"] = -1000000.0
    res = client.post("/predict", json=case_neg_income)
    assert res.status_code == 422

    # 4. Số tiền vay = 0
    case_loan_zero = valid_base.copy()
    case_loan_zero["so_tien_vay_vnd"] = 0.0
    res = client.post("/predict", json=case_loan_zero)
    assert res.status_code == 422

    # 5. Số tiền vay âm = -100
    case_loan_neg = valid_base.copy()
    case_loan_neg["so_tien_vay_vnd"] = -100.0
    res = client.post("/predict", json=case_loan_neg)
    assert res.status_code == 422

    # 6. CIC ngoài range (350 và 900)
    case_cic_low = valid_base.copy()
    case_cic_low["diem_tin_dung_cic"] = 350
    assert client.post("/predict", json=case_cic_low).status_code == 422

    case_cic_high = valid_base.copy()
    case_cic_high["diem_tin_dung_cic"] = 900
    assert client.post("/predict", json=case_cic_high).status_code == 422

    # 7. DTI cực đoan (< 0 hoặc > 100)
    case_dti_neg = valid_base.copy()
    case_dti_neg["ty_le_dti"] = -5.0
    assert client.post("/predict", json=case_dti_neg).status_code == 422

    case_dti_excess = valid_base.copy()
    case_dti_excess["ty_le_dti"] = 150.0
    assert client.post("/predict", json=case_dti_excess).status_code == 422

    # 8. Thu nhập đồng vay và TSĐB âm
    case_co_income_neg = valid_base.copy()
    case_co_income_neg["thu_nhap_nguoi_dong_vay_vnd"] = -500000.0
    assert client.post("/predict", json=case_co_income_neg).status_code == 422

    case_collateral_neg = valid_base.copy()
    case_collateral_neg["gia_tri_tai_san_dam_bao_vnd"] = -1000.0
    assert client.post("/predict", json=case_collateral_neg).status_code == 422


def test_portfolio_stress_endpoint():
    """Kiểm tra endpoint mô phỏng Stress-testing danh mục toàn hàng đợi."""
    res = client.post("/simulate-stress/portfolio", json={"case_ids": ["all_queue"]})
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "details" in data
    summary = data["summary"]
    assert summary["total_cases"] == 14
    assert 0 <= summary["stressed_approved_count"] <= 14
    assert "stressed_npl_ratio_pct" not in summary
    assert "total_delta_expected_loss_vnd" not in summary
    assert len(data["details"]) == 14


def test_core_banking_disburse_endpoint(users, prime):
    assessment = users["officer"].post("/predict", json=prime).json()
    committee = users["chair"].post("/audit/committee-decision", json={
        "assessment_id": assessment["request_id"], "idempotency_key": "committee-core-key",
        "final_decision": "PHÊ DUYỆT", "approved_limit_vnd": prime["so_tien_vay_vnd"], "interest_rate_pct": 8.5}).json()
    payload = {"decision_id": committee["decision_id"], "account_number": "123456789", "idempotency_key": "core-test-key"}
    assert users["officer"].post("/integration/core-banking/disburse", json=payload).status_code == 403
    response = users["chair"].post("/integration/core-banking/disburse", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SIMULATED_NOT_DISBURSED"
    assert data["simulation_id"].startswith("SIM-")
    assert data["account_masked"] == "*****6789"
    repeated = users["chair"].post("/integration/core-banking/disburse", json=payload).json()
    assert repeated["simulation_id"] == data["simulation_id"]


def test_native_excel_export_queue():
    """Kiểm tra endpoint xuất file Excel .xlsx chuẩn OpenXML."""
    res = client.get("/export/excel/queue")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.headers["content-type"]
    assert res.content.startswith(b"PK")  # ZIP/OpenXML magic bytes
    assert len(res.content) > 1000

