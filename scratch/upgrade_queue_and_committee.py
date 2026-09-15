import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Queue Table Header in viewQueue:
# Add "Xuất Toàn Bộ Ra Excel" button in the header toolbar
old_header_btn = '''<button class="px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-[12px] font-semibold text-primary" onclick="loadQueueFromApi()">
                🔄 Làm Mới Hàng Đợi
              </button>'''

new_header_btn = '''<button class="px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-[12px] font-semibold text-primary" onclick="loadQueueFromApi()">
                🔄 Làm Mới
              </button>
              <button class="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[12px] font-semibold flex items-center gap-1.5 shadow-sm transition-colors" onclick="exportAllQueueToExcel()">
                <span class="material-symbols-outlined text-[16px]">file_download</span>
                <span>Xuất Toàn Bộ Excel</span>
              </button>'''

if old_header_btn in content:
    content = content.replace(old_header_btn, new_header_btn)
    print("1. Replaced header button in viewQueue")
else:
    print("Header button not matched!")

# 2. Add checkbox to table thead in viewQueue
old_queue_thead = '''              <thead class="bg-surface-container text-on-surface-variant uppercase tracking-wider font-semibold">
                <tr>
                  <th class="px-4 py-3">Mã Hồ Sơ</th>'''

new_queue_thead = '''              <thead class="bg-surface-container text-on-surface-variant uppercase tracking-wider font-semibold">
                <tr>
                  <th class="w-10 px-3 py-3 text-center">
                    <input type="checkbox" id="selectAllQueueCheckbox" onchange="toggleSelectAllQueue(this.checked)" class="rounded text-primary focus:ring-secondary/30 cursor-pointer" title="Chọn tất cả hồ sơ trên trang hiện tại">
                  </th>
                  <th class="px-4 py-3">Mã Hồ Sơ</th>'''

if old_queue_thead in content:
    content = content.replace(old_queue_thead, new_queue_thead)
    print("2. Added checkbox to queue table thead")
else:
    print("queue thead not matched!")

# 3. Add Queue Floating Batch Action Bar after queue pagination controls
old_queue_pagination = '''          <!-- Pagination Bar (Queue: 8 items / page) -->
          <div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-[12px] font-mono">
            <div class="text-on-surface-variant" id="queuePaginationInfo">Đang tải phân trang...</div>
            <div class="flex items-center gap-1.5" id="queuePaginationControls"></div>
          </div>
        </div>
      </div>'''

new_queue_pagination = '''          <!-- Pagination Bar (Queue: 8 items / page) -->
          <div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-[12px] font-mono">
            <div class="text-on-surface-variant" id="queuePaginationInfo">Đang tải phân trang...</div>
            <div class="flex items-center gap-1.5" id="queuePaginationControls"></div>
          </div>
        </div>

        <!-- Floating Batch Action Bar for Queue -->
        <div id="queueBatchBar" class="hidden fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-3 rounded-2xl bg-primary text-white shadow-2xl flex items-center gap-4 z-[9000] border border-surface-container-high animate-in fade-in slide-in-from-bottom duration-300 text-[13px] font-mono">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span id="queueSelectedCount" class="font-bold text-white">Đã chọn 0 hồ sơ</span>
          </div>
          <div class="h-4 w-px bg-white/20"></div>
          <div class="flex items-center gap-2">
            <button onclick="exportSelectedQueueToExcel()" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[12px] font-bold flex items-center gap-1.5 shadow-sm transition-colors">
              <span class="material-symbols-outlined text-[16px]">file_download</span>
              <span>Xuất Excel Đã Chọn</span>
            </button>
            <button onclick="openBatchAssessModal()" class="px-3 py-1.5 rounded-lg bg-secondary hover:bg-secondary/90 text-on-secondary text-[12px] font-bold flex items-center gap-1.5 shadow-sm transition-colors">
              <span class="material-symbols-outlined text-[16px]">fact_check</span>
              <span>Thẩm Định Hàng Loạt</span>
            </button>
            <button onclick="clearQueueSelection()" class="px-2.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 text-[12px] transition-colors">
              Bỏ chọn
            </button>
          </div>
        </div>
      </div>'''

if old_queue_pagination in content:
    content = content.replace(old_queue_pagination, new_queue_pagination)
    print("3. Added Queue Floating Batch Action Bar")
else:
    print("queue pagination not matched!")

# 4. Insert Batch Assess Modal before auditDetailModal
batch_assess_modal_html = '''
    <!-- ==================================================================== -->
    <!-- MODAL: THẨM ĐỊNH HÀNG LOẠT (BATCH ASSESSMENT SUMMARY MODAL) -->
    <!-- ==================================================================== -->
    <div id="batchAssessModal" class="fixed inset-0 bg-primary/60 backdrop-blur-sm z-[9999] flex items-center justify-center hidden p-4 animate-in fade-in duration-200">
      <div class="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-surface-container overflow-hidden animate-in zoom-in-95 duration-200">
        
        <!-- Modal Header -->
        <div class="p-5 border-b border-surface-container bg-surface-container-lowest flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-secondary-container/30 text-secondary flex items-center justify-center">
              <span class="material-symbols-outlined text-[24px]">fact_check</span>
            </div>
            <div>
              <h3 class="text-[17px] font-bold text-primary flex items-center gap-2">
                BẢNG KẾT QUẢ THẨM ĐỊNH TÍN DỤNG THEO LÔ (BATCH ASSESSMENT)
                <span id="batchModalCountBadge" class="px-2 py-0.5 rounded-full text-[11px] bg-primary text-white font-mono">0 hồ sơ</span>
              </h3>
              <p class="text-[12px] text-on-surface-variant">Tổng hợp kết quả đánh giá tự động từ mô hình AI và chính sách ngân hàng</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="exportBatchModalToExcel()" class="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-[12px] font-semibold flex items-center gap-1.5 transition-colors">
              <span class="material-symbols-outlined text-[16px]">file_download</span>
              <span>Xuất Báo Cáo Excel</span>
            </button>
            <button onclick="closeBatchAssessModal()" class="w-8 h-8 rounded-lg hover:bg-surface-container flex items-center justify-center text-on-surface-variant transition-colors">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        <!-- KPI Summary Cards -->
        <div class="p-5 bg-surface-container-low/50 grid grid-cols-2 sm:grid-cols-4 gap-3 border-b border-surface-container font-mono">
          <div class="p-3.5 rounded-xl bg-white border border-surface-container">
            <div class="text-[11px] text-on-surface-variant uppercase">Tỷ lệ phê duyệt</div>
            <div class="text-[20px] font-black text-emerald-700 mt-1" id="batchKpiApproveRate">0%</div>
            <div class="text-[10px] text-on-surface-variant" id="batchKpiApproveCount">0 / 0 hồ sơ</div>
          </div>
          <div class="p-3.5 rounded-xl bg-white border border-surface-container">
            <div class="text-[11px] text-on-surface-variant uppercase">Tổng hạn mức đề xuất</div>
            <div class="text-[18px] font-black text-primary mt-1" id="batchKpiTotalLimit">0 VNĐ</div>
            <div class="text-[10px] text-emerald-700">Các ca được phê duyệt</div>
          </div>
          <div class="p-3.5 rounded-xl bg-white border border-surface-container">
            <div class="text-[11px] text-on-surface-variant uppercase">Số ca từ chối</div>
            <div class="text-[20px] font-black text-error mt-1" id="batchKpiRejectCount">0</div>
            <div class="text-[10px] text-error" id="batchKpiPolicyKnockout">0 ca vi phạm chính sách</div>
          </div>
          <div class="p-3.5 rounded-xl bg-white border border-surface-container">
            <div class="text-[11px] text-on-surface-variant uppercase">Cần trình Hội đồng</div>
            <div class="text-[20px] font-black text-secondary mt-1" id="batchKpiCommitteeCount">0</div>
            <div class="text-[10px] text-on-surface-variant">Hồ sơ vùng cận biên</div>
          </div>
        </div>

        <!-- Results Table -->
        <div class="p-5 overflow-y-auto flex-1">
          <table class="w-full text-left text-[12px]">
            <thead class="bg-surface-container text-on-surface-variant uppercase tracking-wider font-semibold font-mono">
              <tr>
                <th class="px-3 py-2.5">Mã HS</th>
                <th class="px-3 py-2.5">Khách Hàng</th>
                <th class="px-3 py-2.5">Khoản Vay</th>
                <th class="px-3 py-2.5">Xác Suất AI</th>
                <th class="px-3 py-2.5">Phân Tầng Rủi Ro</th>
                <th class="px-3 py-2.5">Quyết Định AI</th>
                <th class="px-3 py-2.5 text-right">Thao Tác</th>
              </tr>
            </thead>
            <tbody id="batchAssessTableBody" class="divide-y divide-surface-container font-mono">
              <!-- Rendered dynamically -->
            </tbody>
          </table>
        </div>

        <!-- Modal Footer -->
        <div class="p-4 border-t border-surface-container bg-surface-container-lowest flex items-center justify-between text-[12px] font-mono">
          <div class="text-on-surface-variant flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px] text-emerald-600">verified</span>
            <span>Tất cả hồ sơ được thẩm định qua mô hình complete_pipeline.joblib & HardRulesEngine</span>
          </div>
          <button onclick="closeBatchAssessModal()" class="px-4 py-2 rounded-lg bg-surface-container hover:bg-surface-container-high text-primary font-bold transition-colors">
            Đóng bảng
          </button>
        </div>

      </div>
    </div>
'''

if 'id="batchAssessModal"' not in content:
    idx_modal = content.find('<div id="auditDetailModal"')
    if idx_modal != -1:
        content = content[:idx_modal] + batch_assess_modal_html + "\n" + content[idx_modal:]
        print("4. Inserted batchAssessModal")
    else:
        print("auditDetailModal not found!")

with open('app/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Saved preliminary changes to cockpit.html")
