import urllib.request
import json

sample_app = {
    "ma_ho_so": "HS-20268888",
    "ho_ten": "Nguyen Van A",
    "tuoi": 35,
    "gioi_tinh": "Nam",
    "tinh_trang_hon_nhan": "Đã kết hôn",
    "so_nguoi_phu_thuoc": 1,
    "trinh_do_hoc_van": "Cao đẳng / Đại học",
    "loai_hinh_nghe_nghiep": "Nhân viên văn phòng",
    "thu_nhap_thang_vnd": 25000000.0,
    "thu_nhap_nguoi_dong_vay_vnd": 5000000.0,
    "gia_tri_tai_san_dam_bao_vnd": 800000000.0,
    "muc_dich_vay": "Vay tiêu dùng sinh hoạt",
    "so_tien_vay_vnd": 150000000.0,
    "thoi_han_vay_thang": 24,
    "khu_vuc_sinh_song": "Nội thành / Đô thị",
    "diem_tin_dung_cic": 720,
    "nhom_no_cic": "Nhóm 1 (Đủ tiêu chuẩn)",
    "so_lan_tre_han_2_nam": 0,
    "so_khoan_vay_hien_tai": 1,
    "lich_su_no_xau": "Không",
    "ty_le_dti": 28.0
}

data = json.dumps(sample_app).encode("utf-8")
headers = {"Content-Type": "application/json"}

print("=== 1. TEST 3 CLICKS IN A ROW (SAME INPUT) ===")
for i in range(1, 4):
    req = urllib.request.Request("http://127.0.0.1:8000/predict", data=data, headers=headers)
    res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    print(f"Click #{i}: Run #{res.get('run_number')} | is_cached={res.get('is_cached_run')} | Request ID={res.get('request_id')[:8]}")

print("\n=== 2. TEST RE-ASSESSMENT WITH MODIFIED INCOME ===")
sample_app["thu_nhap_thang_vnd"] = 40000000.0
sample_app["ty_le_dti"] = 18.0
data2 = json.dumps(sample_app).encode("utf-8")
req4 = urllib.request.Request("http://127.0.0.1:8000/predict", data=data2, headers=headers)
res4 = json.loads(urllib.request.urlopen(req4).read().decode("utf-8"))
print(f"Re-assessment: Run #{res4.get('run_number')} | is_cached={res4.get('is_cached_run')} | Request ID={res4.get('request_id')[:8]}")
