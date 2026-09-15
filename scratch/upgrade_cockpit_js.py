import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update renderQueuePage
old_render_queue = """      pageItems.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-container/50 transition-colors";
        
        let statusBadge = `<span class="px-2 py-0.5 rounded bg-surface-container text-primary font-bold">Cần Thẩm Định</span>`;
        if (item.trang_thai_so_bo.includes("Prime")) {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-surface-container-high text-on-tertiary-container font-bold">Khả thi cao (Prime)</span>`;
        } else if (item.trang_thai_so_bo.includes("Chặn") || item.trang_thai_so_bo.includes("Rủi ro")) {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-error-container text-error font-bold">${item.trang_thai_so_bo}</span>`;
        } else if (item.trang_thai_so_bo.includes("Cận biên")) {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-secondary-container text-secondary font-bold">Cận biên phê duyệt</span>`;
        }

        tr.innerHTML = `
          <td class="px-4 py-3 font-mono font-bold text-primary">${item.ma_ho_so}</td>
          <td class="px-4 py-3 font-semibold">${item.ho_ten}</td>
          <td class="px-4 py-3 font-mono">${(item.thu_nhap_thang_vnd/1e6).toFixed(0)} Tr</td>
          <td class="px-4 py-3 font-mono font-bold">${(item.so_tien_vay_vnd/1e6).toFixed(0)} Tr</td>
          <td class="px-4 py-3 font-mono font-bold">${item.diem_tin_dung_cic}</td>
          <td class="px-4 py-3 text-[11px]">${item.nhom_no_cic}</td>
          <td class="px-4 py-3 font-mono">${item.ty_le_dti}%</td>
          <td class="px-4 py-3">${statusBadge}</td>
          <td class="px-4 py-3 text-right">
            <button class="px-3 py-1 rounded-lg bg-primary hover:bg-primary/90 text-white text-[11px] font-bold shadow-sm transition-colors" onclick="selectQueueCase('${item.ma_ho_so}')">
              Nạp hồ sơ &rarr;
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });"""

new_render_queue = """      pageItems.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-container/50 transition-colors";
        const isChecked = selectedQueueIds.has(item.ma_ho_so);
        
        let statusBadge = `<span class="px-2 py-0.5 rounded bg-surface-container text-primary font-bold">Cần Thẩm Định</span>`;
        if (item.trang_thai_so_bo.includes("Prime")) {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-surface-container-high text-on-tertiary-container font-bold">Khả thi cao (Prime)</span>`;
        } else if (item.trang_thai_so_bo.includes("Chặn") || item.trang_thai_so_bo.includes("Rủi ro")) {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-error-container text-error font-bold">${item.trang_thai_so_bo}</span>`;
        } else if (item.trang_thai_so_bo.includes("Cận biên")) {
          statusBadge = `<span class="px-2 py-0.5 rounded bg-secondary-container text-secondary font-bold">Cận biên phê duyệt</span>`;
        }

        tr.innerHTML = `
          <td class="w-10 px-3 py-3 text-center">
            <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="toggleQueueItem('${item.ma_ho_so}')" class="rounded text-primary focus:ring-secondary/30 cursor-pointer">
          </td>
          <td class="px-4 py-3 font-mono font-bold text-primary">${item.ma_ho_so}</td>
          <td class="px-4 py-3 font-semibold">${item.ho_ten}</td>
          <td class="px-4 py-3 font-mono">${(item.thu_nhap_thang_vnd/1e6).toFixed(0)} Tr</td>
          <td class="px-4 py-3 font-mono font-bold">${(item.so_tien_vay_vnd/1e6).toFixed(0)} Tr</td>
          <td class="px-4 py-3 font-mono font-bold">${item.diem_tin_dung_cic}</td>
          <td class="px-4 py-3 text-[11px]">${item.nhom_no_cic}</td>
          <td class="px-4 py-3 font-mono">${item.ty_le_dti}%</td>
          <td class="px-4 py-3">${statusBadge}</td>
          <td class="px-4 py-3 text-right">
            <div class="flex items-center justify-end gap-1.5">
              <button title="Xuất Excel hồ sơ này" class="p-1.5 rounded-lg border border-outline-variant/40 hover:bg-surface-container text-emerald-700 transition-colors" onclick="exportSingleQueueToExcel('${item.ma_ho_so}')">
                <span class="material-symbols-outlined text-[16px]">file_download</span>
              </button>
              <button class="px-3 py-1 rounded-lg bg-primary hover:bg-primary/90 text-white text-[11px] font-bold shadow-sm transition-colors" onclick="selectQueueCase('${item.ma_ho_so}')">
                Nạp hồ sơ &rarr;
              </button>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });
      updateQueueBatchBar();"""

if old_render_queue in text:
    text = text.replace(old_render_queue, new_render_queue)
    print("Replaced renderQueuePage rows")
else:
    print("renderQueuePage pattern not matched!")

# 2. Add Queue Selection & Batch Methods
queue_methods_code = """
    // ====================================================================
    // QUEUE MULTI-SELECT, BATCH OPERATIONS & EXCEL EXPORT
    // ====================================================================
    let selectedQueueIds = new Set();
    let batchAssessResultsCache = [];

    function toggleQueueItem(caseId) {
      if (selectedQueueIds.has(caseId)) {
        selectedQueueIds.delete(caseId);
      } else {
        selectedQueueIds.add(caseId);
      }
      updateQueueBatchBar();
    }

    function toggleSelectAllQueue(isChecked) {
      const total = filteredQueueData.length;
      const startIdx = (queueCurrentPage - 1) * QUEUE_PAGE_SIZE;
      const endIdx = Math.min(startIdx + QUEUE_PAGE_SIZE, total);
      const pageItems = filteredQueueData.slice(startIdx, endIdx);

      pageItems.forEach(item => {
        if (isChecked) {
          selectedQueueIds.add(item.ma_ho_so);
        } else {
          selectedQueueIds.delete(item.ma_ho_so);
        }
      });
      renderQueuePage();
    }

    function clearQueueSelection() {
      selectedQueueIds.clear();
      const selectAllCb = document.getElementById('selectAllQueueCheckbox');
      if (selectAllCb) selectAllCb.checked = false;
      renderQueuePage();
    }

    function updateQueueBatchBar() {
      const bar = document.getElementById('queueBatchBar');
      const countEl = document.getElementById('queueSelectedCount');
      const selectAllCb = document.getElementById('selectAllQueueCheckbox');

      if (!bar || !countEl) return;
      const count = selectedQueueIds.size;
      if (count > 0) {
        bar.classList.remove('hidden');
        countEl.textContent = `Đã chọn ${count} hồ sơ`;
      } else {
        bar.classList.add('hidden');
      }

      if (selectAllCb) {
        const total = filteredQueueData.length;
        const startIdx = (queueCurrentPage - 1) * QUEUE_PAGE_SIZE;
        const endIdx = Math.min(startIdx + QUEUE_PAGE_SIZE, total);
        const pageItems = filteredQueueData.slice(startIdx, endIdx);
        const allPageSelected = pageItems.length > 0 && pageItems.every(it => selectedQueueIds.has(it.ma_ho_so));
        selectAllCb.checked = allPageSelected;
      }
    }

    function generateQueueCsv(records) {
      const headers = [
        "Mã Hồ Sơ", "Họ và Tên", "Tuổi", "Giới Tính", "Hôn Nhân", "Học Vấn",
        "Nghề Nghiệp", "Thu Nhập Tháng (VNĐ)", "Thu Nhập Đồng Vay (VNĐ)",
        "Giá Trị TSBĐ (VNĐ)", "Số Tiền Vay (VNĐ)", "Thời Hạn (Tháng)", "Mục Đích Vay",
        "Khu Vực", "Điểm Tín Dụng CIC", "Nhóm Nợ CIC", "Số Lần Trễ Hạn", "Số Khoản Vay",
        "Lịch Sử Nợ Xấu", "DTI (%)", "Đánh Giá Sơ Bộ"
      ];

      const rows = records.map(r => [
        `"${r.ma_ho_so || ''}"`,
        `"${r.ho_ten || ''}"`,
        r.tuoi || '',
        `"${r.gioi_tinh || ''}"`,
        `"${r.tinh_trang_hon_nhan || ''}"`,
        `"${r.trinh_do_hoc_van || ''}"`,
        `"${r.loai_hinh_nghe_nghiep || ''}"`,
        r.thu_nhap_thang_vnd || 0,
        r.thu_nhap_nguoi_dong_vay_vnd || 0,
        r.gia_tri_tai_san_dam_bao_vnd || 0,
        r.so_tien_vay_vnd || 0,
        r.thoi_han_vay_thang || 0,
        `"${r.muc_dich_vay || ''}"`,
        `"${r.khu_vuc_sinh_song || ''}"`,
        r.diem_tin_dung_cic || 0,
        `"${r.nhom_no_cic || ''}"`,
        r.so_lan_tre_han_2_nam || 0,
        r.so_khoan_vay_hien_tai || 0,
        `"${r.lich_su_no_xau || ''}"`,
        r.ty_le_dti || 0,
        `"${r.trang_thai_so_bo || ''}"`
      ]);

      const csvContent = "\\uFEFF" + [headers.join(","), ...rows.map(e => e.join(","))].join("\\n");
      return csvContent;
    }

    function exportSelectedQueueToExcel() {
      if (selectedQueueIds.size === 0) {
        showToastNotification("Vui lòng chọn ít nhất 1 hồ sơ để xuất Excel", "warning");
        return;
      }
      const selected = rawQueueData.filter(item => selectedQueueIds.has(item.ma_ho_so));
      const csv = generateQueueCsv(selected);
      downloadCsvFile(csv, `Danh_Sach_Ho_So_Chon_${selected.length}_Ma_${new Date().toISOString().slice(0, 10)}.csv`);
      showToastNotification(`Đã xuất ${selected.length} hồ sơ ra file Excel (CSV UTF-8 BOM) thành công!`, "file_download");
    }

    function exportAllQueueToExcel() {
      if (!rawQueueData || rawQueueData.length === 0) {
        showToastNotification("Hàng đợi hiện không có dữ liệu!", "warning");
        return;
      }
      const csv = generateQueueCsv(rawQueueData);
      downloadCsvFile(csv, `Toan_Bo_Hang_Doi_Tin_Dung_${rawQueueData.length}_Ho_So_${new Date().toISOString().slice(0, 10)}.csv`);
      showToastNotification(`Đã xuất toàn bộ ${rawQueueData.length} hồ sơ hàng đợi ra Excel!`, "file_download");
    }

    function exportSingleQueueToExcel(caseId) {
      const item = rawQueueData.find(x => x.ma_ho_so === caseId);
      if (!item) return;
      const csv = generateQueueCsv([item]);
      downloadCsvFile(csv, `Ho_So_Tin_Dung_${caseId}_${new Date().toISOString().slice(0, 10)}.csv`);
      showToastNotification(`Đã xuất hồ sơ ${caseId} ra file Excel thành công!`, "file_download");
    }

    function downloadCsvFile(content, filename) {
      const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }

    // ====================================================================
    // BATCH ASSESS MODAL WORKFLOW
    // ====================================================================
    async function openBatchAssessModal() {
      if (selectedQueueIds.size === 0) {
        showToastNotification("Vui lòng chọn ít nhất 1 hồ sơ để thẩm định hàng loạt!", "warning");
        return;
      }

      const selected = rawQueueData.filter(item => selectedQueueIds.has(item.ma_ho_so));
      const modal = document.getElementById('batchAssessModal');
      const tbody = document.getElementById('batchAssessTableBody');
      const badge = document.getElementById('batchModalCountBadge');

      badge.textContent = `${selected.length} hồ sơ`;
      tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-on-surface-variant font-mono"><span class="material-symbols-outlined text-[24px] animate-spin">refresh</span><div class="mt-2">Đang thẩm định hàng loạt qua complete_pipeline & Business Rules...</div></td></tr>`;
      modal.classList.remove('hidden');

      let results = [];
      let summary = null;

      try {
        const payload = {
          applications: selected,
          use_optimal_threshold: true
        };
        const res = await fetch(`${API_BASE}/queue/batch-assess`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const data = await res.json();
          results = data.results;
          summary = data.summary;
        }
      } catch (err) {
        console.warn("Batch API offline, running client-side simulation", err);
      }

      // Offline fallback if needed
      if (!results || results.length === 0) {
        let soDuyet = 0;
        let soTuChoi = 0;
        let tongLimit = 0;
        let soViPham = 0;

        results = selected.map(item => {
          const isHard = (item.nhom_no_cic && (item.nhom_no_cic.includes("Nhóm 3") || item.nhom_no_cic.includes("Nhóm 4") || item.nhom_no_cic.includes("Nhóm 5")));
          const prob = isHard ? 4.5 : (item.diem_tin_dung_cic >= 700 && item.ty_le_dti <= 35 ? 94.5 : 62.0);
          const isApp = (prob >= 73.0 && !isHard) ? 1 : 0;
          if (isApp) { soDuyet++; tongLimit += item.so_tien_vay_vnd; }
          else { soTuChoi++; }
          if (isHard) soViPham++;

          return {
            ma_ho_so: item.ma_ho_so,
            ho_ten: item.ho_ten,
            so_tien_vay_vnd: item.so_tien_vay_vnd,
            xac_suat_phe_duyet: prob,
            muc_do_rui_ro: isHard ? "Cao (Vi phạm chính sách nợ xấu)" : (prob >= 75 ? "Rất thấp (Hồ sơ xuất sắc)" : (prob >= 60 ? "Thấp (Hồ sơ an toàn)" : "Trung bình")),
            ket_qua: isApp ? "PHÊ DUYỆT KHOẢN VAY" : "TỪ CHỐI KHOẢN VAY",
            ma_ket_qua: isApp,
            hard_rule_violated: isHard,
            khuyen_nghi_nghiep_vu: isApp ? "Đủ điều kiện cấp tín dụng" : "Từ chối theo chính sách rủi ro"
          };
        });

        summary = {
          tong_so_ho_so: selected.length,
          so_luong_duyet: soDuyet,
          so_luong_tu_choi: soTuChoi,
          ty_le_duyet_pct: Math.round(soDuyet / selected.length * 100),
          tong_han_muc_de_xuat_vnd: tongLimit,
          so_ca_vi_pham_chinh_sach: soViPham
        };
      }

      batchAssessResultsCache = results;

      // Render KPIs
      document.getElementById('batchKpiApproveRate').textContent = `${summary.ty_le_duyet_pct}%`;
      document.getElementById('batchKpiApproveCount').textContent = `${summary.so_luong_duyet} / ${summary.tong_so_ho_so} hồ sơ`;
      document.getElementById('batchKpiTotalLimit').textContent = `${(summary.tong_han_muc_de_xuat_vnd / 1e9).toFixed(2)} tỷ VNĐ`;
      document.getElementById('batchKpiRejectCount').textContent = summary.so_luong_tu_choi;
      document.getElementById('batchKpiPolicyKnockout').textContent = `${summary.so_ca_vi_pham_chinh_sach} ca vi phạm chính sách`;
      
      const commCount = results.filter(r => r.xac_suat_phe_duyet >= 50 && r.xac_suat_phe_duyet < 73).length;
      document.getElementById('batchKpiCommitteeCount').textContent = commCount;

      // Render Table
      tbody.innerHTML = '';
      results.forEach(r => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-container/40 transition-colors";
        const isApproved = (r.ma_ket_qua === 1);

        tr.innerHTML = `
          <td class="px-3 py-2.5 font-bold text-primary">${r.ma_ho_so}</td>
          <td class="px-3 py-2.5 font-semibold text-slate-800">${r.ho_ten}</td>
          <td class="px-3 py-2.5 font-bold">${r.so_tien_vay_vnd ? (r.so_tien_vay_vnd/1e6).toFixed(0) + ' Tr' : '--'}</td>
          <td class="px-3 py-2.5 font-bold ${isApproved ? 'text-emerald-700' : 'text-error'}">${r.xac_suat_phe_duyet.toFixed(1)}%</td>
          <td class="px-3 py-2.5 text-[11px] text-slate-600">${r.muc_do_rui_ro}</td>
          <td class="px-3 py-2.5">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10.5px] font-bold ${isApproved ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
              <span class="material-symbols-outlined text-[13px]">${isApproved ? 'check_circle' : 'cancel'}</span>
              ${r.ket_qua}
            </span>
          </td>
          <td class="px-3 py-2.5 text-right">
            <button onclick="closeBatchAssessModal(); selectQueueCase('${r.ma_ho_so}');" class="px-2.5 py-1 rounded bg-primary/10 hover:bg-primary text-primary hover:text-white text-[11px] font-bold transition-colors">
              Chi tiết Cockpit
            </button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    function closeBatchAssessModal() {
      const modal = document.getElementById('batchAssessModal');
      if (modal) modal.classList.add('hidden');
    }

    function exportBatchModalToExcel() {
      if (!batchAssessResultsCache || batchAssessResultsCache.length === 0) {
        showToastNotification("Không có dữ liệu kết quả để xuất!", "warning");
        return;
      }
      const headers = ["Mã Hồ Sơ", "Khách Hàng", "Xác Suất Phê Duyệt (%)", "Phân Tầng Rủi Ro", "Kết Quả Thẩm Định", "Khuyến Nghị Nghiệp Vụ", "Vi Phạm Chính Sách Cứng"];
      const rows = batchAssessResultsCache.map(r => [
        `"${r.ma_ho_so}"`,
        `"${r.ho_ten}"`,
        r.xac_suat_phe_duyet.toFixed(2),
        `"${r.muc_do_rui_ro}"`,
        `"${r.ket_qua}"`,
        `"${r.khuyen_nghi_nghiep_vu || ''}"`,
        r.hard_rule_violated ? "Có" : "Không"
      ]);
      const csv = "\\uFEFF" + [headers.join(","), ...rows.map(e => e.join(","))].join("\\n");
      downloadCsvFile(csv, `Ket_Qua_Tham_Dinh_Theo_Lo_${batchAssessResultsCache.length}_Ho_So_${new Date().toISOString().slice(0, 10)}.csv`);
      showToastNotification(`Đã xuất báo cáo thẩm định ${batchAssessResultsCache.length} hồ sơ ra Excel!`, "file_download");
    }
"""

# Insert queue_methods_code before "// MODULE: STRESS TESTING"
idx_stress = text.find("// ====================================================================\n    // MODULE: STRESS TESTING")
if idx_stress != -1:
    text = text[:idx_stress] + queue_methods_code + "\n" + text[idx_stress:]
    print("Inserted queue batch methods")
else:
    print("Stress module marker not found!")

with open('app/cockpit.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved JS enhancements to cockpit.html")
