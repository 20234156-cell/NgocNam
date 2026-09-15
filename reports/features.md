# TÀI LIỆU ĐẶC TRƯNG & FEATURE ENGINEERING
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
| 1 | `diem_tin_dung_cic` | 0.1364 | Cực kỳ then chốt (Top 1) |
| 2 | `chi_so_ap_luc_tai_chinh` | 0.1320 | Cực kỳ then chốt (Top 1) |
| 3 | `so_lan_tre_han_2_nam` | 0.0999 | Quan trọng (Top 2) |
| 4 | `ty_le_vay_tren_tai_san_ltv` | 0.0778 | Quan trọng (Top 2) |
| 5 | `ty_le_vay_tren_thu_nhap_nam` | 0.0623 | Quan trọng (Top 2) |
| 6 | `uoc_tinh_goc_lai_thang_vnd` | 0.0422 | Quan trọng (Top 2) |
| 7 | `so_tien_vay_vnd` | 0.0403 | Quan trọng (Top 2) |
| 8 | `ty_le_dti` | 0.0365 | Quan trọng (Top 2) |
| 9 | `ty_le_tra_gop_tren_thu_nhap` | 0.0264 | Bổ trợ thông tin |
| 10 | `thu_nhap_nguoi_dong_vay_vnd` | 0.0092 | Bổ trợ thông tin |
| 11 | `tong_thu_nhap_thang_vnd` | 0.0066 | Bổ trợ thông tin |
| 12 | `so_khoan_vay_hien_tai` | 0.0038 | Bổ trợ thông tin |
| 13 | `gia_tri_tai_san_dam_bao_vnd` | 0.0003 | Bổ trợ thông tin |
| 14 | `thoi_han_vay_thang` | 0.0000 | Bổ trợ thông tin |
| 15 | `thu_nhap_thang_vnd` | 0.0000 | Bổ trợ thông tin |
| 16 | `tuoi` | 0.0000 | Bổ trợ thông tin |

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
