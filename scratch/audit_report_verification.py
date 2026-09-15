import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("KIỂM TRA ĐỐI CHIẾU 22 ĐIỂM BÁO CÁO CỦA USER VỚI MÃ NGUỒN HIỆN TẠI")
print("=" * 60)

# 1. API SCHEMAS & DROPDOWNS
with open('api/schemas.py', 'r', encoding='utf-8') as f:
    schema_code = f.read()

print("\n--- [LỖI 1 & 8]: Dropdown UI vs Categorical Vocabulary & Pydantic Enum/Literal ---")
print("api/schemas.py có dùng Literal:", "from typing import" in schema_code and "Literal" in schema_code)
types = ['GioiTinhType', 'TinhTrangHonNhanType', 'TrinhDoHocVanType', 'LoaiHinhNgheNghiepType', 'MucDichVayType', 'KhuVucSinhSongType', 'NhomNoCicType', 'LichSuNoXauType']
for t in types:
    print(f"  Schema Type '{t}':", t in schema_code)

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    cockpit_code = f.read()

options_check = {
    "Trung học phổ thông": "Trung học phổ thông" in cockpit_code,
    "THPT (sai cũ)": 'value="THPT"' in cockpit_code or '>THPT<' in cockpit_code,
    "Cán bộ / Công chức": "Cán bộ / Công chức" in cockpit_code,
    "Chuyên gia / Quản lý (sai cũ)": "Chuyên gia / Quản lý" in cockpit_code,
    "Vay tiêu dùng sinh hoạt": "Vay tiêu dùng sinh hoạt" in cockpit_code,
    "Vay tiêu dùng (sai cũ)": 'value="Vay tiêu dùng"' in cockpit_code or '>Vay tiêu dùng<' in cockpit_code,
    "Ngoại thành / Bán đô thị": "Ngoại thành / Bán đô thị" in cockpit_code,
    "Ngoại thành (sai cũ)": 'value="Ngoại thành"' in cockpit_code or '>Ngoại thành<' in cockpit_code,
    "Ly hôn / Góa": "Ly hôn / Góa" in cockpit_code,
    "Ly hôn (sai cũ)": 'value="Ly hôn"' in cockpit_code or '>Ly hôn<' in cockpit_code
}
for k, v in options_check.items():
    print(f"  Option UI '{k}':", v)

# Check queue endpoints in api/main.py
with open('api/main.py', 'r', encoding='utf-8') as f:
    api_main_code = f.read()

print("\n--- [LỖI 1.2]: 14 hồ sơ mẫu tại GET /queue ---")
queue_samples_has_wrong = ("Vay tiêu dùng" in api_main_code and "Vay tiêu dùng sinh hoạt" not in api_main_code) or ("THPT" in api_main_code and "Trung học phổ thông" not in api_main_code)
print("  GET /queue có chứa category sai cũ không:", queue_samples_has_wrong)

# 2. URL API HARD-CODE & ERROR HANDLING
print("\n--- [LỖI 2]: URL API hard-code & xử lý lỗi HTTP ---")
api_base = re.findall(r'const\s+API_BASE\s*=\s*[^;]+', cockpit_code)
print("  Khai báo API_BASE trong cockpit.html:", api_base)
has_hardcode_127 = 'fetch(\'http://127.0.0.1:8000/predict\'' in cockpit_code or 'fetch("http://127.0.0.1:8000/predict"' in cockpit_code
print("  Còn hardcode trực tiếp fetch http://127.0.0.1:8000/predict:", has_hardcode_127)

# Check error handling in predict
predict_error_handling = "res.status === 422" in cockpit_code or "HTTP" in cockpit_code
print("  Cockpit có xử lý chi tiết mã lỗi HTTP/422 không:")

# 3. TRAIN.PY & EVALUATE.PY MODEL SELECTION
print("\n--- [LỖI 3]: train.py / evaluate.py chọn mô hình (LR vs XGBoost) ---")
with open('src/train.py', 'r', encoding='utf-8') as f:
    train_code = f.read()
with open('src/evaluate.py', 'r', encoding='utf-8') as f:
    eval_code = f.read()

auto_select_model = "if auc_lr > auc_xgb" in train_code or "best_model_name" in train_code
print("  train.py có logic tự động chọn mô hình theo số liệu CV/Test không:", auto_select_model)
print("  train.py lưu classifier nào làm complete_pipeline:", "xgb_model" in train_code and "joblib.dump" in train_code)

# 4. AUDIT LOG DRIFT & TEST OVERWRITING
print("\n--- [LỖI 4]: logs/audit.jsonl schema drift & test_audit.py ghi đè production log ---")
with open('src/audit.py', 'r', encoding='utf-8') as f:
    audit_py_code = f.read()

print("  src/audit.py có schema_version:", "schema_version" in audit_py_code)
with open('tests/test_audit.py', 'r', encoding='utf-8') as f:
    test_audit_code = f.read()
uses_tmp_audit = "tmp_path" in test_audit_code or "AUDIT_LOG_DIR" in test_audit_code or "monkeypatch" in test_audit_code
print("  tests/test_audit.py dùng tmp_path/cách ly log production:", uses_tmp_audit)

# 5. SHAP DISPLAY FOR HARD RULE REJECTION
print("\n--- [LỖI 5]: SHAP factor hiển thị khi vi phạm Hard Rule ---")
with open('src/explainability.py', 'r', encoding='utf-8') as f:
    expl_code = f.read()
with open('src/decision.py', 'r', encoding='utf-8') as f:
    dec_code = f.read()
print("  decision.py có ẩn SHAP hoặc chú thích rõ ràng khi vi phạm Hard Rule không:")

# 6. MODEL LEARN ON NHÓM 4 (49.6% vs 0%)
print("\n--- [LỖI 6]: XGBoost predict_proba trên hồ sơ Nhóm 4 ngoài phân phối ---")
# We will inspect how hard rule wraps it.

# 7. SENSITIVE ATTRIBUTES (gioi_tinh, tinh_trang_hon_nhan) IN TRAINING
print("\n--- [LỖI 7]: Dùng trực tiếp gioi_tinh/tinh_trang_hon_nhan làm feature ---")
with open('src/feature_engineering.py', 'r', encoding='utf-8') as f:
    fe_code = f.read()
print("  gioi_tinh trong NUMERIC_FEATURES hoặc CATEGORICAL_FEATURES:", "gioi_tinh" in fe_code)

# 9. REQUIREMENTS.TXT PINNING
print("\n--- [LỖI 9]: requirements.txt pin version ---")
with open('requirements.txt', 'r', encoding='utf-8') as f:
    req_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
pinned_exact = [line for line in req_lines if '==' in line]
minimum_only = [line for line in req_lines if '>=' in line]
print(f"  requirements.txt: {len(pinned_exact)} pinned (==), {len(minimum_only)} unpinned (>=)")

# 10. PREPROCESSOR.TRANSFORM CALLED TWICE
print("\n--- [LỖI 10]: preprocessor.transform() gọi 2 lần/request trong assess_application() ---")
print("  assess_application transform count:")
transform_calls = re.findall(r'transform\(', dec_code)
print("  Số lần xuất hiện transform() trong decision.py:", len(transform_calls))

# 11. READ_RECENT_LOGS() DEQUE STREAMING
print("\n--- [LỖI 11]: read_recent_logs() đọc toàn bộ file hay streaming deque ---")
print("  audit.py sử dụng deque:", "deque" in audit_py_code)

# 12. README TEST COUNT & VERSION DISCREPANCIES
print("\n--- [LỖI 12 & 13]: README test counts & Version discrepancies ---")
with open('README.md', 'r', encoding='utf-8') as f:
    readme_code = f.read()
print("  README chứa '22/22':", "22/22" in readme_code)
print("  README chứa '9/9':", "9/9" in readme_code)
print("  README chứa '34' hoặc '37':", "34" in readme_code or "37" in readme_code)

# 14. COCKPIT.HTML VS INDEX.HTML DIFF
print("\n--- [LỖI 14]: cockpit.html vs index.html ---")
with open('app/index.html', 'r', encoding='utf-8') as f:
    index_code = f.read()
print("  cockpit.html == index.html:", cockpit_code == index_code)
print("  cockpit.html lines:", len(cockpit_code.splitlines()), "vs index.html lines:", len(index_code.splitlines()))

# 15. HARDRULES NONE TYPEERROR
print("\n--- [LỖI 15]: HardRulesEngine handling None explicitly ---")
with open('src/decision.py', 'r', encoding='utf-8') as f:
    dec_code = f.read()
print("  None check in HardRulesEngine:", "if cic_score is None:" in dec_code or "diem_tin_dung_cic is None" in dec_code or "data.get(\"diem_tin_dung_cic\") or" in dec_code)

# 16. CORS CONFIG IN API/MAIN.PY
print("\n--- [LỖI 16]: CORS allow_origins=['*'] + allow_credentials=False ---")
print("  CORS allow_credentials:", re.findall(r'allow_credentials\s*=\s*(?:True|False)', api_main_code))

# 17. TEST_CATEGORY_VOCABULARY.PY
print("\n--- [LỖI 17]: Test đối chiếu vocabulary & category không hợp lệ ---")
print("  tests/test_category_vocabulary.py tồn tại:", os.path.exists("tests/test_category_vocabulary.py"))

# 18. nhom_no_hien_tai
print("\n--- [LỖI 18]: Alias field nhom_no_hien_tai ---")
print("  nhom_no_hien_tai trong decision.py:", "nhom_no_hien_tai" in dec_code)

# 19. test_preprocessing fit on n=1
print("\n--- [LỖI 19]: test_preprocessing n=1 row ---")
with open('tests/test_preprocessing.py', 'r', encoding='utf-8') as f:
    tp_code = f.read()
print("  test_preprocessing.py có test với df > 1 dòng:", "len(df)" in tp_code or "iloc" in tp_code)

# 20. Python loop in data_generator.py
print("\n--- [LỖI 20]: data_generator.py vòng lặp thuần ---")
with open('src/data_generator.py', 'r', encoding='utf-8') as f:
    dg_code = f.read()
print("  Vòng lặp 'for i in range' trong data_generator.py:", "for i in range" in dg_code)

# 21. Dockerfile root user
print("\n--- [LỖI 21]: Dockerfile root user vs non-root user ---")
with open('Dockerfile', 'r', encoding='utf-8') as f:
    dk_code = f.read()
print("  Dockerfile có USER appuser / non-root:", "USER" in dk_code)

# 22. ASSUMPTIONS FICO 300-850 vs 400-850
print("\n--- [LỖI 22]: ASSUMPTIONS.md FICO 300-850 vs 400-850 ---")
with open('ASSUMPTIONS.md', 'r', encoding='utf-8') as f:
    assump_code = f.read()
print("  ASSUMPTIONS.md chứa '300':", "300" in assump_code)
