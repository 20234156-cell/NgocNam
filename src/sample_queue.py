"""Synthetic demonstration profiles; never a live customer queue."""
def get_loan_queue():
    """Danh sách 14 hồ sơ chờ duyệt thực tế - Đã chuẩn hóa 100% khớp từ điển huấn luyện mô hình."""
    return [
        {
            "ma_ho_so": "HS-2026-08492", "ho_ten": "Nguyễn Hoàng Long", "tuoi": 34, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 1, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Chủ doanh nghiệp", "thu_nhap_thang_vnd": 45000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 20000000.0, "gia_tri_tai_san_dam_bao_vnd": 1850000000.0,
            "muc_dich_vay": "Vay mua nhà / đất", "so_tien_vay_vnd": 500000000.0, "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 765,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 24.5, "trang_thai_so_bo": "Khả thi cao (Prime)"
        },
        {
            "ma_ho_so": "HS-2026-09121", "ho_ten": "Trần Minh Tuấn", "tuoi": 41, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 2, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Kinh doanh tự do", "thu_nhap_thang_vnd": 15000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 0.0, "gia_tri_tai_san_dam_bao_vnd": 300000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt", "so_tien_vay_vnd": 400000000.0, "thoi_han_vay_thang": 36,
            "khu_vuc_sinh_song": "Ngoại thành / Bán đô thị", "diem_tin_dung_cic": 480,
            "nhom_no_cic": "Nhóm 4 (Nghi ngờ)", "so_lan_tre_han_2_nam": 3, "so_khoan_vay_hien_tai": 3,
            "lich_su_no_xau": "Có", "ty_le_dti": 65.0, "trang_thai_so_bo": "Rủi ro nợ xấu (Subprime)"
        },
        {
            "ma_ho_so": "HS-2026-07743", "ho_ten": "Lê Thu Hà", "tuoi": 29, "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Độc thân", "so_nguoi_phu_thuoc": 0, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng", "thu_nhap_thang_vnd": 26000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 8000000.0, "gia_tri_tai_san_dam_bao_vnd": 900000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt", "so_tien_vay_vnd": 450000000.0, "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 615,
            "nhom_no_cic": "Nhóm 2 (Cần chú ý)", "so_lan_tre_han_2_nam": 1, "so_khoan_vay_hien_tai": 2,
            "lich_su_no_xau": "Không", "ty_le_dti": 48.5, "trang_thai_so_bo": "Cận biên phê duyệt"
        },
        {
            "ma_ho_so": "HS-2026-08119", "ho_ten": "Phạm Quốc Bảo", "tuoi": 45, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 2, "trinh_do_hoc_van": "Sau đại học",
            "loai_hinh_nghe_nghiep": "Cán bộ / Công chức", "thu_nhap_thang_vnd": 65000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 30000000.0, "gia_tri_tai_san_dam_bao_vnd": 4500000000.0,
            "muc_dich_vay": "Vay mua nhà / đất", "so_tien_vay_vnd": 1200000000.0, "thoi_han_vay_thang": 120,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 810,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 21.0, "trang_thai_so_bo": "Khách hàng VIP (Prime+)"
        },
        {
            "ma_ho_so": "HS-2026-08304", "ho_ten": "Vũ Thị Ngọc Ánh", "tuoi": 32, "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 1, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng", "thu_nhap_thang_vnd": 28000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 15000000.0, "gia_tri_tai_san_dam_bao_vnd": 1200000000.0,
            "muc_dich_vay": "Vay mua ô tô", "so_tien_vay_vnd": 400000000.0, "thoi_han_vay_thang": 60,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 720,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 32.5, "trang_thai_so_bo": "Khả thi cao (Prime)"
        },
        {
            "ma_ho_so": "HS-2026-08552", "ho_ten": "Đặng Văn Lâm", "tuoi": 38, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 2, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Kinh doanh tự do", "thu_nhap_thang_vnd": 35000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 10000000.0, "gia_tri_tai_san_dam_bao_vnd": 800000000.0,
            "muc_dich_vay": "Vay sản xuất kinh doanh", "so_tien_vay_vnd": 600000000.0, "thoi_han_vay_thang": 36,
            "khu_vuc_sinh_song": "Ngoại thành / Bán đô thị", "diem_tin_dung_cic": 635,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 1, "so_khoan_vay_hien_tai": 2,
            "lich_su_no_xau": "Không", "ty_le_dti": 42.0, "trang_thai_so_bo": "Cần thẩm định thêm"
        },
        {
            "ma_ho_so": "HS-2026-08671", "ho_ten": "Hoàng Kim Oanh", "tuoi": 27, "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Độc thân", "so_nguoi_phu_thuoc": 0, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng", "thu_nhap_thang_vnd": 22000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 0.0, "gia_tri_tai_san_dam_bao_vnd": 600000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt", "so_tien_vay_vnd": 200000000.0, "thoi_han_vay_thang": 36,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 690,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 28.0, "trang_thai_so_bo": "Khả thi cao (Prime)"
        },
        {
            "ma_ho_so": "HS-2026-08890", "ho_ten": "Đinh Quang Hải", "tuoi": 49, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 3, "trinh_do_hoc_van": "Trung học phổ thông",
            "loai_hinh_nghe_nghiep": "Công nhân / Lao động kỹ thuật", "thu_nhap_thang_vnd": 12000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 6000000.0, "gia_tri_tai_san_dam_bao_vnd": 400000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt", "so_tien_vay_vnd": 250000000.0, "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Nông thôn", "diem_tin_dung_cic": 510,
            "nhom_no_cic": "Nhóm 3 (Dưới tiêu chuẩn)", "so_lan_tre_han_2_nam": 2, "so_khoan_vay_hien_tai": 2,
            "lich_su_no_xau": "Có", "ty_le_dti": 52.0, "trang_thai_so_bo": "Chặn cứng (Nhóm 3 NHNN)"
        },
        {
            "ma_ho_so": "HS-2026-08991", "ho_ten": "Bùi Mai Phương", "tuoi": 35, "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 1, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng", "thu_nhap_thang_vnd": 38000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 22000000.0, "gia_tri_tai_san_dam_bao_vnd": 2200000000.0,
            "muc_dich_vay": "Vay mua nhà / đất", "so_tien_vay_vnd": 750000000.0, "thoi_han_vay_thang": 120,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 775,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 23.5, "trang_thai_so_bo": "Khả thi cao (Prime)"
        },
        {
            "ma_ho_so": "HS-2026-09012", "ho_ten": "Lý Gia Kiệt", "tuoi": 43, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 2, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Kinh doanh tự do", "thu_nhap_thang_vnd": 55000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 12000000.0, "gia_tri_tai_san_dam_bao_vnd": 1500000000.0,
            "muc_dich_vay": "Vay sản xuất kinh doanh", "so_tien_vay_vnd": 900000000.0, "thoi_han_vay_thang": 36,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 640,
            "nhom_no_cic": "Nhóm 2 (Cần chú ý)", "so_lan_tre_han_2_nam": 1, "so_khoan_vay_hien_tai": 3,
            "lich_su_no_xau": "Không", "ty_le_dti": 46.0, "trang_thai_so_bo": "Cận biên phê duyệt"
        },
        {
            "ma_ho_so": "HS-2026-09144", "ho_ten": "Ngô Thanh Vân", "tuoi": 31, "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Độc thân", "so_nguoi_phu_thuoc": 0, "trinh_do_hoc_van": "Sau đại học",
            "loai_hinh_nghe_nghiep": "Cán bộ / Công chức", "thu_nhap_thang_vnd": 42000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 0.0, "gia_tri_tai_san_dam_bao_vnd": 1600000000.0,
            "muc_dich_vay": "Vay mua ô tô", "so_tien_vay_vnd": 500000000.0, "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 750,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 26.0, "trang_thai_so_bo": "Khả thi cao (Prime)"
        },
        {
            "ma_ho_so": "HS-2026-09255", "ho_ten": "Cao Văn Thắng", "tuoi": 52, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 1, "trinh_do_hoc_van": "Trung học phổ thông",
            "loai_hinh_nghe_nghiep": "Công nhân / Lao động kỹ thuật", "thu_nhap_thang_vnd": 16000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 8000000.0, "gia_tri_tai_san_dam_bao_vnd": 500000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt", "so_tien_vay_vnd": 300000000.0, "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Ngoại thành / Bán đô thị", "diem_tin_dung_cic": 440,
            "nhom_no_cic": "Nhóm 5 (Mất vốn)", "so_lan_tre_han_2_nam": 4, "so_khoan_vay_hien_tai": 2,
            "lich_su_no_xau": "Có", "ty_le_dti": 58.0, "trang_thai_so_bo": "Chặn cứng (Nhóm 5 NHNN)"
        },
        {
            "ma_ho_so": "HS-2026-09378", "ho_ten": "Dương Thùy Linh", "tuoi": 37, "gioi_tinh": "Nữ",
            "tinh_trang_hon_nhan": "Đã kết hôn", "so_nguoi_phu_thuoc": 2, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Nhân viên văn phòng", "thu_nhap_thang_vnd": 31000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 18000000.0, "gia_tri_tai_san_dam_bao_vnd": 1400000000.0,
            "muc_dich_vay": "Vay mua nhà / đất", "so_tien_vay_vnd": 550000000.0, "thoi_han_vay_thang": 84,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 740,
            "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)", "so_lan_tre_han_2_nam": 0, "so_khoan_vay_hien_tai": 1,
            "lich_su_no_xau": "Không", "ty_le_dti": 29.5, "trang_thai_so_bo": "Khả thi cao (Prime)"
        },
        {
            "ma_ho_so": "HS-2026-09489", "ho_ten": "Tạ Đình Phong", "tuoi": 30, "gioi_tinh": "Nam",
            "tinh_trang_hon_nhan": "Độc thân", "so_nguoi_phu_thuoc": 0, "trinh_do_hoc_van": "Cao đẳng / Đại học",
            "loai_hinh_nghe_nghiep": "Kinh doanh tự do", "thu_nhap_thang_vnd": 24000000.0,
            "thu_nhap_nguoi_dong_vay_vnd": 0.0, "gia_tri_tai_san_dam_bao_vnd": 700000000.0,
            "muc_dich_vay": "Vay tiêu dùng sinh hoạt", "so_tien_vay_vnd": 350000000.0, "thoi_han_vay_thang": 48,
            "khu_vuc_sinh_song": "Nội thành / Đô thị", "diem_tin_dung_cic": 625,
            "nhom_no_cic": "Nhóm 2 (Cần chú ý)", "so_lan_tre_han_2_nam": 1, "so_khoan_vay_hien_tai": 2,
            "lich_su_no_xau": "Không", "ty_le_dti": 47.0, "trang_thai_so_bo": "Cận biên phê duyệt"
        }
    ]


