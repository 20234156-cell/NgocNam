"""Authenticated credit decision support API. No external AI or banking calls."""
import json
import logging
import os
from io import BytesIO
from pathlib import Path

import numpy as np
import openpyxl
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import Field

from api.schemas import (LoanApplicationInput, PredictionResponse, CommitteeDecisionInput,
    BatchAssessRequest, BatchAssessResponse, PortfolioStressRequest, CoreBankingDisburseRequest,
    CoreBankingDisburseResponse, LoginInput, StrictInput)
from src import auth
from src.audit import audit_logger
from src.decision import decision_engine, FIELD_CONSTRAINTS, RiskTierEngine
from src.sample_queue import get_loan_queue
from src.storage import store
from src.workflow import assess, committee_decision, simulate_disbursement, check_case_access

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)
app = FastAPI(title="VIETCREDIT · Hỗ trợ thẩm định", version="1.3.0", docs_url=None, redoc_url=None,
              description="Model XGBoost 1.2.0 không đổi. Core Banking chỉ là mô phỏng.")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv(
    "CREDIT_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(","))
MODEL_LOADED = decision_engine._artifacts_loaded
# Compatibility aliases reference the same objects, never load a second pipeline.
complete_pipeline = decision_engine.complete_pipeline
preprocessor = decision_engine.preprocessor
best_model = decision_engine.best_model
feature_names = decision_engine.feature_names

FIELD_NAME_VI = {key: value["description"] for key, value in FIELD_CONSTRAINTS.items()}
PUBLIC = {"/", "/cockpit", "/ui", "/health", "/auth/login"}
RISK_ROUTES = {"/simulate-stress", "/simulate-stress/portfolio"}
AUDIT_ROUTES = {"/audit-logs"}


@app.middleware("http")
async def security_boundary(request: Request, call_next):
    path = request.url.path
    is_public = path in PUBLIC or path.startswith("/static/")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        # Custom header + same origin prevent cross-site form and fetch requests.
        origin = request.headers.get("origin")
        expected_origin = str(request.base_url).rstrip("/")
        if request.headers.get("x-credit-client") != "cockpit" or (origin and origin != expected_origin):
            return JSONResponse({"detail": "Nguồn yêu cầu không hợp lệ."}, status_code=403)
        try:
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 2_000_000:
                    return JSONResponse({"detail": "Yêu cầu vượt giới hạn 2 MB."}, status_code=413)
            request._body = bytes(body)
        except Exception:
            return JSONResponse({"detail": "Không đọc được yêu cầu."}, status_code=400)
    user = None
    if not is_public:
        user = await run_in_threadpool(auth.session_user, request.cookies.get("credit_session"))
        if not user:
            return JSONResponse({"detail": "Vui lòng đăng nhập."}, status_code=401, headers={"Cache-Control": "no-store"})
        if path in RISK_ROUTES and user["role"] != "Risk Manager":
            return JSONResponse({"detail": "Chỉ Quản trị rủi ro được chạy mô phỏng."}, status_code=403)
        if path in AUDIT_ROUTES and user["role"] not in {"Risk Manager", "Committee Chair"}:
            return JSONResponse({"detail": "Bạn không có quyền đọc nhật ký kiểm toán."}, status_code=403)
    request.state.user = user
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    errors = []
    for error in exc.errors():
        loc = list(error["loc"])
        field = str(loc[-1])
        # Never echo the submitted value or arbitrary exception context (PII).
        errors.append({"loc": loc, "field": field, "type": error["type"],
                       "message": f"{FIELD_NAME_VI.get(field, 'Trường dữ liệu')}: thiếu hoặc không hợp lệ."})
    return JSONResponse(status_code=422, content={"detail": errors, "errors_vi": errors,
                                                  "message": " ".join(e["message"] for e in errors)})


@app.exception_handler(Exception)
async def internal_error(request, exc):
    logger.error("Request failed: %s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "Không thể hoàn tất yêu cầu. Chưa xác nhận thành công; hãy thử lại với cùng mã yêu cầu."})


@app.get("/")
def root_info(request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return FileResponse(ROOT / "app" / "cockpit.html")
    return {"dich_vu": app.title, "phien_ban": app.version,
            "trang_thai": "Hoạt động" if MODEL_LOADED else "Lỗi nạp mô hình",
            "nguong_toi_uu_ngan_hang": decision_engine.optimal_threshold,
            "nguong_mac_dinh": decision_engine.default_threshold, "giao_dien_cockpit": "/cockpit"}


@app.get("/cockpit")
@app.get("/ui")
def ui():
    return FileResponse(ROOT / "app" / "cockpit.html")


@app.get("/health")
def health_check():
    if not MODEL_LOADED or not decision_engine._artifacts_loaded:
        raise HTTPException(503, "Artifacts chưa được xác minh hoặc không nạp được.")
    return {"status": "healthy", "model_loaded": True, "n_features": len(feature_names), "model_version": "1.2.0"}


@app.get("/docs", include_in_schema=False)
def api_documentation():
    return FileResponse(ROOT / "app" / "api-docs.html")


@app.post("/auth/login")
def login(payload: LoginInput, request: Request, response: Response):
    token, error = auth.login(payload.username, payload.password, request.client.host if request.client else "unknown")
    if error:
        raise HTTPException(429 if error == "limited" else 401,
                            "Quá nhiều lần đăng nhập. Thử lại sau 15 phút." if error == "limited" else "Tên đăng nhập hoặc mật khẩu không đúng.")
    response.set_cookie("credit_session", token, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https", max_age=auth.SESSION_SECONDS, path="/")
    return auth.session_user(token)


@app.get("/auth/me")
def me(request: Request):
    return request.state.user


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    auth.logout(request.cookies.get("credit_session"))
    response.delete_cookie("credit_session", path="/")
    return {"status": "signed_out"}


@app.get("/config")
def configuration():
    return {"fields": FIELD_CONSTRAINTS, "optimal_threshold": decision_engine.optimal_threshold,
            "default_threshold": decision_engine.default_threshold, "model_version": decision_engine.model_version,
            "model_loaded": MODEL_LOADED, "core_mode": "simulation_only"}


@app.post("/predict", response_model=PredictionResponse)
def predict_loan_approval(application: LoanApplicationInput, request: Request, use_optimal_threshold: bool = True):
    health_check()
    return assess(application, request.state.user, use_optimal_threshold)


@app.get("/queue")
def queue():
    return get_loan_queue()


@app.get("/cases/{case_id}/latest")
def latest_case(case_id: str, request: Request):
    with store.transaction() as db:
        check_case_access(db, case_id, request.state.user)
        row = db.execute("SELECT response FROM assessments WHERE case_id=? ORDER BY run DESC LIMIT 1", (case_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Hồ sơ chưa có kết quả thẩm định.")
        result = json.loads(row[0])
        saved = db.execute("SELECT response FROM committee WHERE assessment_id=?", (result["request_id"],)).fetchone()
        return {"assessment": result, "committee": json.loads(saved[0]) if saved else None}


@app.get("/cases")
def saved_cases(request: Request, q: str = Query(default="", max_length=80),
                limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    # Ownership follows the first assessment, even after a risk manager reassesses.
    condition = "instr(lower(a.case_id), lower(?)) > 0"
    params = [q.strip()]
    if request.state.user["role"] == "Loan Officer":
        condition += " AND json_extract(first.response, '$.created_by') = ?"
        params.append(request.state.user["username"])
    source = """FROM assessments a
        JOIN assessments first ON first.case_id=a.case_id
          AND first.run=(SELECT MIN(run) FROM assessments WHERE case_id=a.case_id)
        WHERE a.run=(SELECT MAX(run) FROM assessments WHERE case_id=a.case_id) AND """ + condition
    with store.transaction() as db:
        total = db.execute("SELECT COUNT(*) " + source, params).fetchone()[0]
        rows = db.execute("SELECT a.response " + source + " ORDER BY a.created DESC, a.case_id LIMIT ? OFFSET ?",
                          [*params, limit, offset]).fetchall()
        items = []
        for row in rows:
            result = json.loads(row[0])
            saved = db.execute("SELECT response FROM committee WHERE assessment_id=?", (result["request_id"],)).fetchone()
            items.append({key: result.get(key) for key in (
                "ma_ho_so", "request_id", "run_number", "assessed_at", "created_by",
                "so_tien_vay_vnd", "xac_suat_phe_duyet", "ket_qua")})
            items[-1]["committee_decision"] = json.loads(saved[0])["final_decision"] if saved else None
        return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/cases/{case_id}/history")
def case_history(case_id: str, request: Request, limit: int = Query(default=20, ge=1, le=100),
                 offset: int = Query(default=0, ge=0)):
    with store.transaction() as db:
        check_case_access(db, case_id, request.state.user)
        total = db.execute("SELECT COUNT(*) FROM assessments WHERE case_id=?", (case_id,)).fetchone()[0]
        if not total:
            raise HTTPException(404, "Hồ sơ chưa có kết quả thẩm định.")
        rows = db.execute("SELECT response FROM assessments WHERE case_id=? ORDER BY run DESC LIMIT ? OFFSET ?",
                          (case_id, limit, offset)).fetchall()
        items = []
        for row in rows:
            assessment = json.loads(row[0])
            saved = db.execute("SELECT response FROM committee WHERE assessment_id=?", (assessment["request_id"],)).fetchone()
            items.append({"assessment": assessment, "committee": json.loads(saved[0]) if saved else None})
        return {"items": items, "total": total, "limit": limit, "offset": offset}


@app.get("/audit-logs")
def get_recent_audit_logs(limit: int = Query(default=100, ge=1, le=500)):
    # Historical files stay untouched; free text is redacted when exposed to clients.
    records = store.recent_events(limit) + audit_logger.read_recent_logs(limit)
    return sorted(records, key=lambda r: r.get("timestamp", ""), reverse=True)[:limit]


@app.post("/audit/committee-decision")
def record_committee_decision(payload: CommitteeDecisionInput, request: Request):
    return committee_decision(payload, request.state.user)


@app.post("/queue/batch-assess", response_model=BatchAssessResponse)
def batch_assess_applications(payload: BatchAssessRequest, request: Request):
    health_check()
    if not payload.use_optimal_threshold and request.state.user["role"] != "Risk Manager":
        raise HTTPException(403, "Chỉ Quản trị rủi ro được dùng ngưỡng so sánh.")
    ids = [a.ma_ho_so for a in payload.applications]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Mỗi hồ sơ chỉ xuất hiện một lần trong lô.")
    results, errors = [], []
    for index, application in enumerate(payload.applications):
        try:
            results.append(assess(application, request.state.user, payload.use_optimal_threshold, "batch_assessment"))
        except HTTPException as exc:
            errors.append({"index": index, "ma_ho_so": application.ma_ho_so, "message": exc.detail})
        except Exception:
            errors.append({"index": index, "ma_ho_so": application.ma_ho_so, "message": "Không hoàn tất thẩm định hồ sơ."})
    approved = sum(r.ma_ket_qua for r in results)
    return {"results": results, "errors": errors, "summary": {
        "tong_so_ho_so": len(payload.applications), "so_luong_thanh_cong": len(results), "so_luong_loi": len(errors),
        "so_luong_duyet": approved, "so_luong_tu_choi": len(results) - approved,
        "ty_le_duyet_pct": round(100 * approved / len(results), 2) if results else 0,
        "tong_han_muc_de_xuat_vnd": sum(r.so_tien_vay_vnd for r in results if r.ma_ket_qua),
        "so_ca_vi_pham_chinh_sach": sum(r.hard_rule_violated for r in results)}}


@app.get("/feature-importance")
def get_global_feature_importance(top_k: int = Query(default=15, ge=1, le=54)):
    health_check()
    values = [{"feature": n, "importance": float(v)} for n, v in zip(feature_names, best_model.feature_importances_)]
    return sorted(values, key=lambda x: x["importance"], reverse=True)[:top_k]


class StressSimulationRequest(StrictInput):
    application: LoanApplicationInput
    income_drop_pct: float = Field(default=0, ge=0, le=50)
    rate_hike_pct: float = Field(default=0, ge=0, le=10)
    collateral_drop_pct: float = Field(default=0, ge=0, le=50)
    cic_drop_pts: int = Field(default=0, ge=0, le=200)


def stress_pair(application, income_drop, rate_hike, collateral_drop, cic_drop):
    base = application.model_dump()
    stressed = base.copy()
    stressed["thu_nhap_thang_vnd"] *= 1 - income_drop / 100
    stressed["gia_tri_tai_san_dam_bao_vnd"] *= 1 - collateral_drop / 100
    stressed["diem_tin_dung_cic"] = max(400, stressed["diem_tin_dung_cic"] - cic_drop)
    household_before = base["thu_nhap_thang_vnd"] + base["thu_nhap_nguoi_dong_vay_vnd"]
    household_after = stressed["thu_nhap_thang_vnd"] + stressed["thu_nhap_nguoi_dong_vay_vnd"]
    # Explicit sensitivity assumption, not a PD model or a regulatory provisioning formula.
    stressed["ty_le_dti"] = min(100, base["ty_le_dti"] * household_before / household_after * (1 + rate_hike * .05))
    a = decision_engine.assess_application(base, client_source="stress", skip_audit=True)
    b = decision_engine.assess_application(stressed, client_source="stress", skip_audit=True)
    def brief(r):
        return {"xac_suat": r["xac_suat_phe_duyet"], "ket_qua": r["ket_qua"], "ma_ket_qua": r["is_approved"],
                "muc_do_rui_ro": r["muc_do_rui_ro"], "hard_rule_violated": r["hard_rule_violated"],
                "nguong_quyet_dinh": r["nguong_quyet_dinh"]}
    return a, b, {"baseline": brief(a), "stressed": brief(b),
                 "delta_prob": round(b["xac_suat_phe_duyet"] - a["xac_suat_phe_duyet"], 2),
                 "stressed_inputs": {k: stressed[k] for k in ("thu_nhap_thang_vnd", "gia_tri_tai_san_dam_bao_vnd", "diem_tin_dung_cic", "ty_le_dti")},
                 "khuyen_nghi_chieu_tai": "Phân tích độ nhạy xác suất phê duyệt, không phải xác suất vỡ nợ. DTI phản ánh giảm thu nhập; lãi suất dùng hệ số độ nhạy 5% mỗi điểm phần trăm. Model giữ lãi suất tham chiếu 8,5% và giới hạn tiền xử lý đã huấn luyện."}


@app.post("/simulate-stress")
def simulate_stress_scenario(params: StressSimulationRequest):
    health_check()
    return stress_pair(params.application, params.income_drop_pct, params.rate_hike_pct,
                       params.collateral_drop_pct, params.cic_drop_pts)[2]


@app.post("/simulate-stress/portfolio")
def simulate_portfolio_stress(req: PortfolioStressRequest):
    health_check()
    if req.applications is not None and req.case_ids is not None:
        raise HTTPException(422, "Chọn danh sách hồ sơ hoặc mã hồ sơ, không gửi cả hai.")
    if req.applications is not None:
        profiles = req.applications
    else:
        samples = get_loan_queue()
        known = {x["ma_ho_so"] for x in samples}
        if req.case_ids and req.case_ids != ["all_queue"] and not set(req.case_ids) <= known:
            raise HTTPException(422, "Có mã hồ sơ không tồn tại trong danh sách mẫu.")
        selected = samples if not req.case_ids or req.case_ids == ["all_queue"] else [x for x in samples if x["ma_ho_so"] in req.case_ids]
        profiles = [LoanApplicationInput(**{k: v for k, v in x.items() if k != "trang_thai_so_bo"}) for x in selected]
    if not profiles or len({p.ma_ho_so for p in profiles}) != len(profiles):
        raise HTTPException(422, "Danh sách phải có hồ sơ và không được trùng mã.")
    # Order is derived from the existing risk engine's boundaries/labels; policy is the worst tier.
    tiers = [RiskTierEngine.get_risk_tier(p) for p in (.9, .7, .5, .1)]
    details = []
    for p in profiles:
        a, b, pair = stress_pair(p, -req.income_shock_pct, req.interest_shock_pct, -req.collateral_shock_pct, -req.cic_shock_points)
        rank_a = 4 if a["hard_rule_violated"] else tiers.index(a["muc_do_rui_ro"])
        rank_b = 4 if b["hard_rule_violated"] else tiers.index(b["muc_do_rui_ro"])
        details.append({"ma_ho_so": p.ma_ho_so, "ho_ten": p.ho_ten,
                        "baseline": pair["baseline"], "stressed": pair["stressed"],
                        "prob_delta": pair["delta_prob"], "tier_migrated": rank_b > rank_a,
                        "so_tien_vay_vnd": p.so_tien_vay_vnd})
    return {"details": details, "summary": {"total_cases": len(details),
        "baseline_approved_count": sum(d["baseline"]["ma_ket_qua"] for d in details),
        "stressed_approved_count": sum(d["stressed"]["ma_ket_qua"] for d in details),
        "baseline_knockout_count": sum(d["baseline"]["hard_rule_violated"] for d in details),
        "stressed_knockout_count": sum(d["stressed"]["hard_rule_violated"] for d in details),
        "migrated_higher_risk_count": sum(d["tier_migrated"] for d in details),
        "total_exposure_vnd": sum(d["so_tien_vay_vnd"] for d in details),
        "policy_note": "Độ nhạy phê duyệt trên dữ liệu mô phỏng. Không suy ra PD, NPL, EL hoặc mức trích lập dự phòng."}}


@app.post("/integration/core-banking/disburse", response_model=CoreBankingDisburseResponse)
def disburse_to_core_banking(req: CoreBankingDisburseRequest, request: Request):
    return simulate_disbursement(req, request.state.user)


@app.get("/export/excel/queue")
def export_queue_excel():
    profiles = get_loan_queue()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ho so mo phong"
    columns = ["ma_ho_so", "ho_ten", *FIELD_CONSTRAINTS]
    ws.append(["Mã hồ sơ", "Họ tên", *(FIELD_NAME_VI[c] for c in FIELD_CONSTRAINTS)])
    for profile in profiles:
        row = [profile.get(c, "") for c in columns]
        ws.append(["'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v for v in row])
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    output = BytesIO()
    wb.save(output)
    return Response(output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="ho_so_mo_phong.xlsx"'})


app.mount("/static", StaticFiles(directory=ROOT / "app"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("api.main:app", host="127.0.0.1", port=port)

