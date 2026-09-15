"""
Data Generator for Vietnamese Loan Approval Prediction System.
Bộ sinh dữ liệu hồ sơ vay vốn khách hàng Việt Nam thực tế:
- Khách hàng người Việt Nam (họ tên tiếng Việt, nhân khẩu học Việt Nam).
- Đơn vị tiền tệ: VNĐ (thu nhập, khoản vay, tài sản đảm bảo).
- Chuẩn đánh giá tín dụng: Điểm tín dụng CIC, Phân nhóm nợ CIC (Nhóm 1 - Nhóm 5).
- Tỷ lệ DTI, LTV và quan hệ nghiệp vụ ngân hàng Việt Nam.
"""

import os
import sys
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Danh sách họ, đệm, tên người Việt Nam
HO_VIET = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Đinh"]
DEM_NAM = ["Văn", "Hữu", "Đức", "Thành", "Minh", "Quang", "Xuân", "Thanh", "Tuấn", "Anh", "Hoàng", "Quốc"]
DEM_NU = ["Thị", "Ngọc", "Thu", "Mai", "Phương", "Khánh", "Mỹ", "Thảo", "Thanh", "Hải", "Như", "Ánh"]
TEN_NAM = ["Hùng", "Cường", "Dũng", "Nam", "Phong", "Long", "Tuấn", "Hải", "Sơn", "Trung", "Bình", "Việt", "Khang", "Tùng", "Bách", "Đạt", "Phúc", "Thịnh"]
TEN_NU = ["Trang", "Linh", "Hương", "Hà", "Lan", "Mai", "Phương", "Huyền", "Nhung", "Vy", "Thảo", "Hạnh", "Ngân", "Hoa", "Yến", "Tâm", "Oanh", "Diệp"]


def generate_vietnamese_names(n_samples: int, genders: np.ndarray, rng: np.random.Generator) -> list:
    """Tạo danh sách họ tên người Việt Nam ngẫu nhiên dựa theo giới tính."""
    names = []
    for g in genders:
        ho = rng.choice(HO_VIET)
        if g == "Nam":
            dem = rng.choice(DEM_NAM)
            ten = rng.choice(TEN_NAM)
        else:
            dem = rng.choice(DEM_NU)
            ten = rng.choice(TEN_NU)
        names.append(f"{ho} {dem} {ten}")
    return names


def generate_vietnamese_loan_dataset(
    n_samples: int = 6000,
    random_state: int = 42,
    include_missing: bool = True
) -> pd.DataFrame:
    """
    Sinh bộ dữ liệu hồ sơ tín dụng khách hàng Việt Nam.
    """
    rng = np.random.default_rng(random_state)

    # 1. Nhân khẩu học
    age = rng.integers(22, 65, size=n_samples)
    gender = rng.choice(["Nam", "Nữ"], size=n_samples, p=[0.54, 0.46])
    full_names = generate_vietnamese_names(n_samples, gender, rng)
    
    marital_status = rng.choice(
        ["Đã kết hôn", "Độc thân", "Ly hôn / Góa"], 
        size=n_samples, 
        p=[0.60, 0.32, 0.08]
    )
    
    # Số người phụ thuộc (con cái, cha mẹ già)
    dependents = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        if marital_status[i] == "Đã kết hôn":
            dependents[i] = rng.choice([0, 1, 2, 3], p=[0.20, 0.40, 0.32, 0.08])
        elif marital_status[i] == "Độc thân":
            dependents[i] = rng.choice([0, 1], p=[0.88, 0.12])
        else:
            dependents[i] = rng.choice([0, 1, 2], p=[0.45, 0.40, 0.15])

    education = rng.choice(
        ["Trung học phổ thông", "Cao đẳng / Đại học", "Sau đại học"],
        size=n_samples,
        p=[0.22, 0.63, 0.15]
    )

    employment_type = rng.choice(
        ["Nhân viên văn phòng", "Cán bộ / Công chức", "Kinh doanh tự do", "Chủ doanh nghiệp", "Công nhân / Lao động kỹ thuật"],
        size=n_samples,
        p=[0.40, 0.18, 0.22, 0.10, 0.10]
    )

    # 2. Thông tin Tài chính (Đơn vị: VNĐ)
    # Thu nhập hàng tháng: trung bình từ 12 triệu đến 80 triệu VNĐ (phân phối log-normal)
    base_mu = np.log(20_000_000) # median ~ 20 triệu
    edu_shift = np.where(education == "Sau đại học", 0.35, np.where(education == "Cao đẳng / Đại học", 0.15, 0.0))
    job_shift = np.where(employment_type == "Chủ doanh nghiệp", 0.55, np.where(employment_type == "Cán bộ / Công chức", 0.10, 0.0))
    
    applicant_income = np.exp(rng.normal(base_mu + edu_shift + job_shift, 0.42, size=n_samples))
    # Làm tròn đến 500,000 VNĐ, giới hạn từ 8 triệu đến 250 triệu VNĐ
    applicant_income = np.clip(np.round(applicant_income / 500_000) * 500_000, 8_000_000, 250_000_000)

    # Thu nhập người đồng vay (vợ/chồng hoặc người bảo lãnh)
    has_coapplicant = (marital_status == "Đã kết hôn") & (rng.random(n_samples) < 0.65) | (rng.random(n_samples) < 0.15)
    coapplicant_income = np.zeros(n_samples)
    coapplicant_income[has_coapplicant] = np.exp(rng.normal(np.log(14_000_000), 0.45, size=np.sum(has_coapplicant)))
    coapplicant_income = np.clip(np.round(coapplicant_income / 500_000) * 500_000, 0, 150_000_000)

    total_income = applicant_income + coapplicant_income

    # Giá trị tài sản đảm bảo hiện có (Bất động sản sổ đỏ/hồng, tiền gửi tiết kiệm, ô tô)
    asset_mult = rng.uniform(5.0, 35.0, size=n_samples) + (age - 22) * 0.8
    existing_assets_value = np.round((total_income * asset_mult) / 10_000_000) * 10_000_000
    existing_assets_value = np.clip(existing_assets_value, 50_000_000, 20_000_000_000)

    # 3. Thông tin Khoản vay đề nghị
    loan_purpose = rng.choice(
        ["Vay mua nhà / đất", "Vay mua ô tô", "Vay sản xuất kinh doanh", "Vay tiêu dùng sinh hoạt", "Vay xây dựng / sửa nhà"],
        size=n_samples,
        p=[0.38, 0.22, 0.20, 0.12, 0.08]
    )

    loan_term_months = rng.choice([12, 24, 36, 60, 120, 240, 300, 360], size=n_samples, p=[0.05, 0.10, 0.15, 0.25, 0.15, 0.15, 0.10, 0.05])

    # Số tiền vay phụ thuộc vào mục đích và thu nhập
    purpose_mult = {
        "Vay mua nhà / đất": rng.uniform(30, 80, size=n_samples),
        "Vay sản xuất kinh doanh": rng.uniform(15, 50, size=n_samples),
        "Vay mua ô tô": rng.uniform(10, 30, size=n_samples),
        "Vay xây dựng / sửa nhà": rng.uniform(8, 25, size=n_samples),
        "Vay tiêu dùng sinh hoạt": rng.uniform(3, 12, size=n_samples)
    }

    loan_amount = np.zeros(n_samples)
    for purp, mult in purpose_mult.items():
        mask = (loan_purpose == purp)
        loan_amount[mask] = total_income[mask] * mult[mask]
    # Làm tròn đến 10 triệu VNĐ, giới hạn từ 30 triệu đến 5 tỷ VNĐ
    loan_amount = np.clip(np.round(loan_amount / 10_000_000) * 10_000_000, 30_000_000, 5_000_000_000)

    property_area = rng.choice(
        ["Nội thành / Đô thị", "Ngoại thành / Bán đô thị", "Nông thôn"],
        size=n_samples,
        p=[0.50, 0.32, 0.18]
    )

    # 4. Lịch sử Tín dụng & Trung tâm Thông tin Tín dụng Quốc gia (CIC)
    # Điểm tín dụng CIC Việt Nam: 400 đến 850
    credit_score = rng.normal(675, 75, size=n_samples)
    credit_score = np.clip(np.round(credit_score), 410, 850).astype(int)

    # Nhóm nợ CIC (Nhóm 1 -> Nhóm 5 theo chuẩn Ngân hàng Nhà nước VN)
    # Nhóm 1: Nợ đủ tiêu chuẩn (quá hạn < 10 ngày)
    # Nhóm 2: Nợ cần chú ý (10 - 90 ngày)
    # Nhóm 3: Nợ dưới tiêu chuẩn (91 - 180 ngày)
    # Nhóm 4: Nợ nghi ngờ (181 - 360 ngày)
    # Nhóm 5: Nợ có khả năng mất vốn (> 360 ngày)
    cic_probs = np.zeros((n_samples, 5))
    for i in range(n_samples):
        sc = credit_score[i]
        if sc >= 720:
            cic_probs[i] = [0.94, 0.05, 0.01, 0.00, 0.00]
        elif sc >= 640:
            cic_probs[i] = [0.82, 0.14, 0.03, 0.01, 0.00]
        elif sc >= 550:
            cic_probs[i] = [0.55, 0.28, 0.12, 0.04, 0.01]
        else:
            cic_probs[i] = [0.20, 0.30, 0.25, 0.15, 0.10]
            
    cic_groups = ["Nhóm 1 (Đủ tiêu chuẩn)", "Nhóm 2 (Cần chú ý)", "Nhóm 3 (Dưới tiêu chuẩn)", "Nhóm 4 (Nghi ngờ)", "Nhóm 5 (Mất vốn)"]
    nhom_no_cic = np.array([rng.choice(cic_groups, p=cic_probs[i]) for i in range(n_samples)])

    # Số lần trễ hạn thanh toán trong 2 năm gần nhất
    delinquency_rate = np.where(credit_score < 580, 1.9, np.where(credit_score < 660, 0.75, 0.12))
    so_lan_tre_han_2_nam = rng.poisson(delinquency_rate, size=n_samples)
    so_lan_tre_han_2_nam = np.clip(so_lan_tre_han_2_nam, 0, 8)

    # Số khoản vay đang mở tại các tổ chức tín dụng
    so_khoan_vay_hien_tai = rng.poisson(3.2, size=n_samples) + 1
    so_khoan_vay_hien_tai = np.clip(so_khoan_vay_hien_tai, 1, 15)

    # Lịch sử nợ xấu (từng rơi vào nhóm 3-5 trong quá khứ)
    bad_debt_prob = np.where(credit_score < 560, 0.45, np.where(credit_score < 650, 0.10, 0.01))
    lich_su_no_xau = np.where(rng.random(n_samples) < bad_debt_prob, "Có", "Không")

    # Tỷ lệ nợ trên thu nhập (DTI %)
    base_dti = rng.normal(33.0, 10.5, size=n_samples) + (so_lan_tre_han_2_nam * 3.2)
    ty_le_dti = np.clip(np.round(base_dti, 1), 8.0, 78.0)

    # 5. Nhãn Mục Tiêu: phe_duyet_khoan_vay (1: Được duyệt, 0: Bị từ chối)
    # Quy tắc nghiệp vụ thẩm định tín dụng ngân hàng Việt Nam:
    z_cic = (credit_score - 660) / 75.0
    z_dti = (40.0 - ty_le_dti) / 12.0
    
    annual_income = total_income * 12.0
    lti = loan_amount / annual_income
    z_lti = (3.2 - lti) / 1.5
    
    ltv = loan_amount / existing_assets_value
    z_ltv = (0.75 - ltv) / 0.4
    
    z_tre_han = -1.25 * so_lan_tre_han_2_nam
    z_no_xau = -2.20 * (lich_su_no_xau == "Có").astype(int)
    z_nhom_no = np.where(
        nhom_no_cic == "Nhóm 1 (Đủ tiêu chuẩn)", 0.6,
        np.where(nhom_no_cic == "Nhóm 2 (Cần chú ý)", -0.8,
        np.where(nhom_no_cic == "Nhóm 3 (Dưới tiêu chuẩn)", -2.5,
        np.where(nhom_no_cic == "Nhóm 4 (Nghi ngờ)", -4.0, -6.0)))
    )

    logit = (
        1.15 * z_cic +
        0.80 * z_dti +
        0.70 * z_lti +
        0.55 * z_ltv +
        z_tre_han +
        z_no_xau +
        z_nhom_no +
        rng.normal(0, 0.50, size=n_samples)
    )

    prob_approved = 1.0 / (1.0 + np.exp(-logit))

    # Luật loại trừ cứng (Hard Knockout Rules):
    # Khách hàng nợ nhóm 3, 4, 5 hoặc điểm CIC < 450 bị ngân hàng tự động từ chối
    prob_approved[np.isin(nhom_no_cic, ["Nhóm 3 (Dưới tiêu chuẩn)", "Nhóm 4 (Nghi ngờ)", "Nhóm 5 (Mất vốn)"])] = 0.0
    prob_approved[credit_score < 450] = 0.0
    prob_approved[so_lan_tre_han_2_nam >= 4] *= 0.10

    phe_duyet_khoan_vay = (rng.random(n_samples) < prob_approved).astype(int)

    df = pd.DataFrame({
        "ma_ho_so": [f"HS-{20260000 + i}" for i in range(n_samples)],
        "ho_ten": full_names,
        "tuoi": age,
        "gioi_tinh": gender,
        "tinh_trang_hon_nhan": marital_status,
        "so_nguoi_phu_thuoc": dependents,
        "trinh_do_hoc_van": education,
        "loai_hinh_nghe_nghiep": employment_type,
        "thu_nhap_thang_vnd": applicant_income,
        "thu_nhap_nguoi_dong_vay_vnd": coapplicant_income,
        "gia_tri_tai_san_dam_bao_vnd": existing_assets_value,
        "muc_dich_vay": loan_purpose,
        "so_tien_vay_vnd": loan_amount,
        "thoi_han_vay_thang": loan_term_months,
        "khu_vuc_sinh_song": property_area,
        "diem_tin_dung_cic": credit_score,
        "nhom_no_cic": nhom_no_cic,
        "so_lan_tre_han_2_nam": so_lan_tre_han_2_nam,
        "so_khoan_vay_hien_tai": so_khoan_vay_hien_tai,
        "lich_su_no_xau": lich_su_no_xau,
        "ty_le_dti": ty_le_dti,
        "phe_duyet_khoan_vay": phe_duyet_khoan_vay
    })

    # Dữ liệu thiếu thực tế (missing values) ~1.5% đến 2.5%
    if include_missing:
        missing_rates = {
            "so_nguoi_phu_thuoc": 0.015,
            "thu_nhap_nguoi_dong_vay_vnd": 0.01,
            "gia_tri_tai_san_dam_bao_vnd": 0.02,
            "diem_tin_dung_cic": 0.015,
            "ty_le_dti": 0.02
        }
        for col, rate in missing_rates.items():
            mask = rng.random(n_samples) < rate
            df.loc[mask, col] = np.nan

    return df


if __name__ == "__main__":
    out_dir = os.path.join("data", "raw")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "loan_data.csv")

    print("Đang tạo bộ dữ liệu tín dụng khách hàng Việt Nam (6,000 hồ sơ)...")
    dataset = generate_vietnamese_loan_dataset(n_samples=6000, random_state=42, include_missing=True)
    dataset.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"Đã lưu thành công dữ liệu vào: {out_path}")
    print(f"Kích thước: {dataset.shape}")
    print(f"Tỷ lệ phê duyệt khoản vay: {dataset['phe_duyet_khoan_vay'].mean():.2%}")
    print("\nVí dụ 3 hồ sơ đầu tiên:")
    print(dataset[["ma_ho_so", "ho_ten", "thu_nhap_thang_vnd", "so_tien_vay_vnd", "diem_tin_dung_cic", "nhom_no_cic", "phe_duyet_khoan_vay"]].head(3))
