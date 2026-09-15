# -*- coding: utf-8 -*-
"""
Script to apply refinements for User Request 11:
1. Robust setFormValues for 100% reliable 1-click presets (Prime, Subprime, Borderline)
   updating all inputs, labels, captions, and case ID elements.
2. In renderResult: When Hard-rule Knockout is active, clearly display
   'N/A (BỊ CHẶN CỨNG)' and 'Model Score overridden by policy' to prevent any confusion.
"""

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. Update setFormValues
    old_set_form = """    function setFormValues(d) {
      document.getElementById('custCode').value = d.code;
      document.getElementById('custName').value = d.name;
      document.getElementById('custAge').value = d.age;
      document.getElementById('custGender').value = d.gender;
      document.getElementById('custMarital').value = d.marital;
      document.getElementById('custDependents').value = d.dependents;
      document.getElementById('custEducation').value = d.education;
      document.getElementById('custJob').value = d.job;
      document.getElementById('inputIncome').value = d.income;
      document.getElementById('inputCoIncome').value = d.coIncome;
      document.getElementById('inputCollateral').value = d.collateral;
      document.getElementById('inputLoanAmt').value = d.loanAmt;
      document.getElementById('inputLoanTenure').value = d.tenure;
      document.getElementById('inputLoanPurpose').value = d.purpose;
      document.getElementById('inputArea').value = d.area;
      document.getElementById('inputCicScore').value = d.cic;
      document.getElementById('inputDebtGroup').value = d.debtGroup;
      document.getElementById('inputDti').value = d.dti;
      document.getElementById('inputDelinquency').value = d.delinquency;
      document.getElementById('inputOpenLoans').value = d.openLoans;
      document.getElementById('inputPastDefault').value = d.pastDefault;

      document.getElementById('dispCaseId').textContent = d.code;
      document.getElementById('metaCaseId').textContent = d.code;
      document.getElementById('commCaseId').textContent = d.code;
      document.getElementById('commCustName').textContent = d.name;

      inputIncome.dispatchEvent(new Event('input'));
      inputCoIncome.dispatchEvent(new Event('input'));
      inputCollateral.dispatchEvent(new Event('input'));
      inputLoanAmt.dispatchEvent(new Event('input'));
      inputCicScore.dispatchEvent(new Event('input'));
      inputDti.dispatchEvent(new Event('input'));
    }"""

    new_set_form = """    function setFormValues(d) {
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) {
          el.value = val;
          el.classList.remove('border-error', 'ring-2', 'ring-error');
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        }
      };
      const setText = (id, txt) => {
        const el = document.getElementById(id);
        if (el) el.textContent = txt;
      };

      setVal('custCode', d.code);
      setVal('custName', d.name);
      setVal('custAge', d.age);
      setVal('custGender', d.gender);
      setVal('custMarital', d.marital);
      setVal('custDependents', d.dependents);
      setVal('custEducation', d.education);
      setVal('custJob', d.job);
      setVal('inputIncome', d.income);
      setVal('inputCoIncome', d.coIncome);
      setVal('inputCollateral', d.collateral);
      setVal('inputLoanAmt', d.loanAmt);
      setVal('inputLoanTenure', d.tenure);
      setVal('inputLoanPurpose', d.purpose);
      setVal('inputArea', d.area);
      setVal('inputCicScore', d.cic);
      setVal('inputDebtGroup', d.debtGroup);
      setVal('inputDti', d.dti);
      setVal('inputDelinquency', d.delinquency);
      setVal('inputOpenLoans', d.openLoans);
      setVal('inputPastDefault', d.pastDefault);

      // Đồng bộ toàn diện tất cả các nhãn hiển thị Case ID và thông số tóm tắt
      setText('dispCaseId', d.code);
      setText('metaCaseId', d.code);
      setText('commCaseId', d.code);
      setText('commCustName', d.name);
      setText('docCaseCode', d.code);
      setText('docApplicantName', d.name);
      setText('metaAmount', `${(d.loanAmt).toLocaleString('vi-VN')} đ`);
      setText('captionIncome', `~ ${(d.income / 1e6).toFixed(1)} triệu VNĐ`);
      setText('captionCoIncome', `~ ${(d.coIncome / 1e6).toFixed(1)} triệu VNĐ`);
      setText('captionCollateral', `~ ${(d.collateral / 1e9).toFixed(2)} tỷ VNĐ`);
      setText('captionLoanAmt', `~ ${(d.loanAmt / 1e6).toFixed(1)} triệu VNĐ`);
      setText('labelCicScore', `${d.cic} (${d.cic >= 700 ? 'Hạng 1 - Tối ưu' : (d.cic >= 600 ? 'Hạng 2 - Trung bình' : 'Hạng 3 - Rủi ro')})`);
      setText('labelDti', `${d.dti}%`);
    }"""

    if old_set_form in c:
        c = c.replace(old_set_form, new_set_form)
        print(f"1. Updated setFormValues in {filepath}")
    else:
        print(f"Could not find old setFormValues in {filepath}")

    # 2. Update renderResult for Hard-rule Knockout to override model score display
    old_render_part = """      if (isHardRule) {
        card.className = "relative overflow-hidden rounded-xl p-6 text-white shadow-xl transition-all duration-500 bg-gradient-to-r from-error via-primary-container to-primary";
        badge.textContent = "KẾT QUẢ: TỪ CHỐI TỰ ĐỘNG (POLICY REJECTED)";
        subtag.textContent = "HARD-RULE KNOCKOUT";
        desc.textContent = data.policy_reason || "Hồ sơ vi phạm quy tắc tín dụng cứng theo quy chuẩn Ngân hàng Nhà nước.";
        icon.textContent = "cancel";
        document.getElementById('probProgressBar').className = "h-full bg-error rounded-full transition-all duration-700";
      } else if (isApproved) {"""

    new_render_part = """      if (isHardRule) {
        // Chuẩn Production: Khi Hard-rule kích hoạt, điểm mô hình bị override hoàn toàn
        heroProb.textContent = "N/A";
        document.getElementById('metricProb').innerHTML = `N/A <span class="text-[11px] text-error font-sans font-semibold block mt-0.5">(Model ${probPercent.toFixed(1)}% bị override)</span>`;
        document.getElementById('probProgressBar').style.width = "0%";
        card.className = "relative overflow-hidden rounded-xl p-6 text-white shadow-xl transition-all duration-500 bg-gradient-to-r from-error via-primary-container to-primary";
        badge.textContent = "KẾT QUẢ: TỪ CHỐI TỰ ĐỘNG (POLICY REJECTED)";
        subtag.textContent = "HARD-RULE KNOCKOUT (MODEL OVERRIDDEN)";
        desc.textContent = `${data.policy_reason || "Hồ sơ vi phạm quy tắc tín dụng cứng theo quy chuẩn Ngân hàng Nhà nước."} [Lưu ý nghiệp vụ: Điểm xác suất mô hình ML (${probPercent.toFixed(1)}%) bị vô hiệu hóa hoàn toàn bởi Chính sách nợ xấu NHNN]`;
        icon.textContent = "gpp_bad";
        document.getElementById('probProgressBar').className = "h-full bg-error rounded-full transition-all duration-700";
      } else if (isApproved) {"""

    if old_render_part in c:
        c = c.replace(old_render_part, new_render_part)
        print(f"2. Updated Hard-rule renderResult in {filepath}")
    else:
        print(f"Could not find old render_part in {filepath}")

    # 3. Update Delta metric when isHardRule
    old_delta_part = """      metricDelta.textContent = `${delta >= 0 ? '+' : ''}${deltaPercent}%`;
      if (delta >= 0) {
        metricDeltaLabel.textContent = "Vượt ngưỡng an toàn";
        metricDeltaLabel.className = "text-[11px] text-on-tertiary-container font-semibold";
        deltaDot.className = "w-2 h-2 rounded-full bg-on-tertiary-container shrink-0";
        deltaNote.textContent = delta >= 0.10 ? "Delta > 10%: Đủ điều kiện giải ngân tiêu chuẩn" : "Delta tiệm cận: Cần thẩm định kỹ hồ sơ pháp lý";
      } else {
        metricDeltaLabel.textContent = "Dưới ngưỡng quy định";
        metricDeltaLabel.className = "text-[11px] text-error font-semibold";
        deltaDot.className = "w-2 h-2 rounded-full bg-error shrink-0";
        deltaNote.textContent = "Không đạt ngưỡng tối thiểu; cần biện pháp giảm thiểu rủi ro";
      }"""

    new_delta_part = """      if (isHardRule) {
        metricDelta.textContent = "OVERRIDE";
        metricDeltaLabel.textContent = "Bị chặn bởi Hard-Rule";
        metricDeltaLabel.className = "text-[11px] text-error font-semibold";
        deltaDot.className = "w-2 h-2 rounded-full bg-error shrink-0";
        deltaNote.textContent = `Chính sách NHNN loại trừ tuyệt đối, không căn cứ xác suất (Model: ${probPercent.toFixed(1)}%)`;
      } else {
        metricDelta.textContent = `${delta >= 0 ? '+' : ''}${deltaPercent}%`;
        if (delta >= 0) {
          metricDeltaLabel.textContent = "Vượt ngưỡng an toàn";
          metricDeltaLabel.className = "text-[11px] text-on-tertiary-container font-semibold";
          deltaDot.className = "w-2 h-2 rounded-full bg-on-tertiary-container shrink-0";
          deltaNote.textContent = delta >= 0.10 ? "Delta > 10%: Đủ điều kiện giải ngân tiêu chuẩn" : "Delta tiệm cận: Cần thẩm định kỹ hồ sơ pháp lý";
        } else {
          metricDeltaLabel.textContent = "Dưới ngưỡng quy định";
          metricDeltaLabel.className = "text-[11px] text-error font-semibold";
          deltaDot.className = "w-2 h-2 rounded-full bg-error shrink-0";
          deltaNote.textContent = "Không đạt ngưỡng tối thiểu; cần biện pháp giảm thiểu rủi ro";
        }
      }"""

    if old_delta_part in c:
        c = c.replace(old_delta_part, new_delta_part)
        print(f"3. Updated Delta metric in {filepath}")
    else:
        print(f"Could not find old delta_part in {filepath}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(c)
    print(f"Saved {filepath} successfully.")

if __name__ == '__main__':
    update_file('app/cockpit.html')
    update_file('app/index.html')
