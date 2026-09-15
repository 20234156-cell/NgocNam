"""Regressions for real authorization, transaction integrity, privacy and explanation."""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.storage import store, WorkflowStore


def assess(users, prime):
    response = users["officer"].post("/predict", json=prime)
    assert response.status_code == 200, response.text
    return response.json()


def approve(users, result, key="approve-test-key"):
    return users["chair"].post("/audit/committee-decision", json={
        "assessment_id": result["request_id"], "idempotency_key": key,
        "final_decision": "PHÊ DUYỆT", "approved_limit_vnd": result["so_tien_vay_vnd"], "interest_rate_pct": 8.5})


def test_unauthenticated_access_and_forged_role(users, prime):
    with TestClient(app) as anonymous:
        assert anonymous.get("/queue").status_code == 401
        assert anonymous.get("/audit-logs").status_code == 401
        assert anonymous.post("/predict", json=prime, headers={"X-Credit-Client": "cockpit"}).status_code == 401
    assert users["officer"].get("/audit-logs").status_code == 403
    assert users["officer"].post("/predict?use_optimal_threshold=false", json=prime).status_code == 403
    assert users["officer"].post("/simulate-stress", json={"application": prime}).status_code == 403
    result = assess(users, prime)
    forged = {"assessment_id": result["request_id"], "idempotency_key": "forged-role-key", "role": "Committee Chair",
              "final_decision": "PHÊ DUYỆT", "approved_limit_vnd": prime["so_tien_vay_vnd"], "interest_rate_pct": 8.5}
    assert users["officer"].post("/audit/committee-decision", json=forged).status_code == 422
    forged.pop("role")
    assert users["officer"].post("/audit/committee-decision", json=forged).status_code == 403


def test_cross_origin_logout_and_session_revocation(users):
    officer = users["officer"]
    assert officer.post("/auth/logout", json={}, headers={"Origin": "https://untrusted.invalid"}).status_code == 403
    token = officer.cookies.get("credit_session")
    assert officer.post("/auth/logout", json={}).status_code == 200
    officer.cookies.set("credit_session", token)
    assert officer.get("/auth/me").status_code == 401


def test_expired_sessions_and_password_reset_revoke_access(users):
    from src.auth import create_user
    import secrets
    create_user("officer", secrets.token_urlsafe(20), "Loan Officer", replace=True)
    assert users["officer"].get("/auth/me").status_code == 401
    with store.transaction() as db:
        db.execute("UPDATE sessions SET expires=0 WHERE username='risk'")
    assert users["risk"].get("/auth/me").status_code == 401


def test_login_rate_limit_and_body_limit(users):
    with TestClient(app) as client:
        client.headers["X-Credit-Client"] = "cockpit"
        for _ in range(10):
            assert client.post("/auth/login", json={"username": "absent", "password": "invalid"}).status_code == 401
        assert client.post("/auth/login", json={"username": "absent", "password": "invalid"}).status_code == 429
        assert client.post("/auth/login", content=b"x" * 2_000_001).status_code == 413


def test_local_documentation_and_security_headers(users):
    response = users["officer"].get("/docs")
    assert response.status_code == 200
    assert "cdn" not in response.text.lower()
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert users["officer"].get("/openapi.json").status_code == 200


def test_missing_input_and_validation_does_not_echo_pii(users, prime, capsys):
    assert users["officer"].post("/predict", json={}).status_code == 422
    malicious = "<img src=x onerror=alert(1)>"
    prime["tuoi"] = malicious
    response = users["officer"].post("/predict", json=prime)
    assert response.status_code == 422
    assert malicious not in response.text
    assert malicious not in capsys.readouterr().out
    assert store.recent_events() == []


def test_full_shap_additivity_and_pii_minimization(users, prime):
    prime["ho_ten"] = "<img src=x onerror=alert(1)>"
    result = assess(users, prime)
    assert len(result["shap_factors"]) == 54
    margin = result["shap_base_value"] + sum(f["shap_value"] for f in result["shap_factors"])
    assert abs(margin - result["fx_log_odds"]) < 1e-5
    assert abs(1 / (1 + np.exp(-margin)) - result["prob_from_log_odds"]) < 1e-6
    assert abs(result["prob_from_log_odds"] * 100 - result["xac_suat_phe_duyet"]) < .0051
    events = store.recent_events()
    assert prime["ho_ten"] not in json.dumps(events)
    with store.transaction() as db:
        persisted = db.execute("SELECT response FROM assessments").fetchone()[0]
    assert "ho_ten" not in persisted
    prime["ho_ten"] = "Tên đã sửa"
    changed = assess(users, prime)
    assert changed["request_id"] != result["request_id"]
    assert changed["ho_ten"] == "Tên đã sửa"


def test_stale_policy_and_comparison_assessments_cannot_be_approved(users, prime):
    old = assess(users, prime)
    prime["so_tien_vay_vnd"] += 1
    current = assess(users, prime)
    assert approve(users, old).status_code == 409
    prime["nhom_no_cic"] = "Nhóm 4 (Nghi ngờ)"
    knockout = assess(users, prime)
    assert knockout["hard_rule_violated"]
    assert approve(users, knockout).status_code == 409
    prime["nhom_no_cic"] = "Nhóm 1 (Đủ tiêu chuẩn)"
    comparison = users["risk"].post("/predict?use_optimal_threshold=false", json=prime).json()
    assert approve(users, comparison).status_code == 409


def test_committee_and_core_idempotency_survive_store_reopen(users, prime):
    result = assess(users, prime)
    decision = approve(users, result)
    assert decision.status_code == 200
    assert approve(users, result).json()["decision_id"] == decision.json()["decision_id"]
    assert approve(users, result, key="different-key").status_code == 409
    payload = {"decision_id": decision.json()["decision_id"], "account_number": "1234567890", "idempotency_key": "core-security-key"}
    endpoint = "/integration/core-banking/disburse"
    first = users["chair"].post(endpoint, json=payload)
    assert first.status_code == 200
    assert first.json()["status"] == "SIMULATED_NOT_DISBURSED"
    assert "1234567890" not in json.dumps(store.recent_events())
    assert len(WorkflowStore(store.path).recent_events()) == 3
    assert users["chair"].post(endpoint, json=payload).json() == first.json()
    payload["account_number"] = "9999999999"
    assert users["chair"].post(endpoint, json=payload).status_code == 409
    payload["idempotency_key"] = "another-core-key"
    assert users["chair"].post(endpoint, json=payload).status_code == 409


def test_concurrent_predictions_create_one_run(users, prime):
    token = users["officer"].cookies.get("credit_session")
    def run(_):
        with TestClient(app) as client:
            client.cookies.set("credit_session", token)
            return client.post("/predict", json=prime, headers={"X-Credit-Client": "cockpit"}).json()
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, range(3)))
    assert len({r["request_id"] for r in results}) == 1
    assert sum(not r["is_cached_run"] for r in results) == 1
    assert len(store.recent_events()) == 1


def test_event_failure_rolls_back_assessment(users, prime, monkeypatch):
    import src.workflow as workflow
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("test failure")
    monkeypatch.setattr(workflow, "record_event", fail)
    with TestClient(app, raise_server_exceptions=False) as client:
        client.cookies.update(users["officer"].cookies)
        response = client.post("/predict", json=prime, headers={"X-Credit-Client": "cockpit"})
        assert response.status_code == 500
        assert "test failure" not in response.text
    with store.transaction() as db:
        assert db.execute("SELECT count(*) FROM assessments").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


def test_append_only_events_reject_update_delete(users, prime):
    assess(users, prime)
    for command in ("UPDATE audit_events SET record='{}'", "DELETE FROM audit_events"):
        with pytest.raises(sqlite3.IntegrityError):
            with store.transaction() as db:
                db.execute(command)


def test_batch_failure_is_reported(users, prime, monkeypatch):
    import api.main as main
    original = main.assess
    def sometimes_fail(application, *args):
        if application.ma_ho_so == "HS-FAIL":
            raise RuntimeError("private diagnostic")
        return original(application, *args)
    monkeypatch.setattr(main, "assess", sometimes_fail)
    response = users["officer"].post("/queue/batch-assess", json={"applications": [prime, {**prime, "ma_ho_so": "HS-FAIL"}]})
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["tong_so_ho_so"] == 2
    assert data["summary"]["so_luong_loi"] == 1
    assert len(data["results"]) == len(data["errors"]) == 1
    assert "private diagnostic" not in response.text


def test_stress_zero_shock_exact_and_no_operational_audit(users, prime):
    response = users["risk"].post("/simulate-stress", json={"application": prime})
    data = response.json()
    assert data["baseline"] == data["stressed"]
    assert data["delta_prob"] == 0
    assert store.recent_events() == []
    response = users["risk"].post("/simulate-stress/portfolio", json={"income_shock_pct": -101})
    assert response.status_code == 422


def test_portfolio_detects_policy_migration(users, prime):
    prime["diem_tin_dung_cic"] = 600
    data = users["risk"].post("/simulate-stress/portfolio", json={"applications": [prime], "cic_shock_points": -200}).json()
    assert data["details"][0]["stressed"]["hard_rule_violated"]
    assert data["details"][0]["tier_migrated"]
    assert data["summary"]["migrated_higher_risk_count"] == 1


def test_modified_artifact_is_rejected_before_deserialization(tmp_path):
    from src.integrity import verify_artifacts
    (tmp_path / "best_model.joblib").write_bytes(b"not a trusted model")
    with pytest.raises(RuntimeError, match="integrity"):
        verify_artifacts(tmp_path)


def test_invalid_threshold_config_fails_closed(tmp_path):
    from src.decision import DecisionEngine
    path = tmp_path / "threshold.json"
    for payload in ("not json", '{"default_threshold":0.5,"optimal_threshold":2}'):
        path.write_text(payload)
        with pytest.raises((ValueError, KeyError)):
            DecisionEngine(config_path=str(path))
    with pytest.raises(FileNotFoundError):
        DecisionEngine(config_path=str(tmp_path / "absent.json"))


def test_research_cannot_overwrite_release():
    from src.integrity import require_experiment_directory
    for path in ("models", "models/other", "data/processed", "reports"):
        with pytest.raises(ValueError):
            require_experiment_directory(path)


def test_case_owner_survives_risk_reassessment(users, prime):
    from src.workflow import assess as run_assessment
    from api.schemas import LoanApplicationInput
    from fastapi import HTTPException
    assess(users, prime)
    with pytest.raises(HTTPException) as denied:
        run_assessment(LoanApplicationInput(**prime), {"username": "other", "role": "Loan Officer"})
    assert denied.value.status_code == 403
    assert len(store.recent_events()) == 1
    assert users["risk"].post("/predict", json=prime).status_code == 200
    assert users["officer"].get(f"/cases/{prime['ma_ho_so']}/latest").status_code == 200
    assert users["officer"].post("/predict", json=prime).status_code == 200


def test_maker_cannot_decide_even_after_another_reassessment(users, prime):
    result = users["chair"].post("/predict", json=prime).json()
    assert approve(users, result).status_code == 403
    result = users["risk"].post("/predict", json=prime).json()
    assert approve(users, result).status_code == 403
    with store.transaction() as db:
        assert db.execute("SELECT count(*) FROM committee").fetchone()[0] == 0


@pytest.mark.parametrize("offset", [-60, 86401])
def test_assessment_time_must_be_valid(users, prime, monkeypatch, offset):
    import src.workflow as workflow
    result = assess(users, prime)
    with store.transaction() as db:
        created = db.execute("SELECT created FROM assessments").fetchone()[0]
    monkeypatch.setattr(workflow.time, "time", lambda: created + offset)
    from api.schemas import CommitteeDecisionInput
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as denied:
        workflow.committee_decision(CommitteeDecisionInput(
            assessment_id=result["request_id"], idempotency_key="clock-check-key",
            final_decision="PHÊ DUYỆT", approved_limit_vnd=prime["so_tien_vay_vnd"], interest_rate_pct=8.5),
            {"username": "chair", "role": "Committee Chair"})
    assert denied.value.status_code == 409


@pytest.mark.parametrize("key", ["model_version", "threshold_config_version", "decision_engine_version"])
def test_old_release_cannot_be_approved(users, prime, monkeypatch, key):
    from src.decision import decision_engine
    result = assess(users, prime)
    monkeypatch.setattr(decision_engine, key, "test-next-release")
    assert approve(users, result).status_code == 409


def test_inconsistent_explanation_rolls_back(users, prime, monkeypatch):
    from src.decision import decision_engine
    original = decision_engine.assess_application
    def inconsistent(*args, **kwargs):
        result = original(*args, **kwargs)
        result["prob_from_log_odds"] = 0.123
        return result
    monkeypatch.setattr(decision_engine, "assess_application", inconsistent)
    assert users["officer"].post("/predict", json=prime).status_code == 503
    assert store.recent_events() == []
    with store.transaction() as db:
        assert db.execute("SELECT count(*) FROM assessments").fetchone()[0] == 0


def test_workflow_records_are_append_only(users, prime):
    result = assess(users, prime)
    decision = approve(users, result).json()
    assert users["chair"].post("/integration/core-banking/disburse", json={
        "decision_id": decision["decision_id"], "account_number": "1234567890",
        "idempotency_key": "append-only-core"}).status_code == 200
    for table in ("assessments", "committee", "core_simulations"):
        for sql in (f"UPDATE {table} SET response='{{}}'", f"DELETE FROM {table}"):
            with pytest.raises(sqlite3.IntegrityError):
                with store.transaction() as db:
                    db.execute(sql)


@pytest.mark.parametrize("username,password", [("   ", "x" * 12), (" user", "x" * 12), ("user", "x" * 257)])
def test_account_creation_matches_login_limits(username, password):
    from src.auth import create_user
    with pytest.raises(ValueError):
        create_user(username, password, "Loan Officer")
