"""
Unit Tests for Audit Logging and Compliance (tests/test_audit.py).
Kiểm tra tính toàn vẹn của Audit Trail, bảo vệ dữ liệu cá nhân (PII Minimization),
và khả năng truy nguyên nguồn gốc mô hình (Lineage & Reproducibility).
"""

import os
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from src.audit import AuditLogger, audit_logger
from src.storage import store

client = TestClient(app)


def test_audit_logger_creates_file_and_fields(tmp_path):
    """Kiểm tra AuditLogger ghi file audit.jsonl đầy đủ các trường metadata."""
    temp_dir = str(tmp_path / "logs")
    logger = AuditLogger(log_dir=temp_dir, log_filename="test_audit.jsonl")

    record = logger.log_decision(
        ma_ho_so="HS-AUDIT-001",
        prob_approved=0.885,
        threshold_applied=0.73,
        decision="PHÊ DUYỆT KHOẢN VAY",
        is_approved=1,
        risk_tier="Rất thấp (Hồ sơ xuất sắc)",
        hard_rule_violated=False,
        recommendation="Đủ điều kiện phê duyệt",
        top_shap_factors=[{"dac_trung": "Điểm CIC", "shap_value": 0.85, "chieu_huong": "Tăng duyệt"}]
    )

    # 1. Kiểm tra cấu trúc bản ghi trả về
    assert "request_id" in record
    assert "timestamp" in record
    assert "schema_version" in record
    assert record["schema_version"] == "1.2.0"
    assert record["ma_ho_so"] == "HS-AUDIT-001"
    assert record["model_version"] == "1.2.0"
    assert record["threshold_config_version"] == "1.2.0"
    assert record["decision_engine_version"] == "1.2.0"
    assert record["prob_approved"] == 0.885
    assert record["threshold"] == 0.73
    assert record["threshold_applied"] == 0.73
    assert record["decision"] == "PHÊ DUYỆT KHOẢN VAY"
    assert record["is_approved"] == 1
    assert record["risk_tier"] == "Rất thấp (Hồ sơ xuất sắc)"
    assert record["hard_rule_violated"] is False
    assert "recommendation" in record
    assert len(record["top_shap_factors"]) == 1

    # 2. Kiểm tra file jsonl thực tế
    assert os.path.exists(logger.log_file)
    with open(logger.log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        loaded = json.loads(lines[0])
        assert loaded["request_id"] == record["request_id"]
        assert loaded["ma_ho_so"] == "HS-AUDIT-001"
        assert loaded["threshold"] == 0.73


def test_audit_trail_pii_minimization(tmp_path):
    """Kiểm tra nguyên tắc PII Minimization: Không lưu các trường thông tin cá nhân (ho_ten) vào log."""
    temp_dir = str(tmp_path / "logs")
    logger = AuditLogger(log_dir=temp_dir, log_filename="pii_test_audit.jsonl")

    logger.log_decision(
        ma_ho_so="HS-PII-TEST",
        prob_approved=0.65,
        threshold_applied=0.73,
        decision="TỪ CHỐI KHOẢN VAY",
        is_approved=0,
        risk_tier="Thấp (Hồ sơ an toàn)",
        hard_rule_violated=False,
        recommendation="Khuyến nghị cân nhắc",
        top_shap_factors=[],
        application_snapshot={"ho_ten": "PII sentinel", "cccd": "secret sentinel", "account_number": "123456789", "thu_nhap_thang_vnd": 30000000, "nested": {"ho_ten": "nested PII"}}
    )

    with open(logger.log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
        # Không có trường 'ho_ten' hay các PII nhạy cảm trực tiếp
        assert "ho_ten" not in log_content
        assert "so_dien_thoai" not in log_content
        assert "cccd" not in log_content


def test_api_predict_writes_to_audit_trail(tmp_path, monkeypatch):
    """Kiểm tra gọi API /predict tự động ghi audit log qua DecisionEngine (cô lập với log sản xuất)."""
    temp_dir = str(tmp_path / "logs")
    monkeypatch.setattr(audit_logger, "log_dir", os.path.abspath(temp_dir))
    monkeypatch.setattr(audit_logger, "log_file", os.path.join(os.path.abspath(temp_dir), "audit.jsonl"))
    os.makedirs(temp_dir, exist_ok=True)

    payload = {
        "ma_ho_so": "HS-API-AUDIT",
        "ho_ten": "Nguyễn Kiểm Toán",
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
        "diem_tin_dung_cic": 740,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 25.0
    }

    response = client.post("/predict?use_optimal_threshold=true", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "request_id" in res_data
    req_id = res_data["request_id"]
    assert req_id is not None
    assert "hard_rule_violated" in res_data

    records = store.recent_events()
    record = next(r for r in records if r["request_id"] == req_id)
    assert record["ma_ho_so"] == "HS-API-AUDIT"
    assert record["model_version"] == "1.2.0"
    assert "ho_ten" not in record["application_snapshot"]
    assert not os.path.exists(audit_logger.log_file)


def test_decision_engine_assess_application_architecture(tmp_path, monkeypatch):
    """Kiểm tra luồng kiến trúc thống nhất: DecisionEngine -> (Prediction, Rules, SHAP) -> AuditLogger."""
    from src.decision import decision_engine

    temp_dir = str(tmp_path / "logs")
    monkeypatch.setattr(audit_logger, "log_dir", os.path.abspath(temp_dir))
    monkeypatch.setattr(audit_logger, "log_file", os.path.join(os.path.abspath(temp_dir), "audit.jsonl"))
    os.makedirs(temp_dir, exist_ok=True)

    sample_app = {
        "ma_ho_so": "HS-ARCH-TEST",
        "ho_ten": "Lê Demo Kiến Trúc",
        "tuoi": 40,
        "gioi_tinh": "Nam",
        "tinh_trang_hon_nhan": "Đã kết hôn",
        "so_nguoi_phu_thuoc": 2,
        "trinh_do_hoc_van": "Sau đại học",
        "loai_hinh_nghe_nghiep": "Chủ doanh nghiệp",
        "thu_nhap_thang_vnd": 80000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 20000000.0,
        "gia_tri_tai_san_dam_bao_vnd": 4000000000.0,
        "muc_dich_vay": "Vay sản xuất kinh doanh",
        "so_tien_vay_vnd": 1200000000.0,
        "thoi_han_vay_thang": 60,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 780,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 20.0
    }

    result = decision_engine.assess_application(
        application_data=sample_app,
        use_optimal_threshold=True,
        client_source="unit_test"
    )

    assert "request_id" in result
    assert result["is_approved"] == 1
    assert "top_shap_factors" in result
    assert len(result["top_shap_factors"]) > 0
    assert "audit_record" in result
    assert result["audit_record"]["model_version"] == "1.2.0"
    assert result["audit_record"]["threshold_config_version"] == "1.2.0"
    assert result["audit_record"]["decision_engine_version"] == "1.2.0"
    assert "ho_ten" not in result["audit_record"]


def test_api_predict_deduplication_within_window(tmp_path, monkeypatch):
    """Kiểm tra chống spam click: Bấm 3 lần liên tiếp chỉ ghi đúng 1 dòng audit log duy nhất."""
    temp_dir = str(tmp_path / "logs")
    monkeypatch.setattr(audit_logger, "log_dir", os.path.abspath(temp_dir))
    monkeypatch.setattr(audit_logger, "log_file", os.path.join(os.path.abspath(temp_dir), "audit.jsonl"))
    os.makedirs(temp_dir, exist_ok=True)

    payload = {
        "ma_ho_so": "HS-DEDUP-TEST-99",
        "ho_ten": "Trần Thị Kiểm Thử Chống Lặp",
        "tuoi": 28,
        "gioi_tinh": "Nữ",
        "tinh_trang_hon_nhan": "Độc thân",
        "so_nguoi_phu_thuoc": 0,
        "trinh_do_hoc_van": "Cao đẳng / Đại học",
        "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
        "thu_nhap_thang_vnd": 30000000.0,
        "thu_nhap_nguoi_dong_vay_vnd": 0.0,
        "gia_tri_tai_san_dam_bao_vnd": 1000000000.0,
        "muc_dich_vay": "Vay tiêu dùng sinh hoạt",
        "so_tien_vay_vnd": 300000000.0,
        "thoi_han_vay_thang": 36,
        "khu_vuc_sinh_song": "Nội thành / Đô thị",
        "diem_tin_dung_cic": 720,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "so_lan_tre_han_2_nam": 0,
        "so_khoan_vay_hien_tai": 1,
        "lich_su_no_xau": "Không",
        "ty_le_dti": 25.0
    }

    # Lần gọi 1: Tạo Run #1 và ghi audit
    resp1 = client.post("/predict?use_optimal_threshold=true", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["is_cached_run"] is False

    # Lần gọi 2: Trong cửa sổ 10s -> trả về cache, không ghi audit
    resp2 = client.post("/predict?use_optimal_threshold=true", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["is_cached_run"] is True
    assert data2["request_id"] == data1["request_id"]

    # Lần gọi 3: Tiếp tục trong cửa sổ 10s
    resp3 = client.post("/predict?use_optimal_threshold=true", json=payload)
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["is_cached_run"] is True

    records = store.recent_events()
    assert len(records) == 1
    assert records[0]["request_id"] == data1["request_id"]
