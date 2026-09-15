import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import json
from fastapi.testclient import TestClient
from api.main import app

sys.stdout.reconfigure(encoding='utf-8')
client = TestClient(app)

valid_base = {
    "ma_ho_so": "HS-VERIFY-EDGE",
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

cases = [
    ("1. Tuổi = 15 (< 18)", {"tuoi": 15}),
    ("2. Tuổi = 75 (> 70)", {"tuoi": 75}),
    ("3. Thu nhập chính = -1.000.000", {"thu_nhap_thang_vnd": -1000000.0}),
    ("4. Thu nhập đồng vay = -500.000", {"thu_nhap_nguoi_dong_vay_vnd": -500000.0}),
    ("5. TSĐB = -1.000", {"gia_tri_tai_san_dam_bao_vnd": -1000.0}),
    ("6. Số tiền vay = 0", {"so_tien_vay_vnd": 0.0}),
    ("7. Số tiền vay = -100", {"so_tien_vay_vnd": -100.0}),
    ("8. Điểm CIC = 350 (< 400)", {"diem_tin_dung_cic": 350}),
    ("9. Điểm CIC = 900 (> 850)", {"diem_tin_dung_cic": 900}),
    ("10. DTI = -5% (< 0%)", {"ty_le_dti": -5.0}),
    ("11. DTI = 150% (> 100%)", {"ty_le_dti": 150.0}),
    ("12. Nghề nghiệp không hợp lệ ('Chuyên gia')", {"loai_hinh_nghe_nghiep": "Chuyên gia"}),
]

print("=" * 80)
print(f"{'STT & TÊN EDGE CASE':<35} | {'HTTP CODE':<10} | {'TRẠNG THÁI SERVER':<18} | {'THÔNG BÁO LỖI TIẾNG VIỆT'}")
print("=" * 80)

for name, patch in cases:
    payload = valid_base.copy()
    payload.update(patch)
    res = client.post("/predict", json=payload)
    status_str = "CHẶN THÀNH CÔNG" if res.status_code == 422 else f"LỖI ({res.status_code})"
    msg = ""
    try:
        data = res.json()
        if "message" in data:
            msg = data["message"]
        elif "detail" in data:
            msg = str(data["detail"])
    except:
        msg = res.text
    
    # Rút gọn message hiển thị
    short_msg = msg[:75] + "..." if len(msg) > 75 else msg
    print(f"{name:<35} | {res.status_code:<10} | {status_str:<18} | {short_msg}")

print("=" * 80)
