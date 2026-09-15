"""
Unit Tests for Decision Engine (src/decision.py).
Kiểm tra Hard Rules, Risk Tiering, Recommendation Engine và Decision Engine tổng hợp.
"""

import pytest
from src.decision import (
    FIELD_CONSTRAINTS,
    HardRulesEngine,
    RiskTierEngine,
    RecommendationEngine,
    DecisionEngine
)


def test_field_constraints_integrity():
    """Kiểm tra tính toàn vẹn của FIELD_CONSTRAINTS."""
    required_fields = [
        "tuoi", "gioi_tinh", "tinh_trang_hon_nhan", "so_nguoi_phu_thuoc",
        "trinh_do_hoc_van", "loai_hinh_nghe_nghiep", "thu_nhap_thang_vnd",
        "thu_nhap_nguoi_dong_vay_vnd", "gia_tri_tai_san_dam_bao_vnd",
        "muc_dich_vay", "so_tien_vay_vnd", "thoi_han_vay_thang",
        "khu_vuc_sinh_song", "diem_tin_dung_cic", "nhom_no_cic",
        "so_lan_tre_han_2_nam", "so_khoan_vay_hien_tai", "lich_su_no_xau", "ty_le_dti"
    ]
    for field in required_fields:
        assert field in FIELD_CONSTRAINTS, f"Thiếu trường {field} trong FIELD_CONSTRAINTS"
        cfg = FIELD_CONSTRAINTS[field]
        assert "default" in cfg
        if "min" in cfg and "max" in cfg:
            assert cfg["min"] <= cfg["default"] <= cfg["max"]


def test_hard_rules_policy_rejection():
    """Kiểm tra các trường hợp vi phạm chính sách tín dụng cứng cơ bản."""
    # Ca 1: Nhóm nợ 4
    violated, reason = HardRulesEngine.check_policy({"nhom_no_cic": "Nhóm 4 (Nghi ngờ)"})
    assert violated is True
    assert "Nhóm 4" in reason

    # Ca 2: Nhóm nợ 5
    violated, reason = HardRulesEngine.check_policy({"nhom_no_cic": "Nhóm 5 (Mất vốn)"})
    assert violated is True
    assert "Nhóm 5" in reason

    # Ca 3: Có tiền sử nợ xấu và CIC < 540
    violated, reason = HardRulesEngine.check_policy({"lich_su_no_xau": "Có", "diem_tin_dung_cic": 510})
    assert violated is True
    assert "540" in reason

    # Ca 4: Điểm CIC < 450 (Hạng 9-10 rủi ro rất cao) bị knockout đồng bộ với data_generator
    violated, reason = HardRulesEngine.check_policy({"diem_tin_dung_cic": 430})
    assert violated is True
    assert "450" in reason

    # Ca 5: Xử lý an toàn khi diem_tin_dung_cic là None tường minh (không văng TypeError)
    violated, reason = HardRulesEngine.check_policy({"lich_su_no_xau": "Có", "diem_tin_dung_cic": None})
    assert isinstance(violated, bool)

    # Ca 6: Hồ sơ chuẩn - Không vi phạm
    violated, reason = HardRulesEngine.check_policy({
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "lich_su_no_xau": "Không",
        "diem_tin_dung_cic": 720
    })
    assert violated is False
    assert reason is None


def test_hard_rules_nhom_3_rejection():
    """Bước 9: Kiểm tra Nhóm 3 (Dưới tiêu chuẩn) bị chặn cứng đồng bộ với Nhóm 4, 5."""
    for nhom in ["Nhóm 3 (Dưới tiêu chuẩn)", "Nhóm 4 (Nghi ngờ)", "Nhóm 5 (Mất vốn)"]:
        r = HardRulesEngine.evaluate({"nhom_no_hien_tai": nhom})
        assert r["violated"] is True
        violated, reason = HardRulesEngine.check_policy({"nhom_no_cic": nhom})
        assert violated is True
        assert any(x in reason for x in ["Nhóm 3", "Nhóm 4", "Nhóm 5"])


def test_hard_rules_nhom_2_negative():
    """Bước 10: Negative test - Nhóm 2 (Cần chú ý) không bị chặn cứng."""
    r = HardRulesEngine.evaluate({
        "nhom_no_hien_tai": "Nhóm 2 (Cần chú ý)",
        "lich_su_no_xau": "Không",
        "diem_tin_dung_cic": 650
    })
    assert r["violated"] is False
    violated, reason = HardRulesEngine.check_policy({
        "nhom_no_cic": "Nhóm 2 (Cần chú ý)",
        "lich_su_no_xau": "Không",
        "diem_tin_dung_cic": 650
    })
    assert violated is False
    assert reason is None


def test_risk_tier_boundaries():
    """Kiểm tra phân tầng rủi ro tại các ngưỡng biên."""
    assert RiskTierEngine.get_risk_tier(0.85) == "Rất thấp (Hồ sơ xuất sắc)"
    assert RiskTierEngine.get_risk_tier(0.75) == "Rất thấp (Hồ sơ xuất sắc)"
    assert RiskTierEngine.get_risk_tier(0.749) == "Thấp (Hồ sơ an toàn)"
    assert RiskTierEngine.get_risk_tier(0.60) == "Thấp (Hồ sơ an toàn)"
    assert RiskTierEngine.get_risk_tier(0.599) == "Trung bình (Cần thẩm định kỹ tài sản)"
    assert RiskTierEngine.get_risk_tier(0.40) == "Trung bình (Cần thẩm định kỹ tài sản)"
    assert RiskTierEngine.get_risk_tier(0.399) == "Cao (Rủi ro vỡ nợ cao)"
    assert RiskTierEngine.get_risk_tier(0.10) == "Cao (Rủi ro vỡ nợ cao)"


def test_decision_engine_evaluation():
    """Kiểm tra quá trình ra quyết định tổng hợp của DecisionEngine."""
    engine = DecisionEngine()
    
    # Test case 1: Hồ sơ đạt chuẩn cao
    app_good = {
        "ma_ho_so": "HS-001",
        "ho_ten": "Nguyễn Văn Tốt",
        "diem_tin_dung_cic": 750,
        "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
        "lich_su_no_xau": "Không",
        "ty_le_dti": 25.0
    }
    res_good = engine.evaluate(prob_approved=0.88, application_data=app_good, threshold=0.70)
    assert res_good["is_approved"] == 1
    assert res_good["ket_qua"] == "PHÊ DUYỆT KHOẢN VAY"
    assert "ĐỦ ĐIỀU KIỆN PHÊ DUYỆT" in res_good["khuyen_nghi_nghiep_vu"]
    assert res_good["hard_rule_violated"] is False

    # Test case 2: Hồ sơ vi phạm chính sách nợ xấu (Hard Rule) dù xác suất cao
    app_policy = {
        "ma_ho_so": "HS-002",
        "ho_ten": "Trần Văn Nợ",
        "diem_tin_dung_cic": 650,
        "nhom_no_cic": "Nhóm 5 (Mất vốn)",
        "lich_su_no_xau": "Có"
    }
    res_policy = engine.evaluate(prob_approved=0.80, application_data=app_policy, threshold=0.50)
    assert res_policy["is_approved"] == 0
    assert "VI PHẠM CHÍNH SÁCH" in res_policy["ket_qua"]
    assert res_policy["hard_rule_violated"] is True
    assert "Chính sách tín dụng" in res_policy["khuyen_nghi_nghiep_vu"]
