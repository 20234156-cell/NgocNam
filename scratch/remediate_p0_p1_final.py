# -*- coding: utf-8 -*-
"""
Script to apply final refinements to app/cockpit.html and app/index.html:
1. Thoroughly wipe all result widgets in clearAssessmentResult() so no old percentages (97.9%) remain.
2. Real-time input listeners to immediately clear results and highlight invalid inputs in red.
3. Keep userRoleSelect dropdown in sync with changeAppRole(role).
"""
import sys

new_clear_func = """    // Xóa trắng bảng kết quả thẩm định khi validation lỗi hoặc dữ liệu không hợp lệ
    function clearAssessmentResult() {
      currentAssessmentResult = null;
      const card = document.getElementById('decisionCard');
      const badge = document.getElementById('verdictBadge');
      const subtag = document.getElementById('verdictSubTag');
      const desc = document.getElementById('verdictDescription');
      const icon = document.getElementById('verdictIcon');
      const heroProb = document.getElementById('metricProbHero');
      const metricProb = document.getElementById('metricProb');
      const probBar = document.getElementById('probProgressBar');
      const metricDelta = document.getElementById('metricDelta');
      const metricDeltaLabel = document.getElementById('metricDeltaLabel');
      const deltaDot = document.getElementById('deltaDot');
      const deltaNote = document.getElementById('deltaNote');
      const metricRiskTier = document.getElementById('metricRiskTier');
      const metricRwa = document.getElementById('metricRwa');
      const metricPd = document.getElementById('metricPd');

      // 1. Reset metrics & probabilities
      if (heroProb) heroProb.textContent = "--%";
      if (metricProb) metricProb.textContent = "--%";
      if (probBar) {
        probBar.style.width = "0%";
        probBar.className = "h-full bg-surface-container-high rounded-full transition-all duration-700";
      }
      if (metricDelta) metricDelta.textContent = "--%";
      if (metricDeltaLabel) {
        metricDeltaLabel.textContent = "Chờ dữ liệu hợp lệ";
        metricDeltaLabel.className = "text-[11px] text-on-surface-variant font-semibold";
      }
      if (deltaDot) deltaDot.className = "w-2 h-2 rounded-full bg-outline shrink-0";
      if (deltaNote) deltaNote.textContent = "Hồ sơ chưa được đưa vào mô hình";

      // 2. Reset risk classification & capital ratios
      if (metricRiskTier) metricRiskTier.textContent = "Chưa xác định";
      if (metricRwa) metricRwa.textContent = "--";
      if (metricPd) metricPd.textContent = "--";

      // 3. Reset decision banner
      if (card) card.className = "relative overflow-hidden rounded-xl p-6 text-white shadow-xl transition-all duration-500 bg-gradient-to-r from-surface-container-high via-surface-container to-surface-variant border border-surface-container-highest";
      if (badge) badge.textContent = "CHỜ DỮ LIỆU THẨM ĐỊNH HỢP LỆ (BỊ CHẶN NHẬP LIỆU)";
      if (subtag) subtag.textContent = "VALIDATION REQUIRED";
      if (desc) desc.textContent = "Dữ liệu nhập vào chưa thỏa mãn chuẩn thẩm định bán lẻ ngân hàng (vi phạm điều kiện tuổi, thu nhập hoặc số tiền vay). Vui lòng kiểm tra lại các trường báo đỏ.";
      if (icon) icon.textContent = "block";

      // 4. Reset hard policy rule box
      const hrBox = document.getElementById('hardRuleBox');
      const hrTitle = document.getElementById('hardRuleTitle');
      const hrBadge = document.getElementById('hardRuleBadge');
      const hrDesc = document.getElementById('hardRuleDesc');
      const hrIcon = document.getElementById('hardRuleIcon');
      if (hrBox) hrBox.className = "p-4 rounded-xl bg-surface-container-low flex items-start gap-4 border border-surface-container";
      if (hrIcon) { hrIcon.textContent = "info"; hrIcon.className = "material-symbols-outlined text-[20px] text-on-surface-variant"; }
      if (hrTitle) hrTitle.textContent = "Tạm dừng kiểm tra Chính sách & Mô hình";
      if (hrBadge) { hrBadge.textContent = "WAITING"; hrBadge.className = "px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-mono text-[10px] font-bold"; }
      if (hrDesc) hrDesc.textContent = "Mô hình và bộ lọc chính sách tự động không chạy khi dữ liệu đầu vào chưa vượt qua lớp phòng thủ kiểm tra hợp lệ.";

      // 5. Reset business recommendation
      const recText = document.getElementById('actionRecommendationText');
      if (recText) recText.innerHTML = '<span class="text-error font-semibold">TẠM DỪNG THẨM ĐỊNH:</span> Dữ liệu đầu vào vi phạm tiêu chuẩn nhập liệu ngân hàng. Mô hình không thực thi tính toán xác suất nhằm tránh sai lệch rủi ro.';

      // 6. Reset audit trails
      const auditReq = document.getElementById('auditRequestId');
      const auditThresh = document.getElementById('auditThreshold');
      const auditTime = document.getElementById('auditTimestamp');
      if (auditReq) auditReq.textContent = "BLOCKED_BEFORE_EXEC";
      if (auditThresh) auditThresh.textContent = "--";
      if (auditTime) auditTime.textContent = new Date().toLocaleString('vi-VN');

      // 7. Reset committee view
      const commProb = document.getElementById('commAiProb');
      const commTier = document.getElementById('commRiskTier');
      if (commProb) commProb.textContent = "--%";
      if (commTier) commTier.textContent = "Chưa thẩm định";

      // 8. Reset SHAP Explainable AI Waterfall & Ranking Table
      const valFinalFx = document.getElementById('valFinalFx');
      const valFinalProb = document.getElementById('valFinalProb');
      if (valFinalFx) valFinalFx.textContent = "--";
      if (valFinalProb) valFinalProb.textContent = "--%";
      const container = document.getElementById('waterfallBarsContainer');
      if (container) container.innerHTML = '<div class="py-12 text-center text-on-surface-variant font-mono text-[12px]"><span class="material-symbols-outlined text-[32px] text-error mb-2 block">report_problem</span>Chờ dữ liệu thẩm định hợp lệ để trích xuất giá trị SHAP đóng góp rủi ro...</div>';
      const tbody = document.getElementById('rankingTableBody');
      if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-on-surface-variant font-mono text-[12px]">Không có dữ liệu SHAP khi hồ sơ vi phạm validation</td></tr>';
    }"""

new_role_sync = """    // 3. RBAC 3-Role State Switcher (Instant Re-render)
    function changeAppRole(role) {
      currentAppRole = role;
      const roleBadge = document.getElementById('roleBadge');
      const roleIcon = document.getElementById('roleIcon');
      const userRoleSelect = document.getElementById('userRoleSelect');
      const radioOptimal = document.getElementById('radioThreshOptimal');
      const radioDefault = document.getElementById('radioThreshDefault');
      const btnSign = document.getElementById('btnCommitteeSign');
      const btnDisburse = document.getElementById('btnCoreDisburse');

      if (userRoleSelect && userRoleSelect.value !== role) {
        userRoleSelect.value = role;
      }

      if (role === 'Loan Officer') {
        if (roleBadge) roleBadge.textContent = "Loan Officer";
        if (roleIcon) roleIcon.textContent = "badge";
        // Threshold: Fixed 0.73, disabled 0.50
        if (radioOptimal) { radioOptimal.checked = true; radioOptimal.disabled = true; }
        if (radioDefault) { radioDefault.disabled = true; }
        // Committee signing and core disburse disabled
        if (btnSign) {
          btnSign.classList.add('opacity-50', 'cursor-not-allowed');
          btnSign.disabled = true;
          btnSign.title = "Chỉ Chủ tịch Hội đồng mới có quyền ký số";
        }
        if (btnDisburse) {
          btnDisburse.classList.add('opacity-50', 'cursor-not-allowed');
          btnDisburse.disabled = true;
          btnDisburse.title = "Chỉ Chủ tịch Hội đồng mới có quyền giải ngân Core Banking";
        }
        showSuccessToast("Chuyển Vai Trò: Thẩm Định Viên", "Quyền hạn: Nhập liệu hồ sơ, chạy mô hình (ngưỡng 0.73 cố định), gửi tờ trình. Khóa quyền ký số và đổi threshold.");
      } else if (role === 'Risk Manager') {
        if (roleBadge) roleBadge.textContent = "Risk Manager";
        if (roleIcon) roleIcon.textContent = "shield";
        // Threshold: Full access to 0.73 and 0.50
        if (radioOptimal) { radioOptimal.disabled = false; }
        if (radioDefault) { radioDefault.disabled = false; }
        // Committee signing disabled
        if (btnSign) {
          btnSign.classList.add('opacity-50', 'cursor-not-allowed');
          btnSign.disabled = true;
          btnSign.title = "Chỉ Chủ tịch Hội đồng mới có quyền ký số";
        }
        if (btnDisburse) {
          btnDisburse.classList.add('opacity-50', 'cursor-not-allowed');
          btnDisburse.disabled = true;
          btnDisburse.title = "Chỉ Chủ tịch Hội đồng mới có quyền giải ngân Core Banking";
        }
        showSuccessToast("Chuyển Vai Trò: Quản Trị Rủi Ro", "Quyền hạn: Mở toàn quyền đổi threshold (0.73 ↔ 0.50), phân tích Stress-test danh mục và kiểm toán công bằng.");
      } else if (role === 'Committee Chair') {
        if (roleBadge) roleBadge.textContent = "Committee Chair";
        if (roleIcon) roleIcon.textContent = "gavel";
        // Threshold: Fixed 0.73 (cannot tamper threshold)
        if (radioOptimal) { radioOptimal.checked = true; radioOptimal.disabled = true; }
        if (radioDefault) { radioDefault.disabled = true; }
        // Committee signing and core disburse enabled
        if (btnSign) {
          btnSign.classList.remove('opacity-50', 'cursor-not-allowed');
          btnSign.disabled = false;
          btnSign.title = "Ký số và ban hành quyết định";
        }
        if (btnDisburse) {
          btnDisburse.classList.remove('opacity-50', 'cursor-not-allowed');
          btnDisburse.disabled = false;
          btnDisburse.title = "Hạch toán sang Core Banking";
        }
        showSuccessToast("Chuyển Vai Trò: Chủ Tịch Hội Đồng", "Quyền hạn: Xem xét hồ sơ, ký số phê duyệt chính thức và hạch toán giải ngân Core Banking.");
      }
    }"""

realtime_listeners = """
    // 7. Gắn lắng nghe sự kiện nhập liệu Real-time để xóa kết quả cũ ngay khi vi phạm
    function setupRealtimeValidationListeners() {
      const inputs = [
        { id: 'custAge', min: 18, max: 70 },
        { id: 'inputIncome', min: 1000000, max: Infinity },
        { id: 'inputLoanAmt', min: 10000000, max: Infinity },
        { id: 'inputCicScore', min: 400, max: 850 },
        { id: 'inputDti', min: 0, max: 100 }
      ];

      inputs.forEach(item => {
        const el = document.getElementById(item.id);
        if (!el) return;
        el.addEventListener('input', () => {
          const val = parseFloat(el.value);
          if (isNaN(val) || val < item.min || val > item.max) {
            el.classList.add('border-error', 'ring-2', 'ring-error');
            clearAssessmentResult();
          } else {
            el.classList.remove('border-error', 'ring-2', 'ring-error');
          }
        });
      });
    }
"""

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace clearAssessmentResult
    start_str = "    // Xóa trắng bảng kết quả thẩm định khi validation lỗi hoặc dữ liệu không hợp lệ\n    function clearAssessmentResult() {"
    end_str = "    function validateClientApplicationData(p) {"
    
    idx_start = content.find(start_str)
    idx_end = content.find(end_str)
    if idx_start != -1 and idx_end != -1:
        content = content[:idx_start] + new_clear_func + "\n\n" + content[idx_end:]
        print(f"Updated clearAssessmentResult in {filepath}")
    else:
        print(f"Could not find clearAssessmentResult boundaries in {filepath}: idx_start={idx_start}, idx_end={idx_end}")

    # 2. Replace changeAppRole
    role_start_str = "    // 3. RBAC 3-Role State Switcher (Instant Re-render)\n    function changeAppRole(role) {"
    role_end_str = "    // 4. Portfolio Stress Sub-Tab Switcher"
    
    r_idx_start = content.find(role_start_str)
    r_idx_end = content.find(role_end_str)
    if r_idx_start != -1 and r_idx_end != -1:
        content = content[:r_idx_start] + new_role_sync + "\n\n" + content[r_idx_end:]
        print(f"Updated changeAppRole in {filepath}")
    else:
        print(f"Could not find changeAppRole boundaries in {filepath}: r_idx_start={r_idx_start}, r_idx_end={r_idx_end}")

    # 3. Add realtime_listeners if not present
    if "setupRealtimeValidationListeners()" not in content:
        target_init = "changeAppRole('Loan Officer');"
        init_pos = content.find(target_init)
        if init_pos != -1:
            content = content[:init_pos] + "setupRealtimeValidationListeners();\n      " + content[init_pos:]
            # Append function before DOMContentLoaded listener
            marker = "document.addEventListener('DOMContentLoaded', () => {"
            m_pos = content.find(marker)
            if m_pos != -1:
                content = content[:m_pos] + realtime_listeners + "\n    " + content[m_pos:]
                print(f"Added setupRealtimeValidationListeners to {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved {filepath} successfully.")

if __name__ == '__main__':
    update_file('app/cockpit.html')
    update_file('app/index.html')
