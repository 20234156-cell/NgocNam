import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import shutil

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add clearAssessmentResult function
clear_func = """
    // Xóa trắng bảng kết quả thẩm định khi validation lỗi hoặc dữ liệu không hợp lệ
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

      if (heroProb) heroProb.textContent = "--%";
      if (metricProb) metricProb.textContent = "--%";
      if (probBar) { probBar.style.width = "0%"; probBar.className = "h-full bg-surface-container-high rounded-full transition-all duration-700"; }
      if (metricDelta) metricDelta.textContent = "--%";

      if (card) card.className = "relative overflow-hidden rounded-xl p-6 text-white shadow-xl transition-all duration-500 bg-gradient-to-r from-surface-container-high via-surface-container to-surface-variant";
      if (badge) badge.textContent = "CHỜ DỮ LIỆU THẨM ĐỊNH HỢP LỆ";
      if (subtag) subtag.textContent = "VALIDATION REQUIRED";
      if (desc) desc.textContent = "Dữ liệu nhập vào chưa hợp lệ hoặc đã bị chặn bởi bộ quy chuẩn ngân hàng. Vui lòng kiểm tra lại các trường báo đỏ.";
      if (icon) icon.textContent = "block";

      const recText = document.getElementById('recText');
      if (recText) recText.textContent = "Hồ sơ chưa được đưa vào mô hình do vi phạm điều kiện tiên quyết nhập liệu.";
      
      const shapWaterfall = document.getElementById('shapWaterfallContainer');
      if (shapWaterfall) shapWaterfall.innerHTML = '<div class="h-64 flex items-center justify-center text-on-surface-variant font-mono text-[12px]">Chờ kết quả thẩm định hợp lệ để vẽ biểu đồ SHAP...</div>';
    }
"""

if "function clearAssessmentResult()" not in html:
    html = html.replace("function validateClientApplicationData(p) {", clear_func + "\n    function validateClientApplicationData(p) {")
    print("1. Added clearAssessmentResult() function")

# 2. Update runPrediction to call clearAssessmentResult() on validation failure or API error
old_run_pred_check = """      // Tường lửa kiểm tra Client Validation Shield
      if (!validateClientApplicationData(payload)) {
        return;
      }"""

new_run_pred_check = """      // Tường lửa kiểm tra Client Validation Shield
      if (!validateClientApplicationData(payload)) {
        clearAssessmentResult();
        return;
      }"""

if old_run_pred_check in html:
    html = html.replace(old_run_pred_check, new_run_pred_check)
    print("2. Integrated clearAssessmentResult into runPrediction validation check")

# Also on 422 error response
old_err_handling = """          const errData = await res.json().catch(() => ({}));
          let errMsg = errData.message || (Array.isArray(errData.detail) ? errData.detail.map(d => d.msg).join(' | ') : "Lỗi dữ liệu gửi lên.");
          showValidationToast(`Lỗi máy chủ (${res.status})`, errMsg);
          return;"""

new_err_handling = """          const errData = await res.json().catch(() => ({}));
          let errMsg = errData.message || (Array.isArray(errData.detail) ? errData.detail.map(d => d.msg).join(' | ') : "Lỗi dữ liệu gửi lên.");
          clearAssessmentResult();
          showValidationToast(`Lỗi máy chủ (${res.status})`, errMsg);
          return;"""

if old_err_handling in html:
    html = html.replace(old_err_handling, new_err_handling)
    print("3. Integrated clearAssessmentResult into API error branch")

# 3. Ensure changeAppRole initializes on page load
init_role_code = """
    // Khởi tạo vai trò mặc định (Loan Officer) ngay khi nạp trang
    document.addEventListener('DOMContentLoaded', () => {
      changeAppRole('Loan Officer');
    });
"""

if "changeAppRole('Loan Officer');" not in html:
    idx_script_end = html.rfind('</script>')
    if idx_script_end != -1:
        html = html[:idx_script_end] + "\n" + init_role_code + "\n" + html[idx_script_end:]
        print("4. Added DOMContentLoaded initialization for Loan Officer role")

with open('app/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(html)

shutil.copyfile('app/cockpit.html', 'app/index.html')
print("5. Synchronized cockpit.html -> index.html successfully!")
