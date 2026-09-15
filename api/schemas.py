import os
import sys
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.decision import FIELD_CONSTRAINTS

# Định nghĩa Literal nghiêm ngặt theo đúng vocabulary của OneHotEncoder và FIELD_CONSTRAINTS
GioiTinhType = Literal["Nam", "Nữ"]
TinhTrangHonNhanType = Literal["Đã kết hôn", "Độc thân", "Ly hôn / Góa"]
TrinhDoHocVanType = Literal["Cao đẳng / Đại học", "Sau đại học", "Trung học phổ thông"]
LoaiHinhNgheNghiepType = Literal[
    "Nhân viên văn phòng",
    "Cán bộ / Công chức",
    "Kinh doanh tự do",
    "Chủ doanh nghiệp",
    "Công nhân / Lao động kỹ thuật"
]
MucDichVayType = Literal[
    "Vay mua nhà / đất",
    "Vay mua ô tô",
    "Vay sản xuất kinh doanh",
    "Vay tiêu dùng sinh hoạt",
    "Vay xây dựng / sửa nhà"
]
KhuVucSinhSongType = Literal["Nội thành / Đô thị", "Ngoại thành / Bán đô thị", "Nông thôn"]
NhomNoCicType = Literal[
    "Nhóm 1 (Đủ tiêu chuẩn)",
    "Nhóm 2 (Cần chú ý)",
    "Nhóm 3 (Dưới tiêu chuẩn)",
    "Nhóm 4 (Nghi ngờ)",
    "Nhóm 5 (Mất vốn)"
]
LichSuNoXauType = Literal["Không", "Có"]


class LoanApplicationInput(BaseModel):
    ma_ho_so: str = Field(..., min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$", description="Mã hồ sơ: chữ, số và gạch ngang")
    ho_ten: str = Field(..., min_length=1, max_length=160, description="Họ và tên khách hàng")
    tuoi: int = Field(
        ...,
        ge=FIELD_CONSTRAINTS["tuoi"]["min"],
        le=FIELD_CONSTRAINTS["tuoi"]["max"],
        description=FIELD_CONSTRAINTS["tuoi"]["description"]
    )
    gioi_tinh: GioiTinhType = Field(
        ...,
        description=FIELD_CONSTRAINTS["gioi_tinh"]["description"]
    )
    tinh_trang_hon_nhan: TinhTrangHonNhanType = Field(
        ...,
        description=FIELD_CONSTRAINTS["tinh_trang_hon_nhan"]["description"]
    )
    so_nguoi_phu_thuoc: int = Field(
        ...,
        ge=FIELD_CONSTRAINTS["so_nguoi_phu_thuoc"]["min"],
        le=FIELD_CONSTRAINTS["so_nguoi_phu_thuoc"]["max"],
        description=FIELD_CONSTRAINTS["so_nguoi_phu_thuoc"]["description"]
    )
    trinh_do_hoc_van: TrinhDoHocVanType = Field(
        ...,
        description=FIELD_CONSTRAINTS["trinh_do_hoc_van"]["description"]
    )
    loai_hinh_nghe_nghiep: LoaiHinhNgheNghiepType = Field(
        ...,
        description=FIELD_CONSTRAINTS["loai_hinh_nghe_nghiep"]["description"]
    )
    thu_nhap_thang_vnd: float = Field(
        ...,
        ge=FIELD_CONSTRAINTS["thu_nhap_thang_vnd"]["min"],
        le=FIELD_CONSTRAINTS["thu_nhap_thang_vnd"]["max"],
        description=FIELD_CONSTRAINTS["thu_nhap_thang_vnd"]["description"]
    )
    thu_nhap_nguoi_dong_vay_vnd: float = Field(
        ...,
        ge=FIELD_CONSTRAINTS["thu_nhap_nguoi_dong_vay_vnd"]["min"],
        le=FIELD_CONSTRAINTS["thu_nhap_nguoi_dong_vay_vnd"]["max"],
        description=FIELD_CONSTRAINTS["thu_nhap_nguoi_dong_vay_vnd"]["description"]
    )
    gia_tri_tai_san_dam_bao_vnd: float = Field(
        ...,
        ge=FIELD_CONSTRAINTS["gia_tri_tai_san_dam_bao_vnd"]["min"],
        le=FIELD_CONSTRAINTS["gia_tri_tai_san_dam_bao_vnd"]["max"],
        description=FIELD_CONSTRAINTS["gia_tri_tai_san_dam_bao_vnd"]["description"]
    )
    muc_dich_vay: MucDichVayType = Field(
        ...,
        description=FIELD_CONSTRAINTS["muc_dich_vay"]["description"]
    )
    so_tien_vay_vnd: float = Field(
        ...,
        ge=FIELD_CONSTRAINTS["so_tien_vay_vnd"]["min"],
        le=FIELD_CONSTRAINTS["so_tien_vay_vnd"]["max"],
        description=FIELD_CONSTRAINTS["so_tien_vay_vnd"]["description"]
    )
    thoi_han_vay_thang: int = Field(
        ...,
        ge=FIELD_CONSTRAINTS["thoi_han_vay_thang"]["min"],
        le=FIELD_CONSTRAINTS["thoi_han_vay_thang"]["max"],
        description=FIELD_CONSTRAINTS["thoi_han_vay_thang"]["description"]
    )
    khu_vuc_sinh_song: KhuVucSinhSongType = Field(
        ...,
        description=FIELD_CONSTRAINTS["khu_vuc_sinh_song"]["description"]
    )
    diem_tin_dung_cic: int = Field(
        ...,
        ge=FIELD_CONSTRAINTS["diem_tin_dung_cic"]["min"],
        le=FIELD_CONSTRAINTS["diem_tin_dung_cic"]["max"],
        description=FIELD_CONSTRAINTS["diem_tin_dung_cic"]["description"]
    )
    nhom_no_cic: NhomNoCicType = Field(
        ...,
        description=FIELD_CONSTRAINTS["nhom_no_cic"]["description"]
    )
    so_lan_tre_han_2_nam: int = Field(
        ...,
        ge=FIELD_CONSTRAINTS["so_lan_tre_han_2_nam"]["min"],
        le=FIELD_CONSTRAINTS["so_lan_tre_han_2_nam"]["max"],
        description=FIELD_CONSTRAINTS["so_lan_tre_han_2_nam"]["description"]
    )
    so_khoan_vay_hien_tai: int = Field(
        ...,
        ge=FIELD_CONSTRAINTS["so_khoan_vay_hien_tai"]["min"],
        le=FIELD_CONSTRAINTS["so_khoan_vay_hien_tai"]["max"],
        description=FIELD_CONSTRAINTS["so_khoan_vay_hien_tai"]["description"]
    )
    lich_su_no_xau: LichSuNoXauType = Field(
        ...,
        description=FIELD_CONSTRAINTS["lich_su_no_xau"]["description"]
    )
    ty_le_dti: float = Field(
        ...,
        ge=FIELD_CONSTRAINTS["ty_le_dti"]["min"],
        le=FIELD_CONSTRAINTS["ty_le_dti"]["max"],
        description=FIELD_CONSTRAINTS["ty_le_dti"]["description"]
    )

    model_config = {
        "extra": "forbid", "allow_inf_nan": False, "str_strip_whitespace": True,
        "json_schema_extra": {
            "example": {
                "ma_ho_so": "HS-20268888",
                "ho_ten": "Nguyễn Hoàng Nam",
                "tuoi": 35,
                "gioi_tinh": "Nam",
                "tinh_trang_hon_nhan": "Đã kết hôn",
                "so_nguoi_phu_thuoc": 1,
                "trinh_do_hoc_van": "Cao đẳng / Đại học",
                "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
                "thu_nhap_thang_vnd": 35000000.0,
                "thu_nhap_nguoi_dong_vay_vnd": 15000000.0,
                "gia_tri_tai_san_dam_bao_vnd": 1800000000.0,
                "muc_dich_vay": "Vay mua nhà / đất",
                "so_tien_vay_vnd": 800000000.0,
                "thoi_han_vay_thang": 120,
                "khu_vuc_sinh_song": "Nội thành / Đô thị",
                "diem_tin_dung_cic": 735,
                "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
                "so_lan_tre_han_2_nam": 0,
                "so_khoan_vay_hien_tai": 2,
                "lich_su_no_xau": "Không",
                "ty_le_dti": 28.5
            }
        }
    }


class ShapFactor(BaseModel):
    dac_trung: str = Field(..., description="Tên đặc trưng tài chính")
    chieu_huong: str = Field(..., description="Chiều hướng tác động (Tăng khả năng duyệt / Tăng rủi ro từ chối)")
    shap_value: float = Field(..., description="Trị số đóng góp SHAP")
    muc_do: str = Field(..., description="Mức độ ảnh hưởng (Rất cao, Đáng kể, Vừa phải)")


class PredictionResponse(BaseModel):
    request_id: Optional[str] = Field(default=None, description="Mã định danh kiểm toán duy nhất của giao dịch (UUID4)")
    ma_ho_so: str
    ho_ten: str
    ket_qua: str = Field(..., description="Kết quả thẩm định: PHÊ DUYỆT hoặc TỪ CHỐI")
    ma_ket_qua: int = Field(..., description="1 nếu được phê duyệt, 0 nếu bị từ chối")
    xac_suat_phe_duyet: float = Field(..., description="Xác suất phê duyệt khoản vay (%)")
    muc_do_rui_ro: str = Field(..., description="Mức độ rủi ro tín dụng (Thấp, Trung bình, Cao)")
    nguong_quyet_dinh: float = Field(..., description="Ngưỡng xác suất phê duyệt được áp dụng")
    top_nhan_to_anh_huong: List[ShapFactor] = Field(..., description="Top các yếu tố giải thích quyết định theo SHAP")
    khuyen_nghi_nghiep_vu: str = Field(..., description="Khuyến nghị xử lý hồ sơ cho cán bộ tín dụng")
    hard_rule_violated: bool = Field(default=False, description="Cờ đánh dấu có vi phạm chính sách tín dụng cứng hay không")
    policy_reason: Optional[str] = Field(default=None, description="Lý do chi tiết nếu vi phạm chính sách tín dụng cứng")
    run_number: int = Field(default=1, description="Thứ tự lần chạy thẩm định của hồ sơ (Run #1, Run #2...)")
    is_cached_run: bool = Field(default=False, description="Cờ đánh dấu kết quả từ cache chống trùng lặp (không ghi thêm audit)")


    shap_base_value: float
    fx_log_odds: float
    prob_from_log_odds: float
    shap_factors: List[ShapFactor]
    model_version: str
    threshold_config_version: str
    decision_engine_version: str
    so_tien_vay_vnd: float
    assessed_at: str


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class CommitteeDecisionInput(StrictInput):
    assessment_id: str = Field(..., min_length=1, max_length=80)
    idempotency_key: str = Field(..., min_length=8, max_length=100)
    final_decision: Literal["PHÊ DUYỆT", "TỪ CHỐI", "BỔ SUNG HỒ SƠ"]
    approved_limit_vnd: float = Field(..., ge=0, le=10_000_000_000)
    interest_rate_pct: float = Field(..., ge=0, le=50)


class BatchAssessRequest(StrictInput):
    applications: List[LoanApplicationInput] = Field(..., min_length=1, max_length=100)
    use_optimal_threshold: bool = True


class BatchAssessSummary(BaseModel):
    tong_so_ho_so: int
    so_luong_thanh_cong: int
    so_luong_loi: int
    so_luong_duyet: int
    so_luong_tu_choi: int
    ty_le_duyet_pct: float
    tong_han_muc_de_xuat_vnd: float
    so_ca_vi_pham_chinh_sach: int


class BatchAssessResponse(BaseModel):
    summary: BatchAssessSummary
    results: List[PredictionResponse]
    errors: List[dict]


class PortfolioStressRequest(StrictInput):
    case_ids: Optional[List[str]] = Field(default=None, max_length=100)
    applications: Optional[List[LoanApplicationInput]] = Field(default=None, max_length=100)
    income_shock_pct: float = Field(default=-15, ge=-50, le=0)
    interest_shock_pct: float = Field(default=2, ge=0, le=10)
    collateral_shock_pct: float = Field(default=-20, ge=-50, le=0)
    cic_shock_points: int = Field(default=-30, ge=-200, le=0)


class CoreBankingDisburseRequest(StrictInput):
    decision_id: str = Field(..., min_length=1, max_length=80)
    account_number: str = Field(..., pattern=r"^[0-9]{6,24}$")
    idempotency_key: str = Field(..., min_length=8, max_length=100)


class CoreBankingDisburseResponse(BaseModel):
    success: bool
    simulation_id: str
    decision_id: str
    status: Literal["SIMULATED_NOT_DISBURSED"]
    ma_ho_so: str
    account_masked: str
    simulated_amount_vnd: float
    timestamp: str
    message: str


class LoginInput(StrictInput):
    username: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=1, max_length=256)
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
