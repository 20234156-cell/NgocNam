import sys
import shutil

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = """              <div class="p-3 rounded-lg bg-surface-container-high text-[11px] text-on-surface-variant mt-4" id="stressAdvice">
                💡 <strong>Khuyến nghị chịu tải:</strong> Với kịch bản sốc này, xác suất phê duyệt vẫn tiệm cận 71.5%. Đề xuất yêu cầu bổ sung điều khoản mua bảo hiểm tín dụng hoặc điều chỉnh trần giải ngân xuống 85% hạn mức.
              </div>
            </div>
          </div>
        </div>
      </div>"""

portfolio_section = """              <div class="p-3 rounded-lg bg-surface-container-high text-[11px] text-on-surface-variant mt-4" id="stressAdvice">
                💡 <strong>Khuyến nghị chịu tải:</strong> Với kịch bản sốc này, xác suất phê duyệt vẫn tiệm cận 71.5%. Đề xuất yêu cầu bổ sung điều khoản mua bảo hiểm tín dụng hoặc điều chỉnh trần giải ngân xuống 85% hạn mức.
              </div>
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
                <div class="text-[20px] font-extrabold text-primary font-mono mt-1" id="portDeltaEl">1,245,000,000 VNĐ</div>
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
                <div class="text-[18px] font-extrabold text-on-tertiary-container font-mono mt-1" id="portProvisionRec">1,820,000,000 VNĐ</div>
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
                      <th class="px-3 py-2.5 text-right">Số Tiền Vay</th>
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
      </div>"""

if target in html:
    html = html.replace(target, portfolio_section)
    print("Successfully injected portfolioStressSection into viewStress!")
    with open('app/cockpit.html', 'w', encoding='utf-8') as f:
        f.write(html)
    shutil.copyfile('app/cockpit.html', 'app/index.html')
    print("Synchronized cockpit.html -> index.html")
else:
    print("Target not matched in html")
