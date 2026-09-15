"""
Feature Engineering Module for Vietnamese Loan Approval Prediction System.
Module trích xuất đặc trưng tài chính nghiệp vụ ngân hàng Việt Nam.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo các chỉ số rủi ro và năng lực tài chính nghiệp vụ từ dữ liệu khách hàng Việt Nam.
    """
    df_out = df.copy()

    # 1. Tổng thu nhập hộ gia đình hàng tháng (VNĐ)
    thu_nhap_chinh = df_out["thu_nhap_thang_vnd"].fillna(df_out["thu_nhap_thang_vnd"].median())
    thu_nhap_phu = df_out["thu_nhap_nguoi_dong_vay_vnd"].fillna(0)
    df_out["tong_thu_nhap_thang_vnd"] = thu_nhap_chinh + thu_nhap_phu

    # 2. Tỷ lệ Khoản vay trên Tổng thu nhập năm (Loan-to-Income: LTI)
    thu_nhap_nam = np.maximum(df_out["tong_thu_nhap_thang_vnd"] * 12.0, 1.0)
    df_out["ty_le_vay_tren_thu_nhap_nam"] = df_out["so_tien_vay_vnd"] / thu_nhap_nam

    # 3. Tỷ lệ Khoản vay trên Tài sản đảm bảo (Loan-to-Value: LTV)
    tai_san = np.maximum(df_out["gia_tri_tai_san_dam_bao_vnd"].fillna(df_out["gia_tri_tai_san_dam_bao_vnd"].median()), 1.0)
    df_out["ty_le_vay_tren_tai_san_ltv"] = df_out["so_tien_vay_vnd"] / tai_san

    # 4. Ước tính Tiền trả góp gốc + lãi hàng tháng (VNĐ) theo phương pháp niên kim (lãi suất tham chiếu 8.5%/năm)
    r = 0.085 / 12.0
    n = np.maximum(df_out["thoi_han_vay_thang"], 12)
    # Công thức niên kim: P = L * [r(1+r)^n] / [(1+r)^n - 1]
    he_so_tra_gop = (r * ((1.0 + r) ** n)) / (((1.0 + r) ** n) - 1.0)
    df_out["uoc_tinh_goc_lai_thang_vnd"] = df_out["so_tien_vay_vnd"] * he_so_tra_gop

    # 5. Tỷ lệ Tiền trả góp trên Thu nhập tháng (Installment-to-Income: ITI)
    df_out["ty_le_tra_gop_tren_thu_nhap"] = df_out["uoc_tinh_goc_lai_thang_vnd"] / np.maximum(df_out["tong_thu_nhap_thang_vnd"], 1.0)

    # 6. Phân nhóm Điểm tín dụng CIC chuẩn
    cic = df_out["diem_tin_dung_cic"].fillna(df_out["diem_tin_dung_cic"].median())
    df_out["nhom_diem_cic"] = pd.cut(
        cic,
        bins=[0, 579, 669, 739, 799, 1000],
        labels=["Kém (<580)", "Trung bình (580-669)", "Khá (670-739)", "Tốt (740-799)", "Xuất sắc (800+)"]
    ).astype(str)

    # 7. Phân nhóm Độ tuổi khách hàng
    df_out["nhom_tuoi"] = pd.cut(
        df_out["tuoi"],
        bins=[18, 25, 35, 50, 60, 100],
        labels=["18-25", "26-35", "36-50", "51-60", "Trên 60"]
    ).astype(str)

    # 8. Chỉ số Áp lực Tài chính tổng hợp (Financial Stress Index)
    dti_val = df_out["ty_le_dti"].fillna(df_out["ty_le_dti"].median())
    no_xau_binary = (df_out["lich_su_no_xau"] == "Có").astype(float)
    df_out["chi_so_ap_luc_tai_chinh"] = (
        (dti_val / 45.0) +
        (df_out["so_lan_tre_han_2_nam"] * 1.5) +
        (no_xau_binary * 2.5)
    )

    return df_out


def run_feature_analysis(data_path: str = "data/raw/loan_data.csv", output_dir: str = "reports"):
    """
    Chạy feature engineering và xuất báo cáo features.md tiếng Việt.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(data_path, encoding="utf-8-sig")
    
    # Tạo đặc trưng
    df_feat = add_engineered_features(df)
    
    candidate_num = [
        "tuoi", "thu_nhap_thang_vnd", "thu_nhap_nguoi_dong_vay_vnd", "tong_thu_nhap_thang_vnd",
        "gia_tri_tai_san_dam_bao_vnd", "so_tien_vay_vnd", "thoi_han_vay_thang",
        "diem_tin_dung_cic", "so_lan_tre_han_2_nam", "so_khoan_vay_hien_tai",
        "ty_le_dti", "ty_le_vay_tren_thu_nhap_nam", "ty_le_vay_tren_tai_san_ltv",
        "uoc_tinh_goc_lai_thang_vnd", "ty_le_tra_gop_tren_thu_nhap", "chi_so_ap_luc_tai_chinh"
    ]
    
    # Tính Mutual Information với nhãn mục tiêu
    X_clean = df_feat[candidate_num].fillna(df_feat[candidate_num].median())
    y_clean = df_feat["phe_duyet_khoan_vay"]
    mi_scores = mutual_info_classif(X_clean, y_clean, random_state=42)
    mi_df = pd.DataFrame({
        "Feature": candidate_num,
        "Mutual_Information": np.round(mi_scores, 4)
    }).sort_values(by="Mutual_Information", ascending=False).reset_index(drop=True)

    md_content = f"""# TÀI LIỆU ĐẶC TRƯNG & FEATURE ENGINEERING
## Dự án: Hệ thống Dự đoán Khả năng Phê duyệt Khoản vay (Khách hàng Việt Nam)

---

### 1. Danh mục Đặc trưng Phái sinh Nghiệp vụ Ngân hàng Việt Nam
Để mô hình nắm bắt bản chất tài chính của hồ sơ vay, 8 đặc trưng nghiệp vụ đã được xây dựng:

1. **`tong_thu_nhap_thang_vnd`**: Tổng thu nhập hộ gia đình = Thu nhập khách hàng chính + Thu nhập người đồng vay.
2. **`ty_le_vay_tren_thu_nhap_nam` (LTI)**: Tỷ lệ số tiền đề nghị vay trên tổng thu nhập năm. Đo lường mức độ đòn bẩy nợ.
3. **`ty_le_vay_tren_tai_san_ltv` (LTV)**: Tỷ lệ số tiền vay trên giá trị tài sản đảm bảo (nhà đất sổ đỏ, ô tô, sổ tiết kiệm). Đo lường mức an toàn thu hồi nợ của ngân hàng.
4. **`uoc_tinh_goc_lai_thang_vnd`**: Nghĩa vụ trả góp gốc + lãi hàng tháng ước tính theo niên kim cố định.
5. **`ty_le_tra_gop_tren_thu_nhap` (ITI)**: Tỷ lệ tiền trả nợ hàng tháng trên tổng thu nhập tháng.
6. **`nhom_diem_cic`**: Phân loại mức độ tín nhiệm FICO/CIC (Kém, Trung bình, Khá, Tốt, Xuất sắc).
7. **`nhom_tuoi`**: Phân nhóm độ tuổi lao động.
8. **`chi_so_ap_luc_tai_chinh`**: Chỉ số composite kết hợp tỷ lệ nợ DTI, tần suất trễ hạn thanh toán và tiền sử nợ xấu.

---

### 2. Xếp hạng Tầm quan trọng của Đặc trưng (Mutual Information Score)
| Thứ hạng | Tên đặc trưng | Điểm Mutual Information | Đánh giá nghiệp vụ |
| :---: | :--- | :---: | :--- |
"""
    for idx, row in mi_df.iterrows():
        mi_val = row["Mutual_Information"]
        role = "Cực kỳ then chốt (Top 1)" if mi_val > 0.10 else ("Quan trọng (Top 2)" if mi_val > 0.03 else "Bổ trợ thông tin")
        md_content += f"| {idx+1} | `{row['Feature']}` | {mi_val:.4f} | {role} |\n"

    md_content += f"""
---

### 3. Danh sách Đặc trưng Đầu vào Pipeline Huấn luyện

**Nhóm biến số liên tục (Numerical Features - 15 biến):**
- `tuoi`, `so_nguoi_phu_thuoc`, `thu_nhap_thang_vnd`, `thu_nhap_nguoi_dong_vay_vnd`, `tong_thu_nhap_thang_vnd`
- `gia_tri_tai_san_dam_bao_vnd`, `so_tien_vay_vnd`, `thoi_han_vay_thang`, `diem_tin_dung_cic`
- `so_lan_tre_han_2_nam`, `so_khoan_vay_hien_tai`, `ty_le_dti`
- `ty_le_vay_tren_thu_nhap_nam`, `ty_le_vay_tren_tai_san_ltv`, `ty_le_tra_gop_tren_thu_nhap`, `chi_so_ap_luc_tai_chinh`

**Nhóm biến phân loại (Categorical Features - 8 biến):**
- `gioi_tinh`, `tinh_trang_hon_nhan`, `trinh_do_hoc_van`, `loai_hinh_nghe_nghiep`
- `muc_dich_vay`, `khu_vuc_sinh_song`, `nhom_no_cic`, `lich_su_no_xau`, `nhom_diem_cic`

Các biến định danh cá nhân (`ma_ho_so`, `ho_ten`) được loại bỏ khỏi ma trận đặc trưng huấn luyện để đảm bảo bảo mật và chống overfitting.
"""

    with open(os.path.join(output_dir, "features.md"), "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print("Feature engineering tiếng Việt hoàn tất! Xuất báo cáo tại reports/features.md.")
    return mi_df


if __name__ == "__main__":
    run_feature_analysis()
