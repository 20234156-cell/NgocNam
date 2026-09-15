"""Every test owns its database and audit files; production files are never test targets."""
import hashlib
import secrets
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def protected_hashes():
    paths = list((ROOT / "models").glob("*")) + list((ROOT / "logs").glob("*"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def pytest_sessionstart(session):
    session.protected_baseline = protected_hashes()


def pytest_sessionfinish(session, exitstatus):
    if protected_hashes() != session.protected_baseline:
        session.exitstatus = 1
        raise AssertionError("Tests changed protected model artifacts or production logs")


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch, request):
    from src.audit import audit_logger
    from src.storage import store
    from src.auth import password_hash
    from api.main import app
    from fastapi.testclient import TestClient

    monkeypatch.setattr(store, "path", str(tmp_path / "credit.sqlite3"))
    monkeypatch.setattr(audit_logger, "log_dir", str(tmp_path / "logs"))
    monkeypatch.setattr(audit_logger, "log_file", str(tmp_path / "logs" / "audit.jsonl"))
    if not hasattr(request.module, "client") and "users" not in request.fixturenames:
        yield {}
        return
    password = secrets.token_urlsafe(20)
    hashed = password_hash(password)
    with store.transaction() as db:
        db.executemany("INSERT INTO users VALUES (?,?,?)", [(name, hashed, role) for name, role in
                       (("officer", "Loan Officer"), ("risk", "Risk Manager"), ("chair", "Committee Chair"))])
    clients = {}
    for name in ("officer", "risk", "chair"):
        client = TestClient(app)
        client.test_password = password
        client.headers["X-Credit-Client"] = "cockpit"
        response = client.post("/auth/login", json={"username": name, "password": password})
        assert response.status_code == 200
        clients[name] = client
    module_client = getattr(request.module, "client", None)
    if module_client is not None:
        module_client.cookies.clear()
        module_client.cookies.update(clients["risk"].cookies)
        module_client.headers["X-Credit-Client"] = "cockpit"
    yield clients
    for client in clients.values():
        client.close()


@pytest.fixture
def users(isolated_runtime):
    return isolated_runtime


@pytest.fixture
def prime():
    from src.sample_queue import get_loan_queue
    return {k: v for k, v in get_loan_queue()[0].items() if k != "trang_thai_so_bo"}
