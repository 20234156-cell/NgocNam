import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('api/main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update schema imports
old_import = """from api.schemas import (
    LoanApplicationInput, PredictionResponse, ShapFactor,
    CommitteeDecisionInput, BatchAssessRequest, BatchAssessResponse, BatchAssessSummary
)"""

new_import = """from api.schemas import (
    LoanApplicationInput, PredictionResponse, ShapFactor,
    CommitteeDecisionInput, BatchAssessRequest, BatchAssessResponse, BatchAssessSummary,
    PortfolioStressRequest, PortfolioStressResponse, PortfolioStressSummary, PortfolioStressItem,
    CoreBankingDisburseRequest, CoreBankingDisburseResponse
)"""

if old_import in code:
    code = code.replace(old_import, new_import)
    print("1. Updated schema imports")
else:
    print("old_import not matched")

# 2. Add openpyxl and Response imports
if "from io import BytesIO" not in code:
    code = code.replace(
        "from fastapi.responses import HTMLResponse, FileResponse, JSONResponse",
        "from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response\nfrom io import BytesIO\nimport openpyxl\nfrom openpyxl.styles import Font, PatternFill, Alignment, Border, Side"
    )
    print("2. Added openpyxl and Response imports")

# 3. Update validation_exception_handler with Vietnamese field mapping
old_val_handler = """# Exception Handler hiển thị chi tiết lỗi 422 rõ ràng ra Console và Response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        msg = err.get("msg", "")
        input_val = err.get("input", "")
        errors.append(f"Trường '{loc}': {msg} (Nhận được: {repr(input_val)})")
    
    error_summary = " | ".join(errors)
    print(f"\\n[⚠️ 422 VALIDATION ERROR]: {error_summary}\\n")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": error_summary}
    )"""

new_val_handler = """FIELD_NAME_VI = {
    "tuoi": "Độ tuổi khách hàng (18 - 70 tuổi)",
    "gioi_tinh": "Giới tính (Nam/Nữ)",
    "tinh_trang_hon_nhan": "Tình trạng hôn nhân",
    "so_nguoi_phu_thuoc": "Số người phụ thuộc (0 - 8)",
    "trinh_do_hoc_van": "Trình độ học vấn",
    "loai_hinh_nghe_nghiep": "Loại hình nghề nghiệp",
    "thu_nhap_thang_vnd": "Thu nhập người vay chính (tối thiểu 1.000.000 VNĐ)",
    "thu_nhap_nguoi_dong_vay_vnd": "Thu nhập người đồng vay (tối thiểu 0 VNĐ)",
    "gia_tri_tai_san_dam_bao_vnd": "Giá trị tài sản đảm bảo (tối thiểu 0 VNĐ)",
    "muc_dich_vay": "Mục đích sử dụng vốn vay",
    "so_tien_vay_vnd": "Số tiền đề nghị vay (tối thiểu 10.000.000 VNĐ)",
    "thoi_han_vay_thang": "Thời hạn vay vốn (6 - 360 tháng)",
    "khu_vuc_sinh_song": "Khu vực sinh sống",
    "diem_tin_dung_cic": "Điểm tín dụng CIC (400 - 850)",
    "nhom_no_cic": "Nhóm nợ CIC",
    "so_lan_tre_han_2_nam": "Số lần chậm trả nợ trong 2 năm (0 - 10)",
    "so_khoan_vay_hien_tai": "Số khoản vay hiện tại (0 - 15)",
    "lich_su_no_xau": "Lịch sử nợ xấu",
    "ty_le_dti": "Tỷ lệ Nợ trên Thu nhập DTI (0 - 100%)"
}

# Exception Handler hiển thị chi tiết lỗi 422 rõ ràng ra Console và Response
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    errors_vi = []
    for err in exc.errors():
        loc_keys = [str(l) for l in err.get("loc", [])]
        raw_field = loc_keys[-1] if loc_keys else "unknown"
        friendly_name = FIELD_NAME_VI.get(raw_field, raw_field)
        msg = err.get("msg", "")
        input_val = err.get("input", "")
        
        # Dịch một số thông báo Pydantic phổ biến sang tiếng Việt chuẩn ngân hàng
        if "greater than or equal to" in msg:
            val_limit = msg.split("greater than or equal to")[-1].strip()
            vi_msg = f"Giá trị phải lớn hơn hoặc bằng {val_limit}"
        elif "less than or equal to" in msg:
            val_limit = msg.split("less than or equal to")[-1].strip()
            vi_msg = f"Giá trị phải nhỏ hơn hoặc bằng {val_limit}"
        elif "Input should be" in msg:
            vi_msg = f"Giá trị không thuộc danh mục ngân hàng cho phép"
        else:
            vi_msg = msg
            
        err_item = f"Trường '{friendly_name}': {vi_msg} (Dữ liệu gửi lên: {repr(input_val)})"
        errors.append(err_item)
        errors_vi.append({
            "field": raw_field,
            "field_name_vi": friendly_name,
            "message": vi_msg,
            "input": input_val
        })
    
    error_summary = " | ".join(errors)
    print(f"\\n[⚠️ 422 VALIDATION ERROR]: {error_summary}\\n")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": error_summary,
            "errors_vi": errors_vi
        }
    )"""

if old_val_handler in code:
    code = code.replace(old_val_handler, new_val_handler)
    print("3. Updated validation_exception_handler")
else:
    print("old_val_handler not matched")

# 4. Add Endpoints before `if __name__ == "__main__":`
new_endpoints = """
# ==============================================================================
# TÍCH HỢP P1: STRESS-TEST CẤP DANH MỤC (PORTFOLIO-LEVEL STRESS TESTING)
# ==============================================================================
@app.post("/simulate-stress/portfolio", response_model=PortfolioStressResponse, tags=["Mô phỏng Stress-test"])
def simulate_portfolio_stress(req: PortfolioStressRequest):
    \"\"\"
    Mô phỏng áp lực căng thẳng kinh tế vĩ mô trên toàn bộ danh mục hồ sơ hàng đợi:
    Áp 4 cú sốc: Thu nhập (-15%), Lãi suất (+2%), TSĐB (-20%), CIC (-30 điểm).
    Tách biệt hồ sơ Knockout, tính toán Projected NPL, ΔEL và khuyến nghị trích lập dự phòng.
    \"\"\"
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Mô hình chưa được nạp.")

    # 1. Xác định danh sách hồ sơ cần phân tích
    profiles_to_test = []
    if req.applications and len(req.applications) > 0:
        profiles_to_test = [a.model_dump() for a in req.applications]
    else:
        all_queue = get_loan_queue()
        if not req.case_ids or "all_queue" in req.case_ids or len(req.case_ids) == 0:
            profiles_to_test = all_queue
        else:
            profiles_to_test = [p for p in all_queue if p["ma_ho_so"] in req.case_ids]

    if not profiles_to_test:
        raise HTTPException(status_code=400, detail="Không tìm thấy hồ sơ nào để chạy mô phỏng danh mục.")

    details = []
    migrated_count = 0
    total_delta_el = 0.0
    total_exposure = 0.0
    baseline_npl_count = 0
    stressed_npl_count = 0
    knockout_count = 0

    for p in profiles_to_test:
        clean_p = {k: v for k, v in p.items() if k != "trang_thai_so_bo"}
        ma_ho_so = clean_p.get("ma_ho_so", "HS-UNKNOWN")
        ho_ten = clean_p.get("ho_ten", "Khách hàng")
        so_tien_vay = float(clean_p.get("so_tien_vay_vnd", 0.0))
        total_exposure += so_tien_vay

        # Kiểm tra quy tắc cứng (Policy Knockout)
        from src.decision import HardRulesEngine
        is_knockout, reason = HardRulesEngine.check_policy(clean_p)

        if is_knockout:
            knockout_count += 0
            baseline_npl_count += 1
            stressed_npl_count += 1
            details.append(PortfolioStressItem(
                ma_ho_so=ma_ho_so,
                ho_ten=ho_ten,
                is_hard_rule_knockout=True,
                policy_reason=reason,
                baseline_approval_prob=0.005,
                stressed_approval_prob=0.001,
                prob_delta=-0.004,
                baseline_tier="Rủi ro rất cao (Subprime)",
                stressed_tier="Rủi ro rất cao (Subprime)",
                tier_migrated=False,
                so_tien_vay_vnd=so_tien_vay,
                expected_loss_delta_vnd=0.0
            ))
            continue

        # Chạy baseline qua Decision Engine
        res_base = decision_engine.assess_application(clean_p, client_source="portfolio_stress_base")
        p_base = float(res_base["xac_suat_phe_duyet"]) / 100.0
        tier_base = res_base["muc_do_rui_ro"]

        # Tạo hồ sơ stressed
        stressed_p = clean_p.copy()
        inc = float(stressed_p["thu_nhap_thang_vnd"])
        stressed_p["thu_nhap_thang_vnd"] = max(1_000_000.0, inc * (1.0 + req.income_shock_pct / 100.0))
        
        coll = float(stressed_p["gia_tri_tai_san_dam_bao_vnd"])
        stressed_p["gia_tri_tai_san_dam_bao_vnd"] = max(0.0, coll * (1.0 + req.collateral_shock_pct / 100.0))
        
        cic = int(stressed_p["diem_tin_dung_cic"])
        stressed_p["diem_tin_dung_cic"] = max(400, min(850, cic + req.cic_shock_points))
        
        dti = float(stressed_p["ty_le_dti"])
        if req.interest_shock_pct > 0:
            extra_dti = (req.interest_shock_pct * 0.05) * dti
            stressed_p["ty_le_dti"] = min(98.0, dti + extra_dti)

        res_stress = decision_engine.assess_application(stressed_p, client_source="portfolio_stress_shock")
        p_stress = float(res_stress["xac_suat_phe_duyet"]) / 100.0
        tier_stress = res_stress["muc_do_rui_ro"]

        # Đánh giá di chuyển tầng rủi ro
        tier_order = {"Rủi ro thấp": 1, "Rủi ro trung bình": 2, "Rủi ro cao": 3}
        migrated = (tier_order.get(tier_stress, 2) > tier_order.get(tier_base, 2))
        if migrated:
            migrated_count += 1

        if p_base < 0.50:
            baseline_npl_count += 1
        if p_stress < 0.50:
            stressed_npl_count += 1

        # Tính Delta EL = Delta PD * LGD * EAD
        delta_pd = max(0.0, p_base - p_stress)
        lgd = 0.45  # Chuẩn bán lẻ Basel II / NHNN
        delta_el = delta_pd * lgd * so_tien_vay
        total_delta_el += delta_el

        details.append(PortfolioStressItem(
            ma_ho_so=ma_ho_so,
            ho_ten=ho_ten,
            is_hard_rule_knockout=False,
            policy_reason=None,
            baseline_approval_prob=round(p_base * 100, 2),
            stressed_approval_prob=round(p_stress * 100, 2),
            prob_delta=round((p_stress - p_base) * 100, 2),
            baseline_tier=tier_base,
            stressed_tier=tier_stress,
            tier_migrated=migrated,
            so_tien_vay_vnd=so_tien_vay,
            expected_loss_delta_vnd=round(delta_el, 0)
        ))

    total_cases = len(details)
    base_npl_pct = round((baseline_npl_count / total_cases) * 100, 2) if total_cases > 0 else 0.0
    stress_npl_pct = round((stressed_npl_count / total_cases) * 100, 2) if total_cases > 0 else 0.0

    # Trích lập dự phòng theo TT11: 0.75% dự phòng chung + 100% phần Delta EL gia tăng
    provision_rec = round(total_exposure * 0.0075 + total_delta_el, 0)

    summary = PortfolioStressSummary(
        total_cases=total_cases,
        knockout_cases=knockout_count,
        model_evaluated_cases=total_cases - knockout_count,
        baseline_npl_ratio_pct=base_npl_pct,
        stressed_npl_ratio_pct=stress_npl_pct,
        npl_increase_pct=round(stress_npl_pct - base_npl_pct, 2),
        total_exposure_vnd=total_exposure,
        total_delta_expected_loss_vnd=round(total_delta_el, 0),
        migrated_higher_risk_count=migrated_count,
        provisioning_recommendation_vnd=provision_rec,
        policy_note="Tuân thủ Thông tư 11/2021/TT-NHNN: Dự phòng chung 0.75% trên tổng dư nợ và dự phòng cụ thể theo độ trượt nhóm rủi ro."
    )

    return PortfolioStressResponse(summary=summary, details=details)


# ==============================================================================
# TÍCH HỢP P1: CỔNG KẾT NỐI GIẢ LẬP CORE BANKING (CORE BANKING MOCK GATEWAY)
# ==============================================================================
CORE_IDEMPOTENCY_CACHE = {}

@app.post("/integration/core-banking/disburse", response_model=CoreBankingDisburseResponse, tags=["Tích hợp Core Banking"])
def disburse_to_core_banking(req: CoreBankingDisburseRequest):
    \"\"\"
    Cổng kết nối giả lập Core Banking (T24 / Flexcube):
    Kiểm tra quyền hạn (Committee Chair), xác thực Idempotency Key,
    sinh mã giao dịch hạch toán ngân hàng chuẩn (FT), và ghi bản ghi kiểm toán.
    \"\"\"
    # 1. Kiểm tra RBAC: Chỉ Committee Chair mới có quyền ký giải ngân sang Core
    if req.role != "Committee Chair":
        raise HTTPException(
            status_code=403,
            detail="Truy cập bị từ chối: Chỉ Chủ tịch Hội đồng Tín dụng (Committee Chair) mới có thẩm quyền phê duyệt lệnh giải ngân sang Core Banking."
        )

    # 2. Kiểm tra Idempotency Key chống trùng lặp giao dịch
    if req.idempotency_key in CORE_IDEMPOTENCY_CACHE:
        cached_res = CORE_IDEMPOTENCY_CACHE[req.idempotency_key]
        return cached_res

    # 3. Sinh mã giao dịch chuẩn Core Banking (FT + yymmdd + 6 số ngẫu nhiên)
    import random
    from datetime import datetime
    now = datetime.now()
    ft_id = f"FT{now.strftime('%y%m%d')}{random.randint(100000, 999999)}"
    timestamp_iso = now.isoformat()

    response_data = CoreBankingDisburseResponse(
        success=True,
        ft_transaction_id=ft_id,
        status="DISPATCHED_TO_CORE",
        ma_ho_so=req.ma_ho_so,
        account_number=req.account_number or "998877665501",
        disbursed_amount_vnd=req.approved_limit_vnd,
        timestamp=timestamp_iso,
        idempotency_key=req.idempotency_key,
        core_system="T24-CoreBanking-vR24",
        message=f"Đã hạch toán giải ngân thành công khoản vay {req.ma_ho_so} vào tài khoản {req.account_number}. Mã giao dịch: {ft_id}"
    )

    # Lưu vào cache chống trùng
    CORE_IDEMPOTENCY_CACHE[req.idempotency_key] = response_data

    # Ghi nhận vào Audit Trail chính thức
    try:
        audit_logger.log_decision(
            request_id=f"CORE-DISBURSE-{ft_id}",
            ma_ho_so=req.ma_ho_so,
            prob_approved=1.0,
            threshold_applied=0.73,
            decision="DISPATCHED_TO_CORE",
            is_approved=True,
            risk_tier="Prime (Giải ngân)",
            hard_rule_violated=False,
            recommendation=f"Đã giải ngân {req.approved_limit_vnd:,.0f} VNĐ theo Quyết định Hội đồng",
            top_shap_factors=[],
            model_version="1.2.0",
            threshold_config_version="1.2.0",
            decision_engine_version="1.2.0",
            application_snapshot={
                "ma_ho_so": req.ma_ho_so,
                "ho_ten": req.ho_ten,
                "approved_limit_vnd": req.approved_limit_vnd,
                "interest_rate_pct": req.interest_rate_pct,
                "account_number": req.account_number,
                "ft_transaction_id": ft_id
            },
            extra_metadata={
                "client_source": "core_banking_gateway",
                "officer_id": req.officer_id,
                "idempotency_key": req.idempotency_key
            }
        )
    except Exception as e:
        print(f"Lỗi ghi audit core banking: {e}")

    return response_data


# ==============================================================================
# TÍCH HỢP P0: XUẤT FILE EXCEL NATIVE SERVER-SIDE (.XLSX)
# ==============================================================================
@app.get("/export/excel/queue", tags=["Xuất dữ liệu"])
def export_queue_excel():
    \"\"\"
    Xuất danh sách toàn bộ 14 hồ sơ hàng đợi ra file Excel (.xlsx) chuẩn OpenXML:
    Định dạng số tiền tệ (#,,##0 VNĐ), kẻ khung ô, tiêu đề xanh thương hiệu ngân hàng.
    \"\"\"
    queue_data = get_loan_queue()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hang Doi Tham Dinh"

    # Header styling
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="002045", end_color="002045", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    headers = [
        "Mã Hồ Sơ", "Họ & Tên", "Tuổi", "Giới Tính", "Hôn Nhân",
        "Học Vấn", "Nghề Nghiệp", "Thu Nhập Chính", "Thu Nhập Đồng Vay",
        "Giá Trị TSĐB", "Mục Đích Vay", "Số Tiền Vay", "Thời Hạn (Tháng)",
        "Khu Vực", "Điểm CIC", "Nhóm Nợ CIC", "Chậm Trả (2 Năm)",
        "Khoản Vay Mở", "Nợ Xấu Lịch Sử", "Tỷ Lệ DTI (%)", "Trạng Thái Sơ Bộ"
    ]

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    ws.row_dimensions[1].height = 26

    # Currency format: #,##0 "VNĐ"
    currency_fmt = '#,##0 "VNĐ"'

    for row_idx, item in enumerate(queue_data, start=2):
        ws.row_dimensions[row_idx].height = 20
        row_values = [
            item.get("ma_ho_so"),
            item.get("ho_ten"),
            item.get("tuoi"),
            item.get("gioi_tinh"),
            item.get("tinh_trang_hon_nhan"),
            item.get("trinh_do_hoc_van"),
            item.get("loai_hinh_nghe_nghiep"),
            float(item.get("thu_nhap_thang_vnd", 0)),
            float(item.get("thu_nhap_nguoi_dong_vay_vnd", 0)),
            float(item.get("gia_tri_tai_san_dam_bao_vnd", 0)),
            item.get("muc_dich_vay"),
            float(item.get("so_tien_vay_vnd", 0)),
            item.get("thoi_han_vay_thang"),
            item.get("khu_vuc_sinh_song"),
            item.get("diem_tin_dung_cic"),
            item.get("nhom_no_cic"),
            item.get("so_lan_tre_han_2_nam"),
            item.get("so_khoan_vay_hien_tai"),
            item.get("lich_su_no_xau"),
            float(item.get("ty_le_dti", 0)),
            item.get("trang_thai_so_bo")
        ]
        ws.append(row_values)
        
        for col_idx in range(1, len(row_values) + 1):
            c = ws.cell(row=row_idx, column=col_idx)
            c.border = thin_border
            # Áp format số tiền tệ cho các cột 8, 9, 10, 12
            if col_idx in [8, 9, 10, 12]:
                c.number_format = currency_fmt
                c.alignment = right_align
            elif col_idx in [1, 3, 4, 13, 15, 17, 18, 19, 21]:
                c.alignment = center_align
            elif col_idx == 20:
                c.number_format = '0.0"%"'
                c.alignment = right_align
            else:
                c.alignment = left_align

    # Tự động căn chỉnh độ rộng cột
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Danh_Sach_Ho_So_Tham_Dinh_VIETCREDIT_{openpyxl.utils.datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
"""

idx_main = code.rfind('if __name__ == "__main__":')
if idx_main != -1:
    code = code[:idx_main] + new_endpoints + "\n\n" + code[idx_main:]
    print("4. Added Portfolio Stress, Core Banking, and Excel endpoints")
else:
    code += new_endpoints
    print("4. Appended endpoints at end")

with open('api/main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully updated api/main.py!")
