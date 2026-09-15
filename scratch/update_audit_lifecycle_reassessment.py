# -*- coding: utf-8 -*-
"""
Script to apply P0, P1, P2 changes to app/cockpit.html and app/index.html:
1. P0: Remove auto-call runPrediction() on DOMContentLoaded.
2. P0: Disable button during in-flight fetch + show spinner + debounce.
3. P0: Client duplicate check if form data hasn't changed.
4. P1: Display Run #X and trigger source in Audit Table and Audit Detail Modal.
5. P2: Form dirty state: show 'Thẩm Định Lại (Run #X)' when form is modified.
"""
import sys

def update_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. P0: Remove auto-call on page load
    old_init = """    // Initialize on Startup
    window.addEventListener('DOMContentLoaded', () => {
      document.getElementById('dispTime').textContent = new Date().toLocaleTimeString('vi-VN');
      runPrediction();
    });"""

    new_init = """    // Initialize on Startup (Không tự động gọi model /predict để chống rác audit log)
    window.addEventListener('DOMContentLoaded', () => {
      document.getElementById('dispTime').textContent = new Date().toLocaleTimeString('vi-VN');
      // Chỉ nạp dữ liệu form sẵn sàng, chờ cán bộ tín dụng chủ động bấm Thẩm Định
      clearAssessmentResult();
      const desc = document.getElementById('verdictDescription');
      if (desc) desc.textContent = "Hồ sơ đã sẵn sàng. Vui lòng kiểm tra thông tin đầu vào và bấm nút 'Chạy Thẩm Định AI' để bắt đầu Run #1.";
      const badge = document.getElementById('verdictBadge');
      if (badge) badge.textContent = "HỒ SƠ SẴN SÀNG THẨM ĐỊNH (CHỜ KÍCH HOẠT RUN #1)";
      const subtag = document.getElementById('verdictSubTag');
      if (subtag) subtag.textContent = "READY FOR ASSESSMENT";
    });"""

    if old_init in c:
        c = c.replace(old_init, new_init)
        print(f"1. Removed auto-call on startup in {filepath}")
    else:
        print(f"Could not find old_init in {filepath}")

    # 2. P0 + P1 + P2: Enhanced runPrediction with button lock, debounce, run counter, dirty state
    old_run_func_marker = "    let currentAssessmentResult = null;\n\n    async function runPrediction() {"
    
    # We find runPrediction definition
    idx_run = c.find(old_run_func_marker)
    idx_simulate = c.find("    function simulateDecisionEngine(p, thresh) {")

    if idx_run != -1 and idx_simulate != -1:
        new_run_func = """    let currentAssessmentResult = null;
    let isPredictionRunning = false;
    let lastExecutedPayloadHash = null;
    let lastExecutedCaseId = null;
    let currentCaseRunNumber = 0;

    function getFormPayloadHash(p) {
      // Hash dữ liệu tài chính & CIC để nhận diện thay đổi
      return `${p.ma_ho_so}_${p.tuoi}_${p.thu_nhap_thang_vnd}_${p.thu_nhap_nguoi_dong_vay_vnd}_${p.gia_tri_tai_san_dam_bao_vnd}_${p.so_tien_vay_vnd}_${p.thoi_han_vay_thang}_${p.diem_tin_dung_cic}_${p.nhom_no_cic}_${p.ty_le_dti}_${p.so_lan_tre_han_2_nam}_${p.so_khoan_vay_hien_tai}_${p.lich_su_no_xau}`;
    }

    function checkFormDirtyState() {
      const btn = document.getElementById('btnRunPrediction');
      const dirtyBadge = document.getElementById('formDirtyBadge');
      if (!btn) return;

      if (!currentAssessmentResult || !lastExecutedPayloadHash) {
        btn.innerHTML = '<span class=\"material-symbols-outlined text-[18px]\">play_arrow</span> <span>Chạy Thẩm Định AI</span>';
        if (dirtyBadge) dirtyBadge.classList.add('hidden');
        return;
      }

      const p = getCurrentFormPayload();
      const curHash = getFormPayloadHash(p);
      const isDirty = (curHash !== lastExecutedPayloadHash);

      if (isDirty) {
        btn.innerHTML = `<span class=\"material-symbols-outlined text-[18px]\">cached</span> <span>Thẩm Định Lại (Run #${currentCaseRunNumber + 1})</span>`;
        if (dirtyBadge) {
          dirtyBadge.textContent = `Dữ liệu đã sửa so với Run #${currentCaseRunNumber}`;
          dirtyBadge.classList.remove('hidden');
        }
      } else {
        btn.innerHTML = `<span class=\"material-symbols-outlined text-[18px]\">check</span> <span>Đã Thẩm Định (Run #${currentCaseRunNumber})</span>`;
        if (dirtyBadge) dirtyBadge.classList.add('hidden');
      }
    }

    function getCurrentFormPayload() {
      return {
        ma_ho_so: (document.getElementById('custCode')?.value || 'HS-20268888').trim(),
        ho_ten: (document.getElementById('custName')?.value || '').trim(),
        tuoi: parseInt(document.getElementById('custAge')?.value || 30),
        gioi_tinh: document.getElementById('custGender')?.value || 'Nam',
        tinh_trang_hon_nhan: document.getElementById('custMarital')?.value || 'Đã kết hôn',
        so_nguoi_phu_thuoc: parseInt(document.getElementById('custDependents')?.value || 0),
        trinh_do_hoc_van: document.getElementById('custEducation')?.value || 'Cao đẳng / Đại học',
        loai_hinh_nghe_nghiep: document.getElementById('custJob')?.value || 'Nhân viên văn phòng',
        thu_nhap_thang_vnd: parseFloat(document.getElementById('inputIncome')?.value || 0),
        thu_nhap_nguoi_dong_vay_vnd: parseFloat(document.getElementById('inputCoIncome')?.value || 0),
        gia_tri_tai_san_dam_bao_vnd: parseFloat(document.getElementById('inputCollateral')?.value || 0),
        muc_dich_vay: document.getElementById('inputLoanPurpose')?.value || 'Vay tiêu dùng sinh hoạt',
        so_tien_vay_vnd: parseFloat(document.getElementById('inputLoanAmt')?.value || 0),
        thoi_han_vay_thang: parseInt(document.getElementById('inputLoanTenure')?.value || 36),
        khu_vuc_sinh_song: document.getElementById('inputArea')?.value || 'Nội thành / Đô thị',
        diem_tin_dung_cic: parseInt(document.getElementById('inputCicScore')?.value || 650),
        nhom_no_cic: document.getElementById('inputDebtGroup')?.value || 'Nhóm 1 (Đủ tiêu chuẩn)',
        so_lan_tre_han_2_nam: parseInt(document.getElementById('inputDelinquency')?.value || 0),
        so_khoan_vay_hien_tai: parseInt(document.getElementById('inputOpenLoans')?.value || 1),
        lich_su_no_xau: document.getElementById('inputPastDefault')?.value || 'Không',
        ty_le_dti: parseFloat(document.getElementById('inputDti')?.value || 30)
      };
    }

    async function runPrediction() {
      // 1. Chống bấm liên tiếp (Client in-flight lock)
      if (isPredictionRunning) {
        console.warn("Thao tác đang xử lý, chặn bấm liên tiếp");
        return;
      }

      const selectedThresh = document.querySelector('input[name=\"thresholdPolicy\"]:checked')?.value || "0.73";
      const threshNum = parseFloat(selectedThresh);
      const payload = getCurrentFormPayload();

      // 2. Chống gửi request trùng lặp nếu form chưa hề thay đổi gì so với run trước
      const currentHash = getFormPayloadHash(payload);
      if (lastExecutedCaseId === payload.ma_ho_so && lastExecutedPayloadHash === currentHash && currentAssessmentResult) {
        showSuccessToast("Hồ sơ chưa có thay đổi", `Hồ sơ ${payload.ma_ho_so} chưa thay đổi dữ liệu so với Run #${currentCaseRunNumber}. Đang giữ nguyên kết quả thẩm định để tránh trùng lặp audit.`);
        return;
      }

      // 3. Tường lửa kiểm tra Client Validation Shield
      if (!validateClientApplicationData(payload)) {
        clearAssessmentResult();
        return;
      }

      // Khóa nút thẩm định và hiện trạng thái đang chạy
      isPredictionRunning = true;
      const btn = document.getElementById('btnRunPrediction');
      if (btn) {
        btn.disabled = true;
        btn.classList.add('opacity-75', 'cursor-not-allowed');
        btn.innerHTML = '<span class=\"material-symbols-outlined text-[18px] animate-spin\">progress_activity</span> <span>Đang thẩm định...</span>';
      }

      try {
        const res = await fetch(`${API_BASE}/predict?use_optimal_threshold=${threshNum === 0.73}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          currentAssessmentResult = data;
          currentCaseRunNumber = data.run_number || (currentCaseRunNumber + 1);
          lastExecutedPayloadHash = currentHash;
          lastExecutedCaseId = payload.ma_ho_so;

          renderResult(data, payload, threshNum);
          document.getElementById('backendStatus').textContent = \"ONLINE (FastAPI)\";

          if (data.is_cached_run) {
            showSuccessToast(\"Kết Quả Cache 10s\", `Phát hiện bấm lặp cùng dữ liệu trong 10s. Hệ thống trả về kết quả Run #${currentCaseRunNumber} mà không tạo audit log trùng.`);
          }
          return;
        } else {
          const errData = await res.json().catch(() => ({}));
          let errMsg = errData.message || (Array.isArray(errData.detail) ? errData.detail.map(d => d.msg).join(' | ') : \"Lỗi dữ liệu gửi lên.\");
          clearAssessmentResult();
          showValidationToast(`Lỗi máy chủ (${res.status})`, errMsg);
          return;
        }
      } catch (err) {
        console.warn(\"FastAPI backend offline, running local high-fidelity Decision Engine simulation:\", err);
        document.getElementById('backendStatus').textContent = \"OFFLINE (Local Simulator)\";
        simulateDecisionEngine(payload, threshNum);
      } finally {
        // Debounce mở lại nút sau 800ms
        setTimeout(() => {
          isPredictionRunning = false;
          if (btn) {
            btn.disabled = false;
            btn.classList.remove('opacity-75', 'cursor-not-allowed');
            checkFormDirtyState();
          }
        }, 800);
      }
    }
"""
        c = c[:idx_run] + new_run_func + "\n" + c[idx_simulate:]
        print(f"2. Updated runPrediction with debounce and dirty state in {filepath}")
    else:
        print(f"Could not find runPrediction boundaries in {filepath}")

    # 3. Update Audit Table rendering to show Run #X and trigger source
    old_audit_row = """          <td class="px-4 py-2.5 font-bold text-primary font-mono">${log.ma_ho_so}</td>"""
    new_audit_row = """          <td class="px-4 py-2.5 font-mono">
            <div class="font-bold text-primary">${log.ma_ho_so}</div>
            <div class="flex items-center gap-1.5 mt-0.5">
              <span class="px-1.5 py-0.2 rounded bg-surface-container-high text-secondary font-bold text-[10px]">Run #${log.run_number || 1}</span>
              <span class="px-1.5 py-0.2 rounded bg-surface-container text-on-surface-variant text-[10px] uppercase">${log.triggered_by || 'click'}</span>
            </div>
          </td>"""
    if old_audit_row in c:
        c = c.replace(old_audit_row, new_audit_row)
        print(f"3. Updated Audit Table row with Run #X in {filepath}")

    # 4. Update Audit Detail Modal subtitle to show Run #X and trigger
    old_modal_sub = "document.getElementById('auditModalSubtitle').textContent = `Request ID: ${log.request_id} | Thời gian: ${new Date(log.timestamp).toLocaleString('vi-VN')}`;"
    new_modal_sub = "document.getElementById('auditModalSubtitle').textContent = `Request ID: ${log.request_id} | Lần chạy: Run #${log.run_number || 1} | Kích hoạt: ${log.triggered_by || 'user_click'} | Thời gian: ${new Date(log.timestamp).toLocaleString('vi-VN')}`;"
    if old_modal_sub in c:
        c = c.replace(old_modal_sub, new_modal_sub)
        print(f"4. Updated Audit Detail Modal subtitle in {filepath}")

    # 5. Add dirty listener in setupRealtimeValidationListeners
    old_listener_end = "      });\n    }"
    new_listener_end = """      });

      // Lắng nghe mọi thay đổi form để cập nhật trạng thái Thẩm Định Lại (Run #X)
      const form = document.getElementById('assessmentForm');
      if (form) {
        form.addEventListener('input', checkFormDirtyState);
        form.addEventListener('change', checkFormDirtyState);
      }
    }"""
    if "form.addEventListener('input', checkFormDirtyState);" not in c and old_listener_end in c:
        c = c.replace(old_listener_end, new_listener_end, 1)
        print(f"5. Added form dirty state listener in {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f"Saved {filepath} successfully.")

if __name__ == '__main__':
    update_html('app/cockpit.html')
    update_html('app/index.html')
