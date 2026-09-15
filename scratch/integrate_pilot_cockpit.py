import sys
import shutil
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("Original length:", len(html))

# 1. Add Toast Container after <body>
if 'id="validationToastContainer"' not in html:
    toast_container = """<body class="bg-surface text-on-surface antialiased">
  <!-- Top Dismissible Toast Container for Validation & Alerts -->
  <div id="validationToastContainer" class="fixed top-5 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 max-w-lg w-full px-4 pointer-events-none"></div>"""
    html = html.replace('<body class="bg-surface text-on-surface antialiased">', toast_container)
    print("1. Added validationToastContainer")

# 2. Add Role Switcher to Top Header
old_header_user = """          <div class="flex items-center gap-2 sm:gap-3">
            <div class="text-right hidden sm:block">
              <div class="text-[14px] text-primary font-bold leading-tight">Nguyễn Văn Minh</div>
              <div class="text-[11px] text-on-surface-variant">Trưởng nhóm Thẩm định Rủi ro</div>
            </div>
            <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-primary flex items-center justify-center text-white shadow-sm shrink-0" title="Nguyễn Văn Minh - Trưởng nhóm Thẩm định">
              <span class="material-symbols-outlined text-[18px] sm:text-[20px]">person</span>
            </div>
          </div>"""

new_header_user = """          <!-- Interactive Role Switcher Dropdown (Pilot RBAC) -->
          <div class="flex items-center gap-2 bg-surface-container-low hover:bg-surface-container p-1.5 sm:px-3 sm:py-1.5 rounded-xl border border-surface-container transition-all">
            <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white shadow-sm shrink-0" id="roleAvatar">
              <span class="material-symbols-outlined text-[18px]" id="roleIcon">badge</span>
            </div>
            <div class="flex flex-col text-left min-w-0">
              <div class="flex items-center gap-1">
                <span class="text-[10px] sm:text-[11px] text-secondary font-bold uppercase tracking-wider" id="roleBadge">Loan Officer</span>
                <span class="material-symbols-outlined text-[14px] text-on-surface-variant">expand_more</span>
              </div>
              <select id="userRoleSelect" onchange="changeAppRole(this.value)" class="bg-transparent text-[12px] sm:text-[13px] font-bold text-primary focus:outline-none cursor-pointer pr-1">
                <option value="Loan Officer">Nguyễn Văn Minh (Thẩm định viên)</option>
                <option value="Risk Manager">Trần Thị Lan (Quản trị Rủi ro)</option>
                <option value="Committee Chair">TS. Lê Hoàng Nam (Chủ tịch Hội đồng)</option>
              </select>
            </div>
          </div>"""

if old_header_user in html:
    html = html.replace(old_header_user, new_header_user)
    print("2. Added RBAC Role Switcher to Header")
else:
    print("old_header_user not matched")

# 3. Add Core Banking action button in Committee View
old_comm_btn = """              <button class="px-6 py-2.5 rounded-lg bg-primary text-white font-bold text-[13px] shadow hover:bg-primary/90 flex items-center justify-center gap-2 transition-all self-end" onclick="submitCommitteeDecision()" type="button">
                <span class="material-symbols-outlined text-[18px]">verified</span>
                KÝ SỐ VÀ BAN HÀNH QUYẾT ĐỊNH CHÍNH THỨC
              </button>"""

new_comm_btn = """              <div class="flex flex-wrap items-center justify-end gap-3 self-end">
                <button id="btnCommitteeSign" class="px-6 py-2.5 rounded-lg bg-primary text-white font-bold text-[13px] shadow hover:bg-primary/90 flex items-center justify-center gap-2 transition-all" onclick="submitCommitteeDecision()" type="button">
                  <span class="material-symbols-outlined text-[18px]">verified</span>
                  KÝ SỐ VÀ BAN HÀNH PHÁN QUYẾT
                </button>
                <button id="btnCoreDisburse" class="px-6 py-2.5 rounded-lg bg-emerald-700 text-white font-bold text-[13px] shadow hover:bg-emerald-800 flex items-center justify-center gap-2 transition-all" onclick="disburseToCoreBanking()" type="button" title="Chỉ Chủ tịch Hội đồng mới có quyền giải ngân Core">
                  <span class="material-symbols-outlined text-[18px]">account_balance</span>
                  HẠCH TOÁN CORE BANKING (T24)
                </button>
              </div>"""

if old_comm_btn in html:
    html = html.replace(old_comm_btn, new_comm_btn)
    print("3. Added Core Banking Action Button in Committee View")
else:
    print("old_comm_btn not matched")

# 4. Update viewStress to have Tabs: Single Case vs Portfolio
old_stress_header = """          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-secondary text-[24px]">crisis_alert</span>
            <h2 class="text-[20px] text-primary font-bold">MÔ PHỎNG KIỂM TRA SỨC CHỊU TẢI RỦI RO (STRESS-TESTING SIMULATOR)</h2>
          </div>
          <p class="text-[12px] text-on-surface-variant mb-6">
            Mô phỏng tác động của các cú sốc vĩ mô (thu nhập giảm, lãi suất tăng, tài sản đảm bảo sụt giá) lên hồ sơ khách hàng đang thẩm định.
          </p>"""

new_stress_header = """          <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="material-symbols-outlined text-secondary text-[24px]">crisis_alert</span>
                <h2 class="text-[20px] text-primary font-bold">MÔ PHỎNG KIỂM TRA SỨC CHỊU TẢI RỦI RO (STRESS-TESTING SIMULATOR)</h2>
              </div>
              <p class="text-[12px] text-on-surface-variant">
                Mô phỏng tác động của 4 cú sốc vĩ mô (thu nhập -15%, lãi suất +2%, TSĐB -20%, CIC -30 điểm) lên hồ sơ đơn lẻ hoặc toàn bộ danh mục hàng đợi.
              </p>
            </div>
            <!-- Sub Tabs: Single Case vs Portfolio -->
            <div class="flex items-center bg-surface-container rounded-xl p-1 border border-surface-container font-semibold text-[13px]">
              <button id="tabStressSingle" onclick="switchStressTab('single')" class="px-4 py-1.5 rounded-lg bg-white text-primary shadow-sm transition-all">
                Hồ Sơ Đơn Lẻ
              </button>
              <button id="tabStressPortfolio" onclick="switchStressTab('portfolio')" class="px-4 py-1.5 rounded-lg text-on-surface-variant hover:text-primary transition-all">
                Danh Mục Hàng Đợi (14 Hồ Sơ)
              </button>
            </div>
          </div>"""

if old_stress_header in html:
    html = html.replace(old_stress_header, new_stress_header)
    print("4. Added Stress Tab Switcher")
else:
    print("old_stress_header not matched")

# Also insert Portfolio Stress Container right before ending viewStress </div>
old_stress_end = """              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================================================================== -->
      <!-- VIEW 5: HỘI ĐỒNG TÍN DỤNG -->"""

portfolio_stress_html = """              </div>
            </div>
          </div>

          <!-- PORTFOLIO LEVEL STRESS TESTING VIEW (P1) -->
          <div id="portfolioStressSection" class="hidden flex flex-col gap-6 mt-4">
            <!-- 4 Portfolio KPI Summary Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div class="p-4 rounded-xl bg-surface-container-low border border-surface-container">
                <div class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Tỷ Lệ Nợ Xấu Dự Kiến (NPL)</div>
                <div class="flex items-baseline gap-2 mt-1">
                  <span class="text-[24px] font-extrabold text-error font-mono" id="portStressedNpl">28.57%</span>
                  <span class="text-[12px] text-on-surface-variant font-mono">(Gốc: <span id="portBaseNpl">14.29%</span>)</span>
                </div>
                <div class="text-[11px] text-error font-semibold mt-1">Tăng +<span id="portNplDelta">14.28</span>% sau cú sốc</div>
              </div>

              <div class="p-4 rounded-xl bg-surface-container-low border border-surface-container">
                <div class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Tổn Thất Dự Tính Gia Tăng (ΔEL)</div>
                <div class="text-[22px] font-extrabold text-primary font-mono mt-1" id="portDeltaEl">1,245,000,000 VNĐ</div>
                <div class="text-[11px] text-on-surface-variant mt-1">ΔEL = Σ(ΔPD × LGD 45% × EAD)</div>
              </div>

              <div class="p-4 rounded-xl bg-surface-container-low border border-surface-container">
                <div class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Hồ Sơ Bị Trượt Nhóm Rủi Ro</div>
                <div class="flex items-baseline gap-2 mt-1">
                  <span class="text-[24px] font-extrabold text-secondary font-mono" id="portMigratedCount">5 / 14</span>
                  <span class="text-[11px] text-on-surface-variant">hồ sơ trượt hạng</span>
                </div>
                <div class="text-[11px] text-secondary font-semibold mt-1">Chuyển sang phân tầng Subprime</div>
              </div>

              <div class="p-4 rounded-xl bg-surface-container-low border border-surface-container">
                <div class="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">Khuyến Nghị Trích Lập (TT11)</div>
                <div class="text-[20px] font-extrabold text-on-tertiary-container font-mono mt-1" id="portProvisionRec">1,820,000,000 VNĐ</div>
                <div class="text-[11px] text-on-surface-variant mt-1">Dự phòng chung 0.75% + ΔEL cụ thể</div>
              </div>
            </div>

            <!-- Portfolio Table Breakdown -->
            <div class="bg-white rounded-xl p-5 border border-surface-container shadow-sm">
              <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div>
                  <h3 class="text-[15px] text-primary font-bold">Chi Tiết Sức Chịu Tải 14 Hồ Sơ Trong Hàng Đợi</h3>
                  <p class="text-[11px] text-on-surface-variant">Phân tích chênh lệch xác suất duyệt và tổn thất dự tính khi nền kinh tế chịu sốc.</p>
                </div>
                <button onclick="loadPortfolioStress()" class="px-4 py-2 rounded-lg bg-secondary text-white text-[12px] font-bold hover:bg-secondary/90 shadow-sm flex items-center gap-1.5 transition-all">
                  <span class="material-symbols-outlined text-[16px]">refresh</span>
                  Chạy Lại Sốc Danh Mục
                </button>
              </div>

              <div class="overflow-x-auto rounded-lg border border-surface-container">
                <table class="w-full text-left text-[12px]">
                  <thead class="bg-surface-container text-on-surface-variant uppercase font-semibold font-mono text-[11px]">
                    <tr>
                      <th class="px-3 py-2.5">Mã Hồ Sơ</th>
                      <th class="px-3 py-2.5">Khách Hàng</th>
                      <th class="px-3 py-2.5">Số Tiền Vay</th>
                      <th class="px-3 py-2.5 text-center">Xác Suất Gốc</th>
                      <th class="px-3 py-2.5 text-center">Sau Cú Sốc</th>
                      <th class="px-3 py-2.5 text-center">Biến Thiên (Δ)</th>
                      <th class="px-3 py-2.5 text-center">Phân Tầng</th>
                      <th class="px-3 py-2.5 text-right">Tổn Thất Dự Tính (ΔEL)</th>
                    </tr>
                  </thead>
                  <tbody id="portfolioStressTableBody" class="divide-y divide-surface-container font-mono text-[11px]">
                    <!-- Rendered dynamically -->
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================================================================== -->
      <!-- VIEW 5: HỘI ĐỒNG TÍN DỤNG -->"""

if old_stress_end in html:
    html = html.replace(old_stress_end, portfolio_stress_html)
    print("5. Added Portfolio Stress UI Section")
else:
    print("old_stress_end not matched")

# 5. Add Native Excel Export button action
html = html.replace(
    'onclick="exportQueueExcel()"',
    'onclick="exportNativeQueueExcel()"'
)

# 6. Add Pilot JS Controllers before </script>
pilot_js = """
    // ====================================================================
    // PILOT P0 + P1: VALIDATION SHIELD, RBAC 3-ROLE & PORTFOLIO STRESS
    // ====================================================================
    let currentAppRole = 'Loan Officer';

    // 1. Toast Notification Helper (Dismissible with specific field highlighting)
    function showValidationToast(title, message, fieldId) {
      const container = document.getElementById('validationToastContainer');
      if (!container) return;
      
      if (fieldId) {
        const el = document.getElementById(fieldId);
        if (el) {
          el.classList.add('border-error', 'ring-2', 'ring-error');
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          el.focus();
          setTimeout(() => {
            el.classList.remove('border-error', 'ring-2', 'ring-error');
          }, 5000);
        }
      }

      const toast = document.createElement('div');
      toast.className = "pointer-events-auto flex items-start gap-3 p-4 rounded-xl bg-error text-white shadow-2xl transition-all duration-300 transform translate-y-0 opacity-100 border border-white/20";
      toast.innerHTML = `
        <span class="material-symbols-outlined text-[24px] text-white shrink-0 mt-0.5">error</span>
        <div class="flex-1 text-left min-w-0">
          <div class="font-bold text-[14px] leading-tight">${title}</div>
          <div class="text-[12px] text-white/90 mt-1 leading-snug break-words">${message}</div>
        </div>
        <button type="button" class="text-white/80 hover:text-white p-1 shrink-0" onclick="this.parentElement.remove()">
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      `;
      container.appendChild(toast);

      setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-[-10px]');
        setTimeout(() => toast.remove(), 300);
      }, 6000);
    }

    function showSuccessToast(title, message) {
      const container = document.getElementById('validationToastContainer');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = "pointer-events-auto flex items-start gap-3 p-4 rounded-xl bg-emerald-700 text-white shadow-2xl transition-all duration-300 transform translate-y-0 opacity-100 border border-white/20";
      toast.innerHTML = `
        <span class="material-symbols-outlined text-[24px] text-white shrink-0 mt-0.5">check_circle</span>
        <div class="flex-1 text-left min-w-0">
          <div class="font-bold text-[14px] leading-tight">${title}</div>
          <div class="text-[12px] text-white/90 mt-1 leading-snug break-words">${message}</div>
        </div>
        <button type="button" class="text-white/80 hover:text-white p-1 shrink-0" onclick="this.parentElement.remove()">
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      `;
      container.appendChild(toast);

      setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-[-10px]');
        setTimeout(() => toast.remove(), 300);
      }, 6000);
    }

    // 2. Client-side Application Data Validator (Shield before fetch)
    function validateClientApplicationData(p) {
      // Họ và tên
      if (!p.ho_ten || !p.ho_ten.trim()) {
        showValidationToast("Lỗi nhập liệu: Họ tên", "Vui lòng nhập Họ & tên khách hàng trước khi thẩm định.", "custName");
        return false;
      }
      // Tuổi: 18 <= age <= 70
      if (isNaN(p.tuoi) || p.tuoi < 18 || p.tuoi > 70) {
        showValidationToast("Lỗi nghiệp vụ: Độ tuổi", `Độ tuổi khách hàng phải từ 18 đến 70 tuổi theo chuẩn thẩm định bán lẻ ngân hàng (bạn nhập: ${p.tuoi}).`, "custAge");
        return false;
      }
      // Thu nhập chính: >= 1.000.000 VNĐ
      if (isNaN(p.thu_nhap_thang_vnd) || p.thu_nhap_thang_vnd < 1000000) {
        showValidationToast("Lỗi tài chính: Thu nhập chính", "Thu nhập người vay chính phải từ 1.000.000 VNĐ trở lên (không chấp nhận số âm hoặc bằng 0).", "inputIncome");
        return false;
      }
      // Thu nhập đồng vay: >= 0
      if (isNaN(p.thu_nhap_nguoi_dong_vay_vnd) || p.thu_nhap_nguoi_dong_vay_vnd < 0) {
        showValidationToast("Lỗi tài chính: Thu nhập đồng vay", "Thu nhập người đồng vay không được là số âm.", "inputCoIncome");
        return false;
      }
      // TSĐB: >= 0
      if (isNaN(p.gia_tri_tai_san_dam_bao_vnd) || p.gia_tri_tai_san_dam_bao_vnd < 0) {
        showValidationToast("Lỗi tài sản: TSĐB", "Giá trị tài sản đảm bảo thẩm định không được là số âm.", "inputCollateral");
        return false;
      }
      // Số tiền vay: >= 10.000.000 VNĐ
      if (isNaN(p.so_tien_vay_vnd) || p.so_tien_vay_vnd < 10000000) {
        showValidationToast("Lỗi khoản vay: Số tiền vay", `Số tiền đề nghị vay tối thiểu từ 10.000.000 VNĐ trở lên (bạn nhập: ${(p.so_tien_vay_vnd || 0).toLocaleString()} VNĐ).`, "inputLoanAmt");
        return false;
      }
      // Điểm tín dụng CIC: 400 - 850
      if (isNaN(p.diem_tin_dung_cic) || p.diem_tin_dung_cic < 400 || p.diem_tin_dung_cic > 850) {
        showValidationToast("Lỗi dữ liệu: Điểm tín dụng CIC", `Điểm tín dụng CIC phải nằm trong thang điểm chuẩn 400 - 850 (bạn nhập: ${p.diem_tin_dung_cic}).`, "inputCicScore");
        return false;
      }
      // DTI: 0% - 100%
      if (isNaN(p.ty_le_dti) || p.ty_le_dti < 0 || p.ty_le_dti > 100) {
        showValidationToast("Lỗi tính toán: Tỷ lệ DTI", "Tỷ lệ DTI tính toán không hợp lệ (phải nằm trong khoảng 0% đến 100%).", "inputDti");
        return false;
      }
      if (p.ty_le_dti > 85.0) {
        showValidationToast("Cảnh báo rủi ro: DTI Vượt Ngưỡng", `Tỷ lệ DTI ${p.ty_le_dti}% vượt ngưỡng khuyến nghị an toàn 85%. Hồ sơ sẽ chịu rủi ro bị từ chối hoặc cần bổ sung người đồng vay.`, "inputDti");
      }
      return true;
    }

    // 3. RBAC 3-Role State Switcher (Instant Re-render)
    function changeAppRole(role) {
      currentAppRole = role;
      const roleBadge = document.getElementById('roleBadge');
      const roleIcon = document.getElementById('roleIcon');
      const radioOptimal = document.getElementById('radioThreshOptimal');
      const radioDefault = document.getElementById('radioThreshDefault');
      const btnSign = document.getElementById('btnCommitteeSign');
      const btnDisburse = document.getElementById('btnCoreDisburse');

      if (role === 'Loan Officer') {
        if (roleBadge) roleBadge.textContent = "Loan Officer";
        if (roleIcon) roleIcon.textContent = "badge";
        // Threshold: Fixed 0.73, disabled 0.50
        if (radioOptimal) { radioOptimal.checked = true; radioOptimal.disabled = true; }
        if (radioDefault) { radioDefault.disabled = true; }
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
        showSuccessToast("Chuyển Vai Trò: Quản Trị Rủi Ro", "Quyền hạn: Được đổi threshold (0.73 ↔ 0.50), chạy Stress-test danh mục, kiểm toán tính công bằng và audit log.");
      } else if (role === 'Committee Chair') {
        if (roleBadge) roleBadge.textContent = "Committee Chair";
        if (roleIcon) roleIcon.textContent = "gavel";
        // Threshold: Fixed 0.73 (cannot tamper threshold)
        if (radioOptimal) { radioOptimal.checked = true; radioOptimal.disabled = true; }
        if (radioDefault) { radioDefault.disabled = true; }
        // Committee signing enabled
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
        showSuccessToast("Chuyển Vai Trò: Chủ Tịch Hội Đồng", "Quyền hạn: Xem xét hồ sơ, biểu quyết, ký số phán quyết chính thức và hạch toán giải ngân Core Banking.");
      }
    }

    // 4. Portfolio Stress Sub-Tab Switcher
    function switchStressTab(tab) {
      const tabSingle = document.getElementById('tabStressSingle');
      const tabPort = document.getElementById('tabStressPortfolio');
      const secSingle = document.querySelector('#viewStress .grid');
      const secPort = document.getElementById('portfolioStressSection');

      if (tab === 'single') {
        tabSingle.className = "px-4 py-1.5 rounded-lg bg-white text-primary shadow-sm transition-all";
        tabPort.className = "px-4 py-1.5 rounded-lg text-on-surface-variant hover:text-primary transition-all";
        if (secSingle) secSingle.classList.remove('hidden');
        if (secPort) secPort.classList.add('hidden');
      } else {
        tabPort.className = "px-4 py-1.5 rounded-lg bg-white text-primary shadow-sm transition-all";
        tabSingle.className = "px-4 py-1.5 rounded-lg text-on-surface-variant hover:text-primary transition-all";
        if (secSingle) secSingle.classList.add('hidden');
        if (secPort) secPort.classList.remove('hidden');
        loadPortfolioStress();
      }
    }

    // 5. Load Portfolio Stress Engine Data
    async function loadPortfolioStress() {
      try {
        const res = await fetch(`${API_BASE}/simulate-stress/portfolio`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ case_ids: ['all_queue'] })
        });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        
        // Render Summary
        document.getElementById('portStressedNpl').textContent = data.summary.stressed_npl_ratio_pct + "%";
        document.getElementById('portBaseNpl').textContent = data.summary.baseline_npl_ratio_pct + "%";
        document.getElementById('portNplDelta').textContent = data.summary.npl_increase_pct;
        document.getElementById('portDeltaEl').textContent = data.summary.total_delta_expected_loss_vnd.toLocaleString() + " VNĐ";
        document.getElementById('portMigratedCount').textContent = `${data.summary.migrated_higher_risk_count} / ${data.summary.total_cases}`;
        document.getElementById('portProvisionRec').textContent = data.summary.provisioning_recommendation_vnd.toLocaleString() + " VNĐ";

        // Render Table
        const tbody = document.getElementById('portfolioStressTableBody');
        if (tbody) {
          tbody.innerHTML = data.details.map(item => {
            const deltaColor = item.prob_delta < 0 ? "text-error font-bold" : "text-on-tertiary-container";
            const deltaSign = item.prob_delta > 0 ? "+" : "";
            const isKnockoutBadge = item.is_hard_rule_knockout ?
              '<span class="px-2 py-0.5 rounded bg-error/10 text-error font-bold text-[10px]">KNOCKOUT CỨNG</span>' :
              `<span class="px-2 py-0.5 rounded ${item.tier_migrated ? 'bg-error/10 text-error font-bold' : 'bg-surface-container text-on-surface'} text-[10px]">${item.stressed_tier}</span>`;
            
            return `
              <tr class="hover:bg-surface-container-low transition-colors">
                <td class="px-3 py-2.5 font-bold text-primary">${item.ma_ho_so}</td>
                <td class="px-3 py-2.5 font-sans">${item.ho_ten}</td>
                <td class="px-3 py-2.5 text-right font-bold text-primary">${item.so_tien_vay_vnd.toLocaleString()} VNĐ</td>
                <td class="px-3 py-2.5 text-center font-bold">${item.baseline_approval_prob}%</td>
                <td class="px-3 py-2.5 text-center font-bold text-primary">${item.stressed_approval_prob}%</td>
                <td class="px-3 py-2.5 text-center ${deltaColor}">${deltaSign}${item.prob_delta}%</td>
                <td class="px-3 py-2.5 text-center">${isKnockoutBadge}</td>
                <td class="px-3 py-2.5 text-right font-bold text-primary">${item.expected_loss_delta_vnd.toLocaleString()} VNĐ</td>
              </tr>
            `;
          }).join('');
        }
      } catch (err) {
        console.error("Lỗi nạp mô phỏng danh mục:", err);
        showValidationToast("Lỗi máy chủ", "Không thể nạp dữ liệu mô phỏng danh mục từ backend FastAPI.");
      }
    }

    // 6. Core Banking Mock Gateway Action
    async function disburseToCoreBanking() {
      if (currentAppRole !== 'Committee Chair') {
        showValidationToast("Truy cập bị từ chối (RBAC 403)", "Chỉ Chủ tịch Hội đồng Tín dụng (Committee Chair) mới có quyền phê duyệt hạch toán giải ngân Core Banking.");
        return;
      }

      const maHoSo = document.getElementById('commCustCode')?.textContent || "HS-20268888";
      const hoTen = document.getElementById('commCustName')?.textContent || "Khách hàng";
      const limit = parseFloat(document.getElementById('commApprovedLimit')?.value || "500000000");
      const rate = parseFloat(document.getElementById('commInterestRate')?.value || "8.5");
      const idempotencyKey = "IDEM-" + Date.now() + "-" + Math.random().toString(36).substring(2, 8);

      try {
        const res = await fetch(`${API_BASE}/integration/core-banking/disburse`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ma_ho_so: maHoSo,
            ho_ten: hoTen,
            approved_limit_vnd: limit,
            interest_rate_pct: rate,
            account_number: "998877665501",
            role: currentAppRole,
            officer_id: "HDTD-CHAIR-01",
            idempotency_key: idempotencyKey
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Lỗi Core Banking");
        }

        const data = await res.json();
        showSuccessToast("Hạch Toán Core Banking Thành Công!", `Mã giao dịch: ${data.ft_transaction_id} | Đã giải ngân: ${limit.toLocaleString()} VNĐ vào TK ${data.account_number}`);
      } catch (err) {
        showValidationToast("Lỗi Hạch Toán Core Banking", err.message);
      }
    }

    // 7. Native Server-Side Excel Export
    function exportNativeQueueExcel() {
      window.location.href = `${API_BASE}/export/excel/queue`;
      showSuccessToast("Đang tải file Excel...", "File .xlsx chuẩn OpenXML đã được sinh từ server kèm định dạng tiền tệ.");
    }
"""

# Inject validation check into runPrediction()
old_run_pred_start = """    async function runPrediction() {
      const selectedThresh = document.querySelector('input[name="thresholdPolicy"]:checked')?.value || "0.73";
      const threshNum = parseFloat(selectedThresh);

      const payload = {
        ma_ho_so: document.getElementById('custCode').value,
        ho_ten: document.getElementById('custName').value,
        tuoi: parseInt(document.getElementById('custAge').value),
        gioi_tinh: document.getElementById('custGender').value,
        tinh_trang_hon_nhan: document.getElementById('custMarital').value,
        so_nguoi_phu_thuoc: parseInt(document.getElementById('custDependents').value),
        trinh_do_hoc_van: document.getElementById('custEducation').value,
        loai_hinh_nghe_nghiep: document.getElementById('custJob').value,
        thu_nhap_thang_vnd: parseFloat(document.getElementById('inputIncome').value),
        thu_nhap_nguoi_dong_vay_vnd: parseFloat(document.getElementById('inputCoIncome').value),
        gia_tri_tai_san_dam_bao_vnd: parseFloat(document.getElementById('inputCollateral').value),
        muc_dich_vay: document.getElementById('inputLoanPurpose').value,
        so_tien_vay_vnd: parseFloat(document.getElementById('inputLoanAmt').value),
        thoi_han_vay_thang: parseInt(document.getElementById('inputLoanTenure').value),
        khu_vuc_sinh_song: document.getElementById('inputArea').value,
        diem_tin_dung_cic: parseInt(document.getElementById('inputCicScore').value),
        nhom_no_cic: document.getElementById('inputDebtGroup').value,
        so_lan_tre_han_2_nam: parseInt(document.getElementById('inputDelinquency').value),
        so_khoan_vay_hien_tai: parseInt(document.getElementById('inputOpenLoans').value),
        lich_su_no_xau: document.getElementById('inputPastDefault').value,
        ty_le_dti: parseFloat(document.getElementById('inputDti').value)
      };

      if (!payload.ho_ten || !payload.ho_ten.trim()) {
        alert("Vui lòng nhập Họ & tên ứng viên trước khi thẩm định!");
        document.getElementById('custName').focus();
        return;
      }"""

new_run_pred_start = """    async function runPrediction() {
      const selectedThresh = document.querySelector('input[name="thresholdPolicy"]:checked')?.value || "0.73";
      const threshNum = parseFloat(selectedThresh);

      const payload = {
        ma_ho_so: document.getElementById('custCode').value,
        ho_ten: document.getElementById('custName').value,
        tuoi: parseInt(document.getElementById('custAge').value),
        gioi_tinh: document.getElementById('custGender').value,
        tinh_trang_hon_nhan: document.getElementById('custMarital').value,
        so_nguoi_phu_thuoc: parseInt(document.getElementById('custDependents').value),
        trinh_do_hoc_van: document.getElementById('custEducation').value,
        loai_hinh_nghe_nghiep: document.getElementById('custJob').value,
        thu_nhap_thang_vnd: parseFloat(document.getElementById('inputIncome').value),
        thu_nhap_nguoi_dong_vay_vnd: parseFloat(document.getElementById('inputCoIncome').value || 0),
        gia_tri_tai_san_dam_bao_vnd: parseFloat(document.getElementById('inputCollateral').value || 0),
        muc_dich_vay: document.getElementById('inputLoanPurpose').value,
        so_tien_vay_vnd: parseFloat(document.getElementById('inputLoanAmt').value),
        thoi_han_vay_thang: parseInt(document.getElementById('inputLoanTenure').value),
        khu_vuc_sinh_song: document.getElementById('inputArea').value,
        diem_tin_dung_cic: parseInt(document.getElementById('inputCicScore').value),
        nhom_no_cic: document.getElementById('inputDebtGroup').value,
        so_lan_tre_han_2_nam: parseInt(document.getElementById('inputDelinquency').value),
        so_khoan_vay_hien_tai: parseInt(document.getElementById('inputOpenLoans').value),
        lich_su_no_xau: document.getElementById('inputPastDefault').value,
        ty_le_dti: parseFloat(document.getElementById('inputDti').value)
      };

      // Tường lửa kiểm tra Client Validation Shield
      if (!validateClientApplicationData(payload)) {
        return;
      }"""

if old_run_pred_start in html:
    html = html.replace(old_run_pred_start, new_run_pred_start)
    print("6. Integrated validateClientApplicationData into runPrediction()")
else:
    print("old_run_pred_start not matched")

# Also update error handling inside runPrediction to show Validation Toast if 422
old_fetch_err = """          const errData = await res.json().catch(() => ({}));
          let errMsg = `Lỗi hệ thống (${res.status}): `;
          if (errData.detail) {
            if (Array.isArray(errData.detail)) {
              errMsg += errData.detail.map(d => `${d.loc ? d.loc.join('.') : ''}: ${d.msg}`).join('\\n');
            } else {
              errMsg += errData.detail;
            }
          } else {
            errMsg += res.statusText;
          }
          alert(errMsg);
          return;"""

new_fetch_err = """          const errData = await res.json().catch(() => ({}));
          let errMsg = errData.message || (Array.isArray(errData.detail) ? errData.detail.map(d => d.msg).join(' | ') : "Lỗi dữ liệu gửi lên.");
          showValidationToast(`Lỗi máy chủ (${res.status})`, errMsg);
          return;"""

if old_fetch_err in html:
    html = html.replace(old_fetch_err, new_fetch_err)
    print("7. Replaced alert() with showValidationToast() for API errors")
else:
    print("old_fetch_err not matched")

# Inject pilot_js before </script>
idx_script_end = html.rfind('</script>')
if idx_script_end != -1:
    html = html[:idx_script_end] + "\n" + pilot_js + "\n" + html[idx_script_end:]
    print("8. Injected pilot JS helpers")

with open('app/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated app/cockpit.html successfully!")

# Synchronize to app/index.html
shutil.copyfile('app/cockpit.html', 'app/index.html')
print("Synchronized app/cockpit.html -> app/index.html successfully!")
