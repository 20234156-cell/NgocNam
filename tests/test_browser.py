"""Browser regressions run only against an isolated loopback server and test database."""
import socket
import os
import threading
import time
from pathlib import Path

import pytest
from playwright.sync_api import expect


@pytest.fixture
def browser_page(users, tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    import uvicorn
    from api.main import app
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(.05)
        assert server.started
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            # No CDN, fonts or other external traffic is allowed during verification.
            external = []
            def route_request(route):
                if route.request.url.startswith(f"http://127.0.0.1:{port}/"):
                    route.continue_()
                else:
                    external.append(route.request.url)
                    route.abort()
            context.route("**/*", route_request)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{port}/cockpit")
            yield page, users, tmp_path
            assert not external
            assert not errors
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()


def sign_in(page, users, name):
    page.locator("#username").fill(name)
    page.locator("#password").fill(users[name].test_password)
    page.locator("#loginForm button").click()
    page.locator("#workspace").wait_for(state="visible")


def test_browser_saved_cases_and_history(browser_page, prime):
    page, users, _ = browser_page
    assert users['officer'].post('/predict', json=prime).status_code == 200
    sign_in(page, users, 'officer')
    menu = page.locator('nav [data-panel]:visible').all_text_contents()
    assert [label.strip().split()[0] for label in menu] == ['01', '02', '03', '04']
    page.locator('[data-panel="cases"]').click()
    expect(page.locator('#caseRows')).to_contain_text(prime['ma_ho_so'])
    page.locator('#caseRows button').first.click()
    expect(page.locator('#historyTitle')).to_contain_text(prime['ma_ho_so'])
    page.locator('#historyRows > details > summary').first.click()
    expect(page.locator('#historyRows')).to_contain_text('CIC')
    page.locator('#caseRows button').nth(1).click()
    expect(page.locator('#committeeContext')).to_contain_text(prime['ma_ho_so'])
    page.locator('[data-panel="cases"]').click()
    page.locator('#caseSearch').fill('NO-MATCH')
    page.locator('#searchCases').click()
    expect(page.locator('#caseRows tr')).to_have_count(0)
    page.locator('#logoutButton').click()
    expect(page.locator('#caseRows tr')).to_have_count(0)


def test_browser_assessment_shap_committee_and_mobile(browser_page):
    page, users, tmp_path = browser_page
    sign_in(page, users, "officer")
    assert page.locator("#thresholdPolicy").is_disabled()
    page.locator("#loadSample").click()
    case_id = page.locator("#ma_ho_so").input_value()
    page.locator("#ho_ten").fill('<img src=x onerror="window.piiXss=1">')
    page.locator("#assessButton").click()
    page.locator("#resultCard").wait_for(state="visible")
    expect(page.locator("#shapRows tr")).to_have_count(54)
    assert page.locator("#waterfall svg").count() == 1
    assert page.evaluate("window.piiXss || 0") == 0
    assert "0.73" in page.locator("#appliedThreshold").inner_text()
    evidence = Path(os.environ.get("CREDIT_UI_EVIDENCE_DIR", str(tmp_path)))
    evidence.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(evidence / "desktop.png"), full_page=True)
    page.locator("#toCommittee").click()
    assert page.locator("#saveDecision").is_disabled()
    page.locator("#logoutButton").click()
    page.locator("#loginView").wait_for(state="visible")
    sign_in(page, users, "chair")
    page.locator('[data-panel="committee"]').click()
    page.locator("#lookupCase").fill(case_id)
    page.locator("#lookupForm button").click()
    expect(page.locator("#saveDecision")).to_be_enabled()
    page.locator("#finalDecision").select_option("PHÊ DUYỆT")
    page.locator("#saveDecision").click()
    page.locator("#savedDecision").wait_for(state="visible")
    assert "chưa ký số" in page.locator("#savedDecisionText").inner_text()
    page.locator("#accountNumber").fill("1234567890")
    page.locator("#simulateCore").click()
    expect(page.locator("#coreResult")).to_contain_text("SIM-")
    assert "Không chuyển tiền" in page.locator("#coreResult").inner_text()
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=str(evidence / "mobile.png"), full_page=True)
    page.locator('[data-panel="assessment"]').click()
    page.locator("#thu_nhap_thang_vnd").fill("46000000")
    assert page.locator("#resultCard").is_hidden()
    assert page.locator("#saveDecision").is_disabled()
    print(f"Browser screenshots: {evidence}")


def test_browser_offline_does_not_fabricate_results(browser_page):
    page, users, _ = browser_page
    sign_in(page, users, "risk")
    page.locator("#loadSample").click()
    page.route("**/predict?*", lambda route: route.abort())
    page.locator("#assessButton").click()
    expect(page.locator("#notification")).to_have_class("error")
    assert page.locator("#resultCard").is_hidden()
    assert page.locator("#saveDecision").is_disabled()
    assert page.locator("#waterfall svg").count() == 0
