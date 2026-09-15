"""
Decision Engine: Bộ não nghiệp vụ thẩm định khoản vay tập trung (Single Source of Truth).
Định nghĩa ràng buộc trường dữ liệu (FIELD_CONSTRAINTS), kiểm tra quy tắc cứng (Hard Rules),
phân tầng rủi ro tín dụng (Risk Tiering) và sinh khuyến nghị nghiệp vụ thống nhất cho cả FastAPI và Streamlit.
"""

import os
import sys
import json
import uuid
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import joblib
import shap

from src.audit import audit_logger
from src.integrity import verify_artifacts
from src.explainability import extract_top_shap_reasons
from src.preprocessing import VietnameseCreditFeatureExtractor, Winsorizer

# Tương thích với joblib pickle khi nạp complete_pipeline
try:
    sys.modules['__main__'].VietnameseCreditFeatureExtractor = VietnameseCreditFeatureExtractor
    sys.modules['__main__'].Winsorizer = Winsorizer
except Exception:
    pass


# ==============================================================================
# 1. NGUỒN CHÂN LÝ DUY NHẤT VỀ RÀNG BUỘC DỮ LIỆU (FIELD CONSTRAINTS)
# ==============================================================================
FIELD_CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    "tuoi": {
        "min": 18,
        "max": 70,
        "default": 35,
        "step": 1,
        "description": "Độ tuổi khách hàng (18 - 70)"
    },
    "gioi_tinh": {
        "options": ["Nam", "Nữ"],
        "default": "Nam",
        "description": "Giới tính khách hàng"
    },
    "tinh_trang_hon_nhan": {
        "options": ["Đã kết hôn", "Độc thân", "Ly hôn / Góa"],
        "default": "Đã kết hôn",
        "description": "Tình trạng hôn nhân"
    },
    "so_nguoi_phu_thuoc": {
        "min": 0,
        "max": 8,
        "default": 1,
        "step": 1,
        "description": "Số người phụ thuộc tài chính (0 - 8)"
    },
    "trinh_do_hoc_van": {
        "options": ["Cao đẳng / Đại học", "Sau đại học", "Trung học phổ thông"],
        "default": "Cao đẳng / Đại học",
        "description": "Trình độ học vấn cao nhất"
    },
    "loai_hinh_nghe_nghiep": {
        "options": [
            "Nhân viên văn phòng",
            "Cán bộ / Công chức",
            "Kinh doanh tự do",
            "Chủ doanh nghiệp",
            "Công nhân / Lao động kỹ thuật"
        ],
        "default": "Nhân viên văn phòng",
        "description": "Loại hình nghề nghiệp hiện tại"
    },
    "thu_nhap_thang_vnd": {
        "min": 1_000_000.0,
        "max": 500_000_000.0,
        "default": 35_000_000.0,
        "step": 1_000_000.0,
        "description": "Thu nhập người vay chính hàng tháng (VNĐ)"
    },
    "thu_nhap_nguoi_dong_vay_vnd": {
        "min": 0.0,
        "max": 300_000_000.0,
        "default": 15_000_000.0,
        "step": 1_000_000.0,
        "description": "Thu nhập người đồng vay hàng tháng (VNĐ)"
    },
    "gia_tri_tai_san_dam_bao_vnd": {
        "min": 0.0,
        "max": 50_000_000_000.0,
        "default": 1_800_000_000.0,
        "step": 10_000_000.0,
        "description": "Giá trị tài sản đảm bảo thẩm định (VNĐ)"
    },
    "muc_dich_vay": {
        "options": [
            "Vay mua nhà / đất",
            "Vay mua ô tô",
            "Vay sản xuất kinh doanh",
            "Vay tiêu dùng sinh hoạt",
            "Vay xây dựng / sửa nhà"
        ],
        "default": "Vay mua nhà / đất",
        "description": "Mục đích sử dụng vốn vay"
    },
    "so_tien_vay_vnd": {
        "min": 10_000_000.0,
        "max": 10_000_000_000.0,
        "default": 800_000_000.0,
        "step": 10_000_000.0,
        "description": "Số tiền đề nghị vay vốn (VNĐ)"
    },
    "thoi_han_vay_thang": {
        "min": 6,
        "max": 360,
        "default": 120,
        "step": 6,
        "description": "Thời hạn vay vốn (tháng, 6 - 360)"
    },
    "khu_vuc_sinh_song": {
        "options": ["Nội thành / Đô thị", "Ngoại thành / Bán đô thị", "Nông thôn"],
        "default": "Nội thành / Đô thị",
        "description": "Khu vực cư trú và vị trí tài sản"
    },
    "diem_tin_dung_cic": {
        "min": 400,
        "max": 850,
        "default": 735,
        "step": 5,
        "description": "Điểm tín dụng CIC Việt Nam (400 - 850)"
    },
    "nhom_no_cic": {
        "options": [
            "Nhóm 1 (Đủ tiêu chuẩn)",
            "Nhóm 2 (Cần chú ý)",
            "Nhóm 3 (Dưới tiêu chuẩn)",
            "Nhóm 4 (Nghi ngờ)",
            "Nhóm 5 (Mất vốn)"
        ],
        "default": "Nhóm 1 (Đủ tiêu chuẩn)",
        "description": "Phân loại nhóm nợ CIC hiện hành"
    },
    "so_lan_tre_han_2_nam": {
        "min": 0,
        "max": 10,
        "default": 0,
        "step": 1,
        "description": "Số lần chậm trả nợ trong 2 năm gần nhất (0 - 10)"
    },
    "so_khoan_vay_hien_tai": {
        "min": 0,
        "max": 15,
        "default": 2,
        "step": 1,
        "description": "Số hợp đồng tín dụng đang mở tại các TCTD (0 - 15)"
    },
    "lich_su_no_xau": {
        "options": ["Không", "Có"],
        "default": "Không",
        "description": "Tiền sử rơi vào nợ xấu nhóm 3-5 trong quá khứ"
    },
    "ty_le_dti": {
        "min": 0.0,
        "max": 100.0,
        "default": 28.5,
        "step": 0.5,
        "description": "Tỷ lệ Nợ trên Thu nhập DTI (0 - 100%)"
    }
}


# ==============================================================================
# 2. KIỂM TRA QUY TẮC CỨNG (HARD POLICY RULES)
# ==============================================================================
class HardRulesEngine:
    """Kiểm tra các chính sách tín dụng tiên quyết (Policy Cut-offs)."""

    @staticmethod
    def check_policy(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Kiểm tra xem hồ sơ có vi phạm quy tắc tín dụng cứng hay không.
        Trả về (violated: bool, reason: str | None).
        """
        nhom_no = data.get("nhom_no_cic") or data.get("nhom_no_hien_tai", "")
        if nhom_no in ["Nhóm 3 (Dưới tiêu chuẩn)", "Nhóm 4 (Nghi ngờ)", "Nhóm 5 (Mất vốn)"]:
            return True, f"Chính sách tín dụng: Khách hàng thuộc {nhom_no} theo chuẩn phân loại NHNN - Từ chối phê duyệt tự động."

        # Xử lý an toàn khi diem_tin_dung_cic là None hoặc không hợp lệ
        raw_cic = data.get("diem_tin_dung_cic")
        cic = int(raw_cic) if raw_cic is not None else 700

        # Đồng bộ luật sàn điểm tín dụng chuẩn NHNN (khớp với data_generator)
        if cic < 450:
            return True, f"Chính sách tín dụng: Điểm tín dụng CIC ({cic} < 450) thuộc nhóm rủi ro rất cao (Hạng 9-10) - Từ chối phê duyệt tự động."

        lich_su = data.get("lich_su_no_xau", "Không")
        if lich_su == "Có" and cic < 540:
            return True, f"Chính sách tín dụng: Khách hàng có tiền sử nợ xấu và điểm CIC hiện tại ({cic} < 540) không đạt tiêu chuẩn tái cấp tín dụng."

        return False, None

    @classmethod
    def evaluate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Đánh giá quy tắc cứng, trả về dict {'violated': bool, 'reason': Optional[str]}
        phục vụ kiểm thử và giao diện mở rộng.
        """
        violated, reason = cls.check_policy(data)
        return {"violated": violated, "reason": reason}


# ==============================================================================
# 3. PHÂN TẦNG RỦI RO TÍN DỤNG (RISK TIERING ENGINE)
# ==============================================================================
class RiskTierEngine:
    """Phân tầng mức độ rủi ro tín dụng dựa trên xác suất phê duyệt."""

    @staticmethod
    def get_risk_tier(prob_approved: float) -> str:
        if prob_approved >= 0.75:
            return "Rất thấp (Hồ sơ xuất sắc)"
        elif prob_approved >= 0.60:
            return "Thấp (Hồ sơ an toàn)"
        elif prob_approved >= 0.40:
            return "Trung bình (Cần thẩm định kỹ tài sản)"
        else:
            return "Cao (Rủi ro vỡ nợ cao)"


# ==============================================================================
# 4. SINH KHUYẾN NGHỊ NGHIỆP VỤ HÀNH ĐỘNG ĐƯỢC (RECOMMENDATION ENGINE)
# ==============================================================================
class RecommendationEngine:
    """Sinh khuyến nghị hành động cụ thể cho cán bộ thẩm định tín dụng."""

    @staticmethod
    def generate_recommendation(
        is_approved: int,
        data: Dict[str, Any],
        prob_approved: float,
        policy_reason: Optional[str] = None
    ) -> str:
        if policy_reason:
            return f"Khuyến nghị: TỪ CHỐI CHO VAY DO VI PHẠM CHÍNH SÁCH. {policy_reason}"

        if is_approved == 1:
            if prob_approved >= 0.85:
                return (
                    "Khuyến nghị: ĐỦ ĐIỀU KIỆN PHÊ DUYỆT ƯU TIÊN. "
                    "Hồ sơ có năng lực tài chính mạnh và lịch sử tín dụng xuất sắc. "
                    "Đề xuất áp dụng gói lãi suất ưu đãi và giải ngân theo luồng nhanh."
                )
            return (
                "Khuyến nghị: ĐỦ ĐIỀU KIỆN PHÊ DUYỆT. "
                "Hồ sơ đáp ứng đầy đủ tiêu chuẩn tín dụng hiện hành. "
                "Có thể giải ngân theo quy trình thẩm định thông thường."
            )
        else:
            cic = data.get("diem_tin_dung_cic", 650)
            delinq = data.get("so_lan_tre_han_2_nam", 0)
            dti = data.get("ty_le_dti", 30.0)

            if cic < 550 or delinq >= 3:
                return (
                    "Khuyến nghị: TỪ CHỐI CHO VAY. "
                    "Điểm tín dụng CIC dưới chuẩn hoặc có nhiều lần chậm thanh toán trong 2 năm gần nhất. "
                    "Cần cải thiện lịch sử trả nợ trước khi nộp lại hồ sơ."
                )
            elif dti > 45.0:
                return (
                    f"Khuyến nghị: TẠM HOÃN / TỪ CHỐI. "
                    f"Tỷ lệ nghĩa vụ nợ trên thu nhập DTI ({dti:.1f}%) vượt ngưỡng an toàn quy định (45%). "
                    "Đề nghị khách hàng tất toán bớt các khoản vay nhỏ hiện hữu để giảm áp lực tài chính."
                )
            else:
                return (
                    "Khuyến nghị: CÂN NHẮC / YÊU CẦU BỔ SUNG. "
                    "Hồ sơ cận biên phê duyệt. Cần xem xét bổ sung người đồng vay có thu nhập ổn định, "
                    "tăng giá trị tài sản thế chấp hoặc giảm số tiền đề nghị vay để cải thiện hệ số LTV/DTI."
                )


# ==============================================================================
# 5. ĐỘNG CƠ RA QUYẾT ĐỊNH TỔNG HỢP (DECISION ENGINE)
# ==============================================================================
class DecisionEngine:
    """
    Bộ não ra quyết định tập trung, tích hợp Hard Rules, Machine Learning Probability,
    Thresholding, Risk Tiering, Explainable AI (SHAP) và Audit Trail.
    """

    def __init__(self, config_path: Optional[str] = None, models_dir: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.models_dir = models_dir or self._find_models_dir()
        self.default_threshold = 0.50
        self.optimal_threshold = 0.50
        self.model_version = "1.2.0"
        self.threshold_config_version = "1.2.0"
        self.decision_engine_version = "1.2.0"
        self.complete_pipeline = None
        self.preprocessor = None
        self.best_model = None
        self.tree_explainer = None
        self.feature_names: List[str] = []
        self._artifacts_loaded = False
        self.load_threshold_config()

    def _find_config_path(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..", "models", "threshold_config.json")

    def _find_models_dir(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..", "models")

    def load_threshold_config(self) -> None:
        # Never silently substitute another decision policy when configuration is missing.
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        default, optimal = float(cfg["default_threshold"]), float(cfg["optimal_threshold"])
        if not (0 < default < 1 and 0 < optimal < 1):
            raise ValueError("Thresholds must be finite probabilities between zero and one")
        self.default_threshold, self.optimal_threshold = default, optimal
        for key in ("model_version", "threshold_config_version", "decision_engine_version"):
            setattr(self, key, str(cfg[key]))

    def load_artifacts(self, models_dir: Optional[str] = None) -> bool:
        target_dir = models_dir or self.models_dir
        self._artifacts_loaded = False
        try:
            verify_artifacts(target_dir)
            self.load_threshold_config()
            self.complete_pipeline = joblib.load(os.path.join(target_dir, "complete_pipeline.joblib"))
            self.preprocessor = self.complete_pipeline.named_steps["preprocessor"]
            self.best_model = self.complete_pipeline.named_steps["classifier"]
            metadata = joblib.load(os.path.join(target_dir, "feature_metadata.joblib"))
            self.feature_names = metadata["all_feature_names"]
            if len(self.feature_names) != self.best_model.n_features_in_:
                raise ValueError("Model and feature metadata do not match")
            self.tree_explainer = shap.TreeExplainer(self.best_model)
            self._artifacts_loaded = True
            return True
        except Exception:
            self.complete_pipeline = self.preprocessor = self.best_model = self.tree_explainer = None
            self.feature_names = []
            return False

    def ensure_artifacts_loaded(self) -> None:
        if not self._artifacts_loaded:
            raise RuntimeError("Verified model artifacts are unavailable; restart after restoring the approved release")

    def evaluate(
        self,
        prob_approved: float,
        application_data: Dict[str, Any],
        threshold: Optional[float] = None,
        use_optimal_threshold: bool = True
    ) -> Dict[str, Any]:
        """
        Thực hiện đánh giá nghiệp vụ thuần túy dựa trên xác suất và quy tắc chính sách.
        """
        # Xác định ngưỡng áp dụng
        if threshold is not None:
            applied_threshold = float(threshold)
        elif use_optimal_threshold:
            applied_threshold = self.optimal_threshold
        else:
            applied_threshold = self.default_threshold

        # 1. Kiểm tra Hard Rules
        violated, policy_reason = HardRulesEngine.check_policy(application_data)

        if violated:
            is_approved = 0
            ket_qua = "TỪ CHỐI CHO VAY (VI PHẠM CHÍNH SÁCH)"
            risk_tier = "Cao (Vi phạm chính sách nợ xấu)"
            recommendation = RecommendationEngine.generate_recommendation(
                is_approved=0,
                data=application_data,
                prob_approved=prob_approved,
                policy_reason=policy_reason
            )
        else:
            # 2. Đánh giá dựa trên xác suất và ngưỡng
            is_approved = 1 if prob_approved >= applied_threshold else 0
            ket_qua = "PHÊ DUYỆT KHOẢN VAY" if is_approved == 1 else "TỪ CHỐI KHOẢN VAY"
            risk_tier = RiskTierEngine.get_risk_tier(prob_approved)
            recommendation = RecommendationEngine.generate_recommendation(
                is_approved=is_approved,
                data=application_data,
                prob_approved=prob_approved,
                policy_reason=None
            )

        return {
            "ma_ho_so": application_data.get("ma_ho_so", ""),
            "ho_ten": application_data.get("ho_ten", ""),
            "is_approved": is_approved,
            "ket_qua": ket_qua,
            "xac_suat_phe_duyet": round(prob_approved * 100, 2),
            "prob_approved": prob_approved,
            "muc_do_rui_ro": risk_tier,
            "nguong_quyet_dinh": round(applied_threshold, 3),
            "khuyen_nghi_nghiep_vu": recommendation,
            "hard_rule_violated": violated,
            "policy_reason": policy_reason
        }

    def assess_application(
        self,
        application_data: Dict[str, Any],
        threshold: Optional[float] = None,
        use_optimal_threshold: bool = True,
        request_id: Optional[str] = None,
        client_source: str = "api",
        top_k_shap: int = 5,
        run_number: int = 1,
        triggered_by: str = "user_click",
        is_official: bool = False,
        skip_audit: bool = False
    ) -> Dict[str, Any]:
        """
        Quy trình thẩm định tín dụng tập trung hoàn chỉnh:
        Streamlit UI / FastAPI -> DecisionEngine -> (Prediction, Business Rules, SHAP) -> AuditLogger -> logs/audit.jsonl
        """
        self.ensure_artifacts_loaded()
        req_id = request_id or str(uuid.uuid4())

        # Chuẩn bị DataFrame ma trận đặc trưng
        df_input = pd.DataFrame([application_data])
        df_features = df_input.drop(columns=["ma_ho_so", "ho_ten"], errors="ignore")

        # 1. Dự đoán xác suất qua Machine Learning Model (Prediction)
        # Tối ưu hóa: Chỉ transform 1 lần duy nhất để phục vụ cả Model và SHAP Explainer
        X_prep = self.preprocessor.transform(df_features)
        prob_approved = float(self.best_model.predict_proba(X_prep)[0, 1])

        # 2. Đánh giá nghiệp vụ (Business Rules)
        eval_result = self.evaluate(
            prob_approved=prob_approved,
            application_data=application_data,
            threshold=threshold,
            use_optimal_threshold=use_optimal_threshold
        )

        # 3. Tính toán đóng góp đặc trưng AI có thể giải thích (SHAP)
        shap_vals = self.tree_explainer.shap_values(X_prep)[0]
        top_shap_factors = extract_top_shap_reasons(
            shap_vals, 
            self.feature_names, 
            feature_values_row=X_prep[0],
            top_k=top_k_shap
        )

        # 4. Ghi vết kiểm toán tự động (Audit Trail & PII Minimization)
        ma_ho_so = str(application_data.get("ma_ho_so") or "HS-DEFAULT")
        audit_record = None
        if not skip_audit:
            audit_record = audit_logger.log_decision(
                request_id=req_id,
                ma_ho_so=ma_ho_so,
                prob_approved=prob_approved,
                threshold_applied=eval_result["nguong_quyet_dinh"],
                decision=eval_result["ket_qua"],
                is_approved=eval_result["is_approved"],
                risk_tier=eval_result["muc_do_rui_ro"],
                hard_rule_violated=eval_result["hard_rule_violated"],
                recommendation=eval_result["khuyen_nghi_nghiep_vu"],
                top_shap_factors=top_shap_factors,
                model_version=self.model_version,
                threshold_config_version=self.threshold_config_version,
                decision_engine_version=self.decision_engine_version,
                application_snapshot={k: v for k, v in application_data.items() if k not in ["cccd", "so_dien_thoai"]},
                extra_metadata={"client_source": client_source},
                run_number=run_number,
                triggered_by=triggered_by,
                is_official=is_official
            )

        exp_val = float(np.ravel(self.tree_explainer.expected_value)[0])
        fx_log_odds = exp_val + float(np.sum(shap_vals))

        return {
            **eval_result,
            "request_id": req_id,
            "threshold": eval_result["nguong_quyet_dinh"],
            "top_shap_factors": top_shap_factors,
            "shap_values": shap_vals,
            "shap_base_value": exp_val,
            "fx_log_odds": fx_log_odds,
            "prob_from_log_odds": float(1.0 / (1.0 + np.exp(-fx_log_odds))),
            "X_prep": X_prep,
            "feature_names": self.feature_names,
            "model_version": self.model_version,
            "threshold_config_version": self.threshold_config_version,
            "decision_engine_version": self.decision_engine_version,
            "audit_record": audit_record
        }


# Singleton instance dùng cho toàn ứng dụng
decision_engine = DecisionEngine()
try:
    decision_engine.load_artifacts()
except Exception:
    pass
