"""
Audit Logger: Hệ thống ghi vết kiểm toán thẩm định tín dụng (Audit Trail).
Đảm bảo tính giải trình (Auditability), truy nguyên nguồn gốc (Model Lineage & Reproducibility)
và tuân thủ bảo vệ dữ liệu cá nhân (PII Minimization).
Ghi dữ liệu có cấu trúc append-only vào logs/audit.jsonl.
"""

import os
import json
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Explicit allowlist: names, contact details, accounts, arbitrary nested data and notes
# must never enter the operational audit trail.
SNAPSHOT_FIELDS = frozenset({
    "tuoi", "gioi_tinh", "tinh_trang_hon_nhan", "so_nguoi_phu_thuoc",
    "trinh_do_hoc_van", "loai_hinh_nghe_nghiep", "thu_nhap_thang_vnd",
    "thu_nhap_nguoi_dong_vay_vnd", "gia_tri_tai_san_dam_bao_vnd", "muc_dich_vay",
    "so_tien_vay_vnd", "thoi_han_vay_thang", "khu_vuc_sinh_song", "diem_tin_dung_cic",
    "nhom_no_cic", "so_lan_tre_han_2_nam", "so_khoan_vay_hien_tai", "lich_su_no_xau", "ty_le_dti"
})
METADATA_FIELDS = frozenset({"client_source", "officer_id", "assessment_id", "decision_id"})


def safe_snapshot(data):
    return {k: v for k, v in (data or {}).items()
            if k in SNAPSHOT_FIELDS and isinstance(v, (str, int, float, bool))}


class AuditLogger:
    """Quản lý ghi và tra cứu log kiểm toán quyết định tín dụng."""

    def __init__(self, log_dir: Optional[str] = None, log_filename: str = "audit.jsonl"):
        env_dir = os.environ.get("AUDIT_LOG_DIR")
        target_dir = log_dir or env_dir or os.path.join(os.path.dirname(__file__), "..", "logs")
        self.log_dir = os.path.abspath(target_dir)
        self.log_file = os.path.join(self.log_dir, log_filename)

    def log_decision(
        self,
        ma_ho_so: str,
        prob_approved: float,
        threshold_applied: float,
        decision: str,
        is_approved: int,
        risk_tier: str,
        hard_rule_violated: bool,
        recommendation: str,
        top_shap_factors: List[Dict[str, Any]],
        request_id: Optional[str] = None,
        model_version: str = "1.2.0",
        threshold_config_version: str = "1.2.0",
        decision_engine_version: str = "1.2.0",
        schema_version: str = "1.2.0",
        application_snapshot: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        run_number: int = 1,
        triggered_by: str = "user_click",
        is_official: bool = False,
        persist: bool = True
    ) -> Dict[str, Any]:
        """
        Ghi một bản ghi kiểm toán chuẩn hóa vào logs/audit.jsonl.
        Tuân thủ nguyên tắc PII Minimization: Không lưu trực tiếp họ tên hay số điện thoại.
        """
        req_id = request_id or str(uuid.uuid4())
        thresh = round(float(threshold_applied), 4)
        prob = round(float(prob_approved), 4)

        record = {
            "schema_version": schema_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": req_id,
            "ma_ho_so": str(ma_ho_so),
            # Metadata nguồn gốc mô hình & quy tắc (Lineage & Reproducibility)
            "model_version": model_version,
            "threshold_config_version": threshold_config_version,
            "decision_engine_version": decision_engine_version,
            # Chỉ số quyết định
            "prob_approved": prob,
            "threshold": thresh,
            "threshold_applied": thresh,  # Alias tương thích ngược
            "decision": decision,
            "is_approved": int(is_approved),
            "risk_tier": risk_tier,
            "hard_rule_violated": bool(hard_rule_violated),
            "recommendation": recommendation,
            # Định danh vòng đời hồ sơ & loại kích hoạt
            "run_number": int(run_number),
            "triggered_by": str(triggered_by),
            "is_official": bool(is_official),
            # Snapshot các chỉ số tài chính & nhân khẩu học
            "application_snapshot": safe_snapshot(application_snapshot),
            # Tóm tắt lý do SHAP (đóng góp định lượng)
            "top_shap_factors": [
                {
                    "dac_trung": f.get("dac_trung", ""),
                    "shap_value": round(float(f.get("shap_value", 0.0)), 4),
                    "chieu_huong": f.get("chieu_huong", "")
                }
                for f in top_shap_factors
            ]
        }

        if extra_metadata:
            record["extra_metadata"] = {k: v for k, v in extra_metadata.items() if k in METADATA_FIELDS}

        # Ghi append-only an toàn dạng JSON Lines
        if persist:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    def read_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Đọc N bản ghi kiểm toán gần nhất phục vụ thanh tra/đối soát.
        Tối ưu hóa: Dùng collections.deque streaming để chỉ giữ N dòng cuối,
        tiết kiệm RAM tối đa khi file log tăng lên hàng trăm nghìn dòng.
        """
        if not os.path.exists(self.log_file):
            return []

        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        recent_lines: deque = deque(maxlen=limit)
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s:
                    recent_lines.append(s)

        records = []
        for line in recent_lines:
            try:
                rec = json.loads(line)
                # Tương thích ngược với các schema cũ (backwards compatibility)
                if "threshold" not in rec and "threshold_applied" in rec:
                    rec["threshold"] = rec["threshold_applied"]
                if "threshold_applied" not in rec and "threshold" in rec:
                    rec["threshold_applied"] = rec["threshold"]
                if "client" in rec and "extra_metadata" not in rec:
                    rec["extra_metadata"] = {"client_source": rec.get("client", "api")}
                # Legacy free-text fields can contain PII supplied by old clients.
                allowed = {"timestamp", "request_id", "ma_ho_so", "model_version", "threshold_config_version",
                           "decision_engine_version", "schema_version", "threshold", "threshold_applied",
                           "prob_approved", "is_approved", "hard_rule_violated", "run_number", "is_official", "triggered_by"}
                rec = {k: v for k, v in rec.items() if k in allowed}
                rec["legacy"] = True
                rec["decision"] = "Bản ghi lịch sử (đã ẩn nội dung tự do)"
                records.append(rec)
            except Exception:
                pass
        return records


# Singleton audit logger dùng chung toàn hệ thống
audit_logger = AuditLogger()
