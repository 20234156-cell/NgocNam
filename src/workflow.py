"""Persist assessments and authorized human decisions without duplicating model rules."""
import hashlib
import json
import math
import time
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from api.schemas import PredictionResponse
from src.audit import audit_logger, safe_snapshot
from src.decision import decision_engine
from src.explainability import extract_top_shap_reasons
from src.storage import store


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def check_case_access(db, case_id, user):
    """Risk staff may reassess; this must not transfer the originating officer's access."""
    first = db.execute("SELECT response FROM assessments WHERE case_id=? ORDER BY run LIMIT 1",
                       (case_id,)).fetchone()
    if first and user["role"] == "Loan Officer" and json.loads(first[0]).get("created_by") != user["username"]:
        raise HTTPException(403, "Hồ sơ thuộc cán bộ khác; không được đọc hoặc ghi đè.")


def record_event(db, response, user, source, *, event_id=None, official=False, decision=None, snapshot=None, linked=None, terms=None):
    record = audit_logger.log_decision(
        request_id=event_id or response["request_id"], ma_ho_so=response["ma_ho_so"],
        prob_approved=response["prob_from_log_odds"], threshold_applied=response["nguong_quyet_dinh"],
        decision=decision or response["ket_qua"], is_approved=response["ma_ket_qua"],
        risk_tier=response["muc_do_rui_ro"], hard_rule_violated=response["hard_rule_violated"],
        recommendation=response["khuyen_nghi_nghiep_vu"], top_shap_factors=response["top_nhan_to_anh_huong"],
        model_version=response["model_version"], threshold_config_version=response["threshold_config_version"],
        decision_engine_version=response["decision_engine_version"], run_number=response["run_number"],
        application_snapshot=snapshot, is_official=official, triggered_by=source,
        extra_metadata={"client_source": source, "officer_id": user["username"], **(linked or {})}, persist=False)
    record["event_type"] = source
    # Model recommendation and human decision are separate facts.
    record["model_is_approved"] = response["ma_ket_qua"]
    if decision:
        record["is_approved"] = int(decision == "PHÊ DUYỆT") if source == "credit_committee" else None
    if terms:
        record.update(terms)
    db.execute("INSERT INTO audit_events(request_id,record) VALUES (?,?)",
               (record["request_id"], json.dumps(record, ensure_ascii=False)))
    return record


def assess(application, user, optimal=True, source="user_click"):
    if not optimal and user["role"] != "Risk Manager":
        raise HTTPException(403, "Chỉ Quản trị rủi ro được sử dụng ngưỡng so sánh.")
    decision_engine.ensure_artifacts_loaded()
    payload = application.model_dump()
    digest = fingerprint({"application": payload, "optimal": optimal, "actor": user["username"]})
    # Inference and audit commit atomically. Two workers cannot create the same run.
    with store.transaction() as db:
        now = time.time()
        check_case_access(db, application.ma_ho_so, user)
        latest = db.execute("SELECT * FROM assessments WHERE case_id=? ORDER BY run DESC LIMIT 1",
                            (application.ma_ho_so,)).fetchone()
        if latest and latest["fingerprint"] == digest and 0 <= now - latest["created"] < 10:
            response = json.loads(latest["response"])
            response.update(ho_ten=application.ho_ten, is_cached_run=True)
            return PredictionResponse(**response)
        run = latest["run"] + 1 if latest else 1
        result = decision_engine.assess_application(payload, use_optimal_threshold=optimal,
                    top_k_shap=3, run_number=run, client_source=source, skip_audit=True)
        all_factors = extract_top_shap_reasons(result["shap_values"], result["feature_names"],
                                              result["X_prep"][0], top_k=len(result["feature_names"]))
        # Full precision contributions are required for additivity, not rounded display values.
        by_name = dict(zip(result["feature_names"], result["shap_values"]))
        for factor in all_factors:
            factor["shap_value"] = float(by_name[factor["raw_feature"]])
        margin = result["shap_base_value"] + sum(f["shap_value"] for f in all_factors)
        probability = result["prob_from_log_odds"]
        if (not all(math.isfinite(v) for v in (margin, probability, result["fx_log_odds"],
                                               result["xac_suat_phe_duyet"]))
                or not 0 <= probability <= 1
                or abs(margin - result["fx_log_odds"]) > 1e-5
                or abs(probability - (1 + math.tanh(margin / 2)) / 2) > 1e-6
                or abs(probability * 100 - result["xac_suat_phe_duyet"]) > .0051):
            raise HTTPException(503, "Kết quả model và giải thích không nhất quán; chưa lưu thẩm định.")
        response = PredictionResponse(
            request_id=result["request_id"], ma_ho_so=application.ma_ho_so, ho_ten=application.ho_ten,
            ket_qua=result["ket_qua"], ma_ket_qua=result["is_approved"],
            xac_suat_phe_duyet=result["xac_suat_phe_duyet"], muc_do_rui_ro=result["muc_do_rui_ro"],
            nguong_quyet_dinh=result["nguong_quyet_dinh"], top_nhan_to_anh_huong=result["top_shap_factors"],
            khuyen_nghi_nghiep_vu=result["khuyen_nghi_nghiep_vu"], hard_rule_violated=result["hard_rule_violated"],
            policy_reason=result["policy_reason"], run_number=run,
            shap_base_value=result["shap_base_value"], fx_log_odds=result["fx_log_odds"],
            prob_from_log_odds=result["prob_from_log_odds"], shap_factors=all_factors,
            model_version=result["model_version"], threshold_config_version=result["threshold_config_version"],
            decision_engine_version=result["decision_engine_version"], so_tien_vay_vnd=application.so_tien_vay_vnd,
            assessed_at=iso_now())
        persisted = response.model_dump(exclude={"ho_ten"})
        persisted["application_snapshot"] = safe_snapshot(payload)
        persisted["created_by"] = user["username"]
        db.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?)",
                   (response.request_id, application.ma_ho_so, digest, now, run, json.dumps(persisted, ensure_ascii=False)))
        record_event(db, persisted, user, source, snapshot=payload)
        return response


def latest_assessment(db, request_id):
    row = db.execute("SELECT * FROM assessments WHERE request_id=?", (request_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Không tìm thấy lần thẩm định.")
    latest = db.execute("SELECT request_id FROM assessments WHERE case_id=? ORDER BY run DESC LIMIT 1",
                        (row["case_id"],)).fetchone()
    age = time.time() - row["created"]
    if latest[0] != request_id or not math.isfinite(age) or not 0 <= age <= 86400:
        raise HTTPException(409, "Kết quả đã cũ hoặc quá 24 giờ. Vui lòng thẩm định lại.")
    assessment = json.loads(row["response"])
    decision_engine.ensure_artifacts_loaded()
    if any(assessment.get(key) != getattr(decision_engine, key) for key in
           ("model_version", "threshold_config_version", "decision_engine_version")):
        raise HTTPException(409, "Phiên bản thẩm định không còn hiện hành. Vui lòng thẩm định lại.")
    return assessment


def committee_decision(payload, user):
    if user["role"] != "Committee Chair":
        raise HTTPException(403, "Chỉ Chủ tịch hội đồng được ghi quyết định chính thức.")
    digest = fingerprint({**payload.model_dump(), "actor": user["username"]})
    with store.transaction() as db:
        prior = db.execute("SELECT * FROM committee WHERE idempotency_key=?", (payload.idempotency_key,)).fetchone()
        if prior:
            if prior["fingerprint"] != digest:
                raise HTTPException(409, "Khóa lặp đã được dùng với nội dung khác.")
            return json.loads(prior["response"])
        assessment = latest_assessment(db, payload.assessment_id)
        authors = db.execute("SELECT response FROM assessments WHERE case_id=?", (assessment["ma_ho_so"],))
        if any(json.loads(row[0]).get("created_by") == user["username"] for row in authors):
            raise HTTPException(403, "Người đã thẩm định hồ sơ không được ghi quyết định hội đồng cho cùng hồ sơ.")
        if db.execute("SELECT 1 FROM committee WHERE assessment_id=?", (payload.assessment_id,)).fetchone():
            raise HTTPException(409, "Lần thẩm định này đã có quyết định. Hãy thẩm định lại khi hồ sơ thay đổi.")
        approving = payload.final_decision == "PHÊ DUYỆT"
        if approving:
            if assessment["hard_rule_violated"] or not assessment["ma_ket_qua"]:
                raise HTTPException(409, "Hồ sơ chưa đạt chính sách phê duyệt; không được bỏ qua kết quả thẩm định.")
            if assessment["nguong_quyet_dinh"] != decision_engine.optimal_threshold:
                raise HTTPException(409, "Cần thẩm định lại với ngưỡng chính thức trước khi phê duyệt.")
            if not 0 < payload.approved_limit_vnd <= assessment["so_tien_vay_vnd"]:
                raise HTTPException(422, "Hạn mức phải dương và không vượt khoản vay đã thẩm định.")
        elif payload.approved_limit_vnd != 0:
            raise HTTPException(422, "Quyết định không phê duyệt phải có hạn mức bằng 0.")
        decision_id = str(uuid.uuid4())
        response = {"status": "recorded", "decision_id": decision_id, "assessment_id": payload.assessment_id,
                    "ma_ho_so": assessment["ma_ho_so"], "final_decision": payload.final_decision,
                    "approved_limit_vnd": payload.approved_limit_vnd, "interest_rate_pct": payload.interest_rate_pct,
                    "officer_id": user["username"], "timestamp": iso_now(), "digital_signature": False}
        record = record_event(db, assessment, user, "credit_committee", event_id=decision_id, official=True,
                             decision=payload.final_decision, linked={"assessment_id": payload.assessment_id},
                             terms={"approved_limit_vnd": payload.approved_limit_vnd, "interest_rate_pct": payload.interest_rate_pct})
        # Terms are stored in the immutable committee row; audit links by decision ID.
        response["audit_record"] = record
        db.execute("INSERT INTO committee VALUES (?,?,?,?,?)", (decision_id, payload.assessment_id,
                   payload.idempotency_key, digest, json.dumps(response, ensure_ascii=False)))
        return response


def simulate_disbursement(payload, user):
    if user["role"] != "Committee Chair":
        raise HTTPException(403, "Chỉ Chủ tịch hội đồng được thực hiện mô phỏng.")
    digest = fingerprint({**payload.model_dump(), "actor": user["username"]})
    with store.transaction() as db:
        previous = db.execute("SELECT * FROM core_simulations WHERE idempotency_key=?", (payload.idempotency_key,)).fetchone()
        if previous:
            if previous["fingerprint"] != digest:
                raise HTTPException(409, "Khóa lặp đã được dùng với nội dung khác.")
            return json.loads(previous["response"])
        row = db.execute("SELECT * FROM committee WHERE decision_id=?", (payload.decision_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy quyết định hội đồng.")
        decision = json.loads(row["response"])
        assessment = latest_assessment(db, row["assessment_id"])
        if decision["final_decision"] != "PHÊ DUYỆT":
            raise HTTPException(409, "Chỉ mô phỏng cho quyết định đã phê duyệt.")
        if db.execute("SELECT 1 FROM core_simulations WHERE decision_id=?", (payload.decision_id,)).fetchone():
            raise HTTPException(409, "Quyết định đã được mô phỏng; không tạo giao dịch trùng.")
        simulation_id = "SIM-" + str(uuid.uuid4())
        response = {"success": True, "simulation_id": simulation_id, "decision_id": payload.decision_id,
                    "status": "SIMULATED_NOT_DISBURSED", "ma_ho_so": assessment["ma_ho_so"],
                    "account_masked": "*" * (len(payload.account_number) - 4) + payload.account_number[-4:],
                    "simulated_amount_vnd": decision["approved_limit_vnd"], "timestamp": iso_now(),
                    "message": "Đã ghi nhận mô phỏng. Không chuyển tiền, không kết nối ngân hàng."}
        db.execute("INSERT INTO core_simulations VALUES (?,?,?,?,?)", (simulation_id, payload.decision_id,
                   payload.idempotency_key, digest, json.dumps(response, ensure_ascii=False)))
        record_event(db, assessment, user, "core_simulation", event_id=simulation_id,
                     decision="SIMULATED_NOT_DISBURSED", linked={"decision_id": payload.decision_id})
        return response
