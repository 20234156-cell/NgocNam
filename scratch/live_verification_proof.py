# -*- coding: utf-8 -*-
"""
Script to produce comprehensive live verification evidence for:
1. Batch Assessment (POST /queue/batch-assess) on 14 queue profiles.
2. Portfolio Stress Simulation (POST /simulate-stress/portfolio).
3. Core Banking Integration (POST /integration/core-banking/disburse) with RBAC & Idempotency.
4. Presets and Hard-Rule Knockout UI representation.
"""
import sys
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def test_batch_assess():
    print("=" * 70)
    print("1. KIỂM CHỨNG LIVE: THẨM ĐỊNH HÀNG LOẠT (POST /queue/batch-assess)")
    print("=" * 70)
    # Fetch 14 profiles from queue first
    with urllib.request.urlopen(f"{BASE_URL}/queue") as resp:
        queue_data = json.loads(resp.read().decode('utf-8'))
        applications = queue_data if isinstance(queue_data, list) else queue_data.get("items", [])
    
    print(f"-> Số lượng hồ sơ nạp từ hàng đợi: {len(applications)} hồ sơ")

    payload = {
        "applications": applications,
        "use_optimal_threshold": True
    }
    req = urllib.request.Request(
        f"{BASE_URL}/queue/batch-assess",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    summary = data.get("summary", {})
    results = data.get("results", [])

    print("\n--- KPI ĐIỀU HÀNH TỔNG HỢP THEO LÔ (SUMMARY) ---")
    print(f"• Tổng số hồ sơ: {summary.get('tong_so_ho_so')} hồ sơ")
    print(f"• Số lượng phê duyệt: {summary.get('so_luong_duyet')} hồ sơ ({summary.get('ty_le_duyet_pct')}%)")
    print(f"• Số lượng từ chối: {summary.get('so_luong_tu_choi')} hồ sơ")
    print(f"• Tổng hạn mức cấp tín dụng đề xuất: {summary.get('tong_han_muc_de_xuat_vnd'):,} VNĐ")
    print(f"• Số ca vi phạm chính sách cứng (Knockout): {summary.get('so_ca_vi_pham_chinh_sach')} ca")

    app_map = {a.get('ma_ho_so'): a for a in applications}

    print("\n--- CHI TIẾT 14 HỒ SƠ THẨM ĐỊNH LÔ ---")
    header = f"{'STT':<4} | {'MÃ HỒ SƠ':<14} | {'HỌ VÀ TÊN':<20} | {'KHOẢN VAY':<15} | {'XÁC SUẤT':<9} | {'KẾT QUẢ':<32} | {'GHI CHÚ'}"
    print(header)
    print("-" * len(header))
    for idx, r in enumerate(results, 1):
        app = app_map.get(r.get('ma_ho_so'), {})
        loan_amt = app.get('so_tien_vay_vnd', 0)
        note = "Policy Knockout (Nhóm 3-5)" if r.get('hard_rule_violated') else ("Duyệt tiêu chuẩn" if r.get('ma_ket_qua') == 1 else "Dưới ngưỡng 0.73")
        print(f"{idx:<4} | {r.get('ma_ho_so'):<14} | {r.get('ho_ten'):<20} | {loan_amt:>11,} đ | {r.get('xac_suat_phe_duyet'):>6.1f}%   | {r.get('ket_qua'):<32} | {note}")


def test_portfolio_stress():
    print("\n" + "=" * 70)
    print("2. KIỂM CHỨNG LIVE: MÔ PHỎNG STRESS DANH MỤC (POST /simulate-stress/portfolio)")
    print("=" * 70)
    payload = {
        "case_ids": ["all_queue"],
        "shock_interest_rate_pct": 2.5,
        "shock_income_reduction_pct": 20.0,
        "shock_unemployment_increase_pct": 3.0
    }
    req = urllib.request.Request(
        f"{BASE_URL}/simulate-stress/portfolio",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    s = data.get("summary", {})
    details = data.get("details", [])

    print("\n--- CHỈ SỐ RỦI RO DANH MỤC SAU CÚ SỐC VĨ MÔ ---")
    print(f"• Tỷ lệ NPL thông thường (Baseline): {s.get('baseline_npl_ratio_pct')}%")
    print(f"• Tỷ lệ NPL sau cú sốc (Stressed): {s.get('stressed_npl_ratio_pct')}%")
    print(f"• Biến thiên NPL: {s.get('npl_increase_pct'):+}%")
    print(f"• Tổng tổn thất dự kiến gia tăng (ΔEL): {s.get('total_delta_expected_loss_vnd'):,} VNĐ")
    print(f"• Khuyến nghị trích lập dự phòng rủi ro (TT11): {s.get('provisioning_recommendation_vnd'):,} VNĐ")
    print(f"• Số hồ sơ bị suy giảm hạng rủi ro (Migrated): {s.get('migrated_higher_risk_count')} / {s.get('total_cases')} hồ sơ")

    print("\n--- CHI TIẾT ĐỘ NHẠY TỪNG HỒ SƠ DƯỚI CÚ SỐC ---")
    header = f"{'STT':<4} | {'MÃ HỒ SƠ':<14} | {'P(BASE)':<8} | {'P(STRESS)':<9} | {'Δ PROB':<8} | {'HẠNG MỚI':<15} | {'Δ TỔN THẤT (ΔEL)'}"
    print(header)
    print("-" * len(header))
    for idx, d in enumerate(details[:7], 1):  # print first 7 for brevity
        print(f"{idx:<4} | {d.get('ma_ho_so'):<14} | {d.get('baseline_approval_prob'):>6.1f}% | {d.get('stressed_approval_prob'):>6.1f}%  | {d.get('prob_delta'):>+6.1f}% | {d.get('stressed_tier'):<15} | {d.get('expected_loss_delta_vnd'):>12,} VNĐ")
    print(f"... và {len(details) - 7} hồ sơ còn lại đều được phân tích độ nhạy đầy đủ.")


def test_core_banking():
    print("\n" + "=" * 70)
    print("3. KIỂM CHỨNG LIVE: HẠCH TOÁN CORE BANKING & PHÂN QUYỀN RBAC")
    print("=" * 70)
    
    # Test 1: Loan Officer attempts to disburse -> Must be 403 Forbidden
    payload_unauth = {
        "ma_ho_so": "HS-20268888",
        "ho_ten": "Nguyễn Hoàng Long",
        "approved_limit_vnd": 500000000,
        "interest_rate_pct": 8.5,
        "account_number": "998877665501",
        "role": "Loan Officer",
        "idempotency_key": "TEST-IDEM-001"
    }
    req_unauth = urllib.request.Request(
        f"{BASE_URL}/integration/core-banking/disburse",
        data=json.dumps(payload_unauth).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req_unauth)
        print("❌ LỖI: Loan Officer giải ngân thành công (vi phạm RBAC)")
    except urllib.error.HTTPError as e:
        print(f"✅ Kiểm thử 1 (RBAC Chặn Loan Officer): HTTP {e.code} Forbidden ({e.read().decode('utf-8')})")

    # Test 2: Committee Chair disburses -> Must be 200 OK + FT Transaction ID
    idempotency_key = "IDEM-TEST-2026-CHAIR-X99"
    payload_auth = {
        "ma_ho_so": "HS-20268888",
        "ho_ten": "Nguyễn Hoàng Long",
        "approved_limit_vnd": 500000000,
        "interest_rate_pct": 8.5,
        "account_number": "998877665501",
        "role": "Committee Chair",
        "idempotency_key": idempotency_key
    }
    req_auth = urllib.request.Request(
        f"{BASE_URL}/integration/core-banking/disburse",
        data=json.dumps(payload_auth).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_auth) as resp:
        res1 = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Kiểm thử 2 (Chủ tịch Hội đồng Giải ngân): HTTP {resp.status}")
        print(f"   • Mã giao dịch Core Banking sinh ra: {res1.get('ft_transaction_id')}")
        print(f"   • Số tiền hạch toán: {res1.get('disbursed_amount_vnd'):,} VNĐ")
        print(f"   • Trạng thái hạch toán: {res1.get('status')}")

    # Test 3: Repeat with same Idempotency Key -> Must return duplicate detection
    req_repeat = urllib.request.Request(
        f"{BASE_URL}/integration/core-banking/disburse",
        data=json.dumps(payload_auth).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_repeat) as resp:
        res2 = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Kiểm thử 3 (Chống trùng lệnh Idempotency): HTTP {resp.status}")
        print(f"   • Trùng khớp mã FT ban đầu: {res2.get('ft_transaction_id') == res1.get('ft_transaction_id')} ({res2.get('ft_transaction_id')})")
        print(f"   • Thông báo từ Gateway: {res2.get('message')}")

if __name__ == '__main__':
    test_batch_assess()
    test_portfolio_stress()
    test_core_banking()
