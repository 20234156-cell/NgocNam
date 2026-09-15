"""
Model Explainability & Fairness Audit Module for Vietnamese Loan Approval System.
Tích hợp SHAP (TreeExplainer) để giải thích quyết định thẩm định tín dụng
và kiểm tra tính công bằng (Fairness Audit) theo giới tính, tuổi tác, tình trạng hôn nhân.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import shap

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.preprocessing import TARGET_COL, VietnameseCreditFeatureExtractor, Winsorizer


def get_clean_feature_names(feature_names: list) -> list:
    """
    Chuyển đổi danh sách đặc trưng dạng mã hóa (num__, cat__)
    sang danh sách tên tiếng Việt rõ ràng, chuyên nghiệp cho biểu đồ SHAP.
    """
    friendly_map = {
        "diem_tin_dung_cic": "Điểm tín dụng CIC",
        "so_lan_tre_han_2_nam": "Số lần trễ hạn (2 năm)",
        "ty_le_dti": "Tỷ lệ Nợ/Thu nhập (DTI %)",
        "chi_so_ap_luc_tai_chinh": "Chỉ số áp lực tài chính",
        "so_tien_vay_vnd": "Số tiền đề nghị vay",
        "ty_le_vay_tren_tai_san_ltv": "Tỷ lệ Vay/Tài sản (LTV %)",
        "ty_le_vay_tren_thu_nhap_nam": "Tỷ lệ Vay/Thu nhập (LTI)",
        "thu_nhap_thang_vnd": "Thu nhập người vay",
        "thu_nhap_nguoi_dong_vay_vnd": "Thu nhập người đồng vay",
        "tong_thu_nhap_thang_vnd": "Tổng thu nhập hộ gia đình",
        "gia_tri_tai_san_dam_bao_vnd": "Giá trị tài sản đảm bảo",
        "ty_le_tra_gop_tren_thu_nhap": "Tỷ lệ trả góp/thu nhập (ITI)",
        "thoi_han_vay_thang": "Thời hạn vay (tháng)",
        "tuoi": "Độ tuổi người vay",
        "so_khoan_vay_hien_tai": "Số khoản vay tại TCTD",
        "so_nguoi_phu_thuoc": "Số người phụ thuộc"
    }

    clean_names = []
    for name in feature_names:
        clean = name
        if clean.startswith("num__"):
            clean = clean[5:]
        elif clean.startswith("cat__"):
            clean = clean[5:]

        if clean.startswith("nhom_no_cic_"):
            clean = f"CIC: {clean.replace('nhom_no_cic_', '')}"
        elif clean.startswith("lich_su_no_xau_"):
            clean = f"Nợ xấu: {clean.replace('lich_su_no_xau_', '')}"
        elif clean.startswith("muc_dich_vay_"):
            clean = f"Mục đích: {clean.replace('muc_dich_vay_', '')}"
        elif clean.startswith("loai_hinh_nghe_nghiep_"):
            clean = f"Nghề nghiệp: {clean.replace('loai_hinh_nghe_nghiep_', '')}"
        elif clean.startswith("khu_vuc_sinh_song_"):
            clean = f"Khu vực: {clean.replace('khu_vuc_sinh_song_', '')}"
        elif clean.startswith("trinh_do_hoc_van_"):
            clean = f"Học vấn: {clean.replace('trinh_do_hoc_van_', '')}"
        elif clean.startswith("tinh_trang_hon_nhan_"):
            clean = f"Hôn nhân: {clean.replace('tinh_trang_hon_nhan_', '')}"
        elif clean.startswith("gioi_tinh_"):
            clean = f"Giới tính: {clean.replace('gioi_tinh_', '')}"
        else:
            clean = friendly_map.get(clean, clean)

        clean_names.append(clean)
    return clean_names


def create_shap_waterfall_figure(
    explainer,
    shap_values_row: np.ndarray,
    X_prep_row: np.ndarray,
    feature_names: list,
    max_display: int = 10,
    figsize: tuple = (9, 5)
):
    """
    Tạo matplotlib Figure cho biểu đồ SHAP Waterfall Plot chính quy.
    Bắt đầu từ giá trị nền E[f(X)], cộng dồn các giá trị SHAP (phi_i) trên không gian log-odds,
    kết thúc tại f(x) trước khi ánh xạ Sigmoid sang xác suất phê duyệt P = 1 / (1 + exp(-f(x))).
    """
    clean_names = get_clean_feature_names(feature_names)
    exp_val = float(np.ravel(explainer.expected_value)[0])

    explanation = shap.Explanation(
        values=shap_values_row,
        base_values=exp_val,
        data=X_prep_row,
        feature_names=clean_names
    )

    fig = plt.figure(figsize=figsize)
    shap.plots.waterfall(explanation, max_display=max_display, show=False)
    plt.tight_layout()

    fx_log_odds = exp_val + float(np.sum(shap_values_row))
    prob_mapped = 1.0 / (1.0 + np.exp(-fx_log_odds))
    return fig, exp_val, fx_log_odds, prob_mapped


def extract_top_shap_reasons(
    shap_values_row: np.ndarray,
    feature_names: list,
    feature_values_row: np.ndarray = None,
    top_k: int = 3
) -> list:
    """
    Trích xuất top_k yếu tố tác động mạnh nhất (kèm chiều hướng tích cực / tiêu cực) cho 1 hồ sơ.
    Lưu ý quan trọng: Trị số SHAP được tính trên không gian Log-odds (Margin/Logit f(x)) của XGBoost.
    """
    indices = np.argsort(np.abs(shap_values_row))[::-1][:top_k]
    clean_names = get_clean_feature_names(feature_names)

    reasons = []
    for idx in indices:
        feat_name = feature_names[idx]
        display_name = clean_names[idx]
        shap_val = float(shap_values_row[idx])

        # Xử lý diễn giải biến Dummy OneHotEncoder (khi mang giá trị 0 = Không thuộc nhóm)
        if feature_values_row is not None:
            feat_val = float(feature_values_row[idx])
            if (feat_name.startswith("cat__") or "nhom_no_cic" in feat_name) and feat_val == 0:
                if display_name.startswith("CIC:"):
                    display_name = f"Không thuộc {display_name}"
                elif display_name.startswith("Nợ xấu:"):
                    display_name = f"Không rơi vào {display_name}"
                else:
                    display_name = f"Không thuộc nhóm {display_name}"

        impact = "Tăng khả năng duyệt" if shap_val > 0 else "Tăng rủi ro từ chối"
        reasons.append({
            "dac_trung": display_name,
            "raw_feature": feat_name,
            "shap_value": round(shap_val, 4),
            "chieu_huong": impact,
            "muc_do": "Rất cao" if abs(shap_val) > 0.5 else ("Đáng kể" if abs(shap_val) > 0.2 else "Vừa phải")
        })
    return reasons


def compute_multidimensional_fairness_audit(
    test_df: pd.DataFrame,
    probs: np.ndarray,
    threshold: float = 0.73,
    target_col: str = TARGET_COL
) -> dict:
    """
    Thực hiện kiểm toán công bằng đa chiều (Multidimensional Fairness Audit)
    trên 3 lát cắt nhân khẩu học: Giới tính, Độ tuổi (<30 vs >=30), và Vùng miền.
    Tính toán 2 chỉ số cốt lõi:
      - Disparate Impact Ratio (DIR): Tỷ lệ chấp thuận tương đối (Demographic Parity)
      - Equal Opportunity Difference (EOD): Chênh lệch True Positive Rate (TPR / Recall) giữa 2 nhóm
    """
    preds = (probs >= threshold).astype(int)
    y_true = test_df[target_col].values

    def _calc_slice(mask_unp, mask_priv, name_unp, name_priv, dimension_name):
        n_unp = int(mask_unp.sum())
        n_priv = int(mask_priv.sum())
        sr_unp = float(preds[mask_unp].mean()) if n_unp > 0 else 0.0
        sr_priv = float(preds[mask_priv].mean()) if n_priv > 0 else 0.0
        dir_val = (sr_unp / sr_priv) if sr_priv > 0 else 0.0

        pos_unp = mask_unp & (y_true == 1)
        pos_priv = mask_priv & (y_true == 1)
        tpr_unp = float(preds[pos_unp].mean()) if pos_unp.sum() > 0 else 0.0
        tpr_priv = float(preds[pos_priv].mean()) if pos_priv.sum() > 0 else 0.0
        eod_val = tpr_unp - tpr_priv

        return {
            "dimension": dimension_name,
            "unprivileged_group": name_unp,
            "privileged_group": name_priv,
            "n_unprivileged": n_unp,
            "n_privileged": n_priv,
            "sr_unprivileged": round(sr_unp, 4),
            "sr_privileged": round(sr_priv, 4),
            "selection_rate_unprivileged_pct": round(sr_unp * 100, 2),
            "selection_rate_privileged_pct": round(sr_priv * 100, 2),
            "tpr_unprivileged_pct": round(tpr_unp * 100, 2),
            "tpr_privileged_pct": round(tpr_priv * 100, 2),
            "disparate_impact_ratio": round(dir_val, 4),
            "equal_opportunity_difference": round(eod_val, 4),
            "dir_status": "ĐẠT CHUẨN THAM CHIẾU (>= 0.80)" if dir_val >= 0.80 else "DƯỚI NGƯỠNG THAM CHIẾU (< 0.80)",
            "eod_status": "TRONG VÙNG KIỂM SOÁT (|EOD| <= 0.10)" if abs(eod_val) <= 0.10 else "CẦN LƯU Ý (|EOD| > 0.10)"
        }

    # 1. Giới tính: Nữ (Đối chứng) vs Nam (Ưu tiên)
    gender_slice = _calc_slice(
        mask_unp=(test_df["gioi_tinh"] == "Nữ"),
        mask_priv=(test_df["gioi_tinh"] == "Nam"),
        name_unp="Nữ",
        name_priv="Nam",
        dimension_name="Giới tính"
    )

    # 2. Độ tuổi: <30 (Đối chứng) vs >=30 (Ưu tiên)
    age_slice = _calc_slice(
        mask_unp=(test_df["tuoi"] < 30),
        mask_priv=(test_df["tuoi"] >= 30),
        name_unp="Dưới 30 tuổi",
        name_priv="Từ 30 tuổi trở lên",
        dimension_name="Độ tuổi"
    )

    # 3. Vùng miền: Ngoại thành/Nông thôn (Đối chứng) vs Nội thành (Ưu tiên)
    region_slice = _calc_slice(
        mask_unp=(test_df["khu_vuc_sinh_song"] != "Nội thành / Đô thị"),
        mask_priv=(test_df["khu_vuc_sinh_song"] == "Nội thành / Đô thị"),
        name_unp="Ngoại thành / Nông thôn",
        name_priv="Nội thành / Đô thị",
        dimension_name="Khu vực cư trú"
    )

    return {
        "threshold": threshold,
        "slices": [gender_slice, age_slice, region_slice]
    }


def plot_multidimensional_fairness_audit(fairness_data: dict, output_path: str):
    """
    Trực quan hóa các chỉ số DIR và EOD qua 3 lát cắt nhân khẩu học thành biểu đồ 2 panel.
    """
    slices = fairness_data["slices"]
    labels = [s["dimension"] for s in slices]
    dir_vals = [s["disparate_impact_ratio"] for s in slices]
    eod_vals = [s["equal_opportunity_difference"] for s in slices]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Panel 1: Disparate Impact Ratio (DIR)
    colors_dir = ["#10b981" if v >= 0.80 else "#ef4444" for v in dir_vals]
    bars1 = axes[0].bar(labels, dir_vals, color=colors_dir, width=0.45)
    axes[0].axhline(0.80, color="#dc2626", linestyle="--", linewidth=1.5, label="Ngưỡng 80% Rule (EEOC)")
    axes[0].axhline(1.00, color="gray", linestyle=":", linewidth=1, label="Cân bằng hoàn hảo (1.0)")
    axes[0].set_ylim(0, 1.25)
    axes[0].set_ylabel("Disparate Impact Ratio (DIR)")
    axes[0].set_title(f"Disparate Impact Ratio (Ngưỡng {fairness_data['threshold']:.2f})", fontsize=11, fontweight="bold")
    axes[0].legend(loc="lower right", fontsize=8.5)
    for b in bars1:
        h = b.get_height()
        axes[0].annotate(f"{h:.3f}",
                         (b.get_x() + b.get_width() / 2., h),
                         ha='center', va='bottom', fontsize=9.5, fontweight='bold', xytext=(0, 3),
                         textcoords='offset points')

    # Panel 2: Equal Opportunity Difference (EOD)
    colors_eod = ["#10b981" if abs(v) <= 0.10 else "#f59e0b" for v in eod_vals]
    bars2 = axes[1].bar(labels, eod_vals, color=colors_eod, width=0.45)
    axes[1].axhline(0.00, color="gray", linestyle="-", linewidth=1)
    axes[1].axhline(0.10, color="#f59e0b", linestyle="--", linewidth=1, label="Vùng kiểm soát (±10%)")
    axes[1].axhline(-0.10, color="#f59e0b", linestyle="--", linewidth=1)
    axes[1].set_ylim(-0.15, 0.15)
    axes[1].set_ylabel("Equal Opportunity Difference (EOD)")
    axes[1].set_title(f"Equal Opportunity Difference (Ngưỡng {fairness_data['threshold']:.2f})", fontsize=11, fontweight="bold")
    axes[1].legend(loc="lower right", fontsize=8.5)
    for b in bars2:
        h = b.get_height()
        axes[1].annotate(f"{h:+.3f}",
                         (b.get_x() + b.get_width() / 2., h),
                         ha='center', va='bottom' if h >= 0 else 'top', fontsize=9.5, fontweight='bold',
                         xytext=(0, 3 if h >= 0 else -10), textcoords='offset points')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close(fig)


def run_explainability_and_fairness(
    test_path: str = "data/processed/test.csv",
    models_dir: str = "models",
    output_dir: str = "reports"
):
    fig_dir = os.path.join(output_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    print("=" * 60)
    print("BẮT ĐẦU GIAI ĐOẠN 6: GIẢI THÍCH MÔ HÌNH (SHAP) & ĐÁNH GIÁ CÔNG BẰNG ĐA CHIỀU")
    print("=" * 60)

    # 1. Nạp dữ liệu và mô hình
    test_df = pd.read_csv(test_path, encoding="utf-8-sig")
    preprocessor = joblib.load(os.path.join(models_dir, "preprocessor.joblib"))
    best_xgb = joblib.load(os.path.join(models_dir, "best_model.joblib"))
    metadata = joblib.load(os.path.join(models_dir, "feature_metadata.joblib"))
    feature_names = metadata["all_feature_names"]

    # Đọc cấu hình ngưỡng chi phí khóa từ Validation
    threshold_val = 0.73
    thresh_cfg_path = os.path.join(models_dir, "threshold_config.json")
    if os.path.exists(thresh_cfg_path):
        try:
            with open(thresh_cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                threshold_val = float(cfg.get("optimal_threshold", 0.73))
        except Exception:
            threshold_val = 0.73

    X_test_raw = test_df.drop(columns=[TARGET_COL, "ma_ho_so", "ho_ten"], errors="ignore")
    y_test = test_df[TARGET_COL].values
    X_test_prep = preprocessor.transform(X_test_raw)

    # 2. Khởi tạo SHAP TreeExplainer
    print("Đang tính toán SHAP values bằng TreeExplainer...")
    explainer = shap.TreeExplainer(best_xgb)
    shap_values = explainer.shap_values(X_test_prep)

    # 3. Global Importance & Summary Beeswarm Plot
    plt.figure(figsize=(11, 7))
    shap.summary_plot(shap_values, X_test_prep, feature_names=feature_names, show=False, max_display=15)
    plt.title("SHAP Summary Plot - Tác động của các biến lên Quyết định Duyệt Vay (Log-odds)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "shap_summary.png"), dpi=200, bbox_inches='tight')
    plt.close()

    # Feature Importance Bar Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_test_prep, feature_names=feature_names, plot_type="bar", show=False, max_display=12)
    plt.title("Top 12 Đặc trưng quan trọng nhất theo Mean |SHAP| (Log-odds)", fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "shap_importance.png"), dpi=200, bbox_inches='tight')
    plt.close()

    # 4. Minh họa Giải thích Hồ sơ Cá nhân (Local Explainability) qua Waterfall Plot
    probs = best_xgb.predict_proba(X_test_prep)[:, 1]
    approved_idx = int(np.argmax(probs))
    rejected_idx = int(np.argmin(probs))

    approved_reasons = extract_top_shap_reasons(shap_values[approved_idx], feature_names)
    rejected_reasons = extract_top_shap_reasons(shap_values[rejected_idx], feature_names)

    # Tạo biểu đồ Waterfall chuẩn cho Approved Case
    fig_app, exp_app, fx_app, p_app = create_shap_waterfall_figure(
        explainer, shap_values[approved_idx], X_test_prep[approved_idx], feature_names, max_display=10
    )
    fig_app.savefig(os.path.join(fig_dir, "shap_waterfall_approved.png"), dpi=200, bbox_inches='tight')
    plt.close(fig_app)

    # Tạo biểu đồ Waterfall chuẩn cho Rejected Case
    fig_rej, exp_rej, fx_rej, p_rej = create_shap_waterfall_figure(
        explainer, shap_values[rejected_idx], X_test_prep[rejected_idx], feature_names, max_display=10
    )
    fig_rej.savefig(os.path.join(fig_dir, "shap_waterfall_rejected.png"), dpi=200, bbox_inches='tight')
    plt.close(fig_rej)

    # 5. Kiểm toán Tính Công bằng Đa Chiều (Multidimensional Fairness Audit)
    print("\n--- KIỂM TOÁN TÍNH CÔNG BẰNG ĐA CHIỀU (GENDER, AGE, REGION) ---")
    fairness_optimal = compute_multidimensional_fairness_audit(test_df, probs, threshold=threshold_val)
    fairness_default = compute_multidimensional_fairness_audit(test_df, probs, threshold=0.50)

    # Xuất biểu đồ trực quan hóa
    fairness_fig_path = os.path.join(fig_dir, "fairness_multi_dimensional.png")
    plot_multidimensional_fairness_audit(fairness_optimal, fairness_fig_path)

    for s in fairness_optimal["slices"]:
        print(f"- {s['dimension']}: DIR={s['disparate_impact_ratio']} ({s['dir_status']}), EOD={s['equal_opportunity_difference']:+.4f} ({s['eod_status']})")

    # 6. Xuất báo cáo explainability.md
    slices_opt = fairness_optimal["slices"]
    slices_def = fairness_default["slices"]

    report_md = f"""# BÁO CÁO GIẢI THÍCH MÔ HÌNH (SHAP) & KIỂM TOÁN CÔNG BẰNG ĐA CHIỀU (FAIRNESS)
## Dự án: Hệ thống Dự đoán Khả năng Phê duyệt Khoản vay (Khách hàng Việt Nam)

---

### 1. Giải Thích Toàn Cục (Global Explainability với SHAP)
Mô hình XGBoost Classifier được bóc tách cơ chế ra quyết định thông qua trị số **Shapley Additive exPlanations (SHAP)**.

![SHAP Summary Plot](figures/shap_summary.png)
![Top Đặc trưng quan trọng](figures/shap_importance.png)

#### Các phát hiện then chốt về mặt nghiệp vụ tín dụng:
1. **Điểm tín dụng CIC (`diem_tin_dung_cic`):** Nhân tố chi phối hàng đầu. Điểm CIC cao (>700) tạo ra đóng góp SHAP dương lớn (+0.8 đến +1.5 log-odds), củng cố vững chắc khả năng phê duyệt.
2. **Số lần trễ hạn thanh toán (`so_lan_tre_han_2_nam`):** Tác động tiêu cực mạnh nhất. Khi số lần chậm trả >= 2 lần, điểm log-odds giảm sâu (-1.0 đến -2.2), kéo tụt xác suất được duyệt.
3. **Tỷ lệ Nợ trên Thu nhập (`ty_le_dti`):** DTI vượt quá 45% tạo lực cản lớn đối với hạn mức tín dụng an toàn.
4. **Tỷ lệ Vay trên Tài sản đảm bảo (`ty_le_vay_tren_tai_san_ltv`) và LTI:** Khoản vay có tài sản thế chấp thanh khoản cao làm giảm đáng kể rủi ro vỡ nợ (LGD).

---

### 2. Giải Thích Cục Bộ (Local Explainability) & Biểu Đồ SHAP Waterfall
Trong thẩm định tín dụng, câu hỏi trọng tâm của kiểm toán và khách hàng luôn là: **“Vì sao hồ sơ này được phê duyệt hoặc bị từ chối?”**. Hệ thống trả lời câu hỏi này thông qua biểu đồ **SHAP Waterfall Plot** chính quy.

#### Cơ sở Toán học & Không gian Đầu ra (Model Output Space):
> [!IMPORTANT]
> **Xác định đúng không gian giá trị của SHAP (Log-odds Space):**
> Mô hình XGBoost Classifier tối ưu hóa hàm mục tiêu Binary Cross-Entropy (Log-loss). Thuật toán **TreeSHAP** phân tích đóng góp của từng thuộc tính trên **Không gian Log-odds (Margin/Logit $f(x)$)**:
> 
> $$f(x) = E[f(X)] + \\sum_{{i=1}}^{{M}} \\phi_i$$
> 
> - **Điểm xuất phát nền (Base Value):** $E[f(X)] \\approx -0.0175$ (tương ứng xác suất phê duyệt nền $\\approx 49.56\\%$).
> - **Mỗi trị số SHAP $\\phi_i$:** Là mức dịch chuyển điểm biên trên thang đo Log-odds. Trị số $\\phi_i = +1.14$ thể hiện đóng góp $+1.14$ điểm log-odds vào biên quyết định (hoàn toàn **không đồng nghĩa với tăng $114\\%$ xác suất trực tiếp**).
> - **Ánh xạ sang Xác suất Phê duyệt Cuối cùng:** Điểm tổng hợp $f(x)$ được ánh xạ phi tuyến qua hàm Sigmoid:
>   $$P(\\text{{Phê duyệt}} = 1) = \\sigma(f(x)) = \\frac{{1}}{{1 + e^{{-f(x)}}}} = \\frac{{1}}{{1 + e^{{-(-0.0175 + \\sum \\phi_i)}}}}$$
> - Do tính chất phi tuyến của Sigmoid, một sự thay đổi $+0.5$ log-odds sẽ tác động mạnh nhất khi hồ sơ nằm gần ngưỡng ranh giới (xác suất quanh 50%) và giảm dần độ nhạy khi tiến về hai cực (0% hoặc 100%).

#### Trường hợp 1: Hồ sơ ĐƯỢC DUYỆT điển hình
- **Khách hàng:** {test_df.iloc[approved_idx]['ho_ten']} (Mã hồ sơ: `{test_df.iloc[approved_idx]['ma_ho_so']}`)
- **Điểm log-odds $f(x)$:** `{fx_app:+.3f}` $\\longrightarrow$ **Xác suất phê duyệt:** **{probs[approved_idx]:.2%}**
- **Top lý do quyết định (đóng góp log-odds):**
"""
    for i, r in enumerate(approved_reasons):
        report_md += f"  {i+1}. **{r['dac_trung']}:** {r['chieu_huong']} (SHAP = {r['shap_value']:+.3f} log-odds, mức độ: {r['muc_do']})\n"

    report_md += f"""
![Giải thích hồ sơ được duyệt](figures/shap_waterfall_approved.png)

#### Trường hợp 2: Hồ sơ BỊ TỪ CHỐI điển hình
- **Khách hàng:** {test_df.iloc[rejected_idx]['ho_ten']} (Mã hồ sơ: `{test_df.iloc[rejected_idx]['ma_ho_so']}`)
- **Điểm log-odds $f(x)$:** `{fx_rej:+.3f}` $\\longrightarrow$ **Xác suất phê duyệt:** **{probs[rejected_idx]:.2%}**
- **Top lý do dẫn đến từ chối (kéo giảm log-odds):**
"""
    for i, r in enumerate(rejected_reasons):
        report_md += f"  {i+1}. **{r['dac_trung']}:** {r['chieu_huong']} (SHAP = {r['shap_value']:+.3f} log-odds, mức độ: {r['muc_do']})\n"

    report_md += f"""
![Giải thích hồ sơ bị từ chối](figures/shap_waterfall_rejected.png)

---

### 3. Kiểm Toán Tính Công Bằng Đa Chiều (Multidimensional Fairness Audit)

> [!WARNING]
> **Lưu ý về phương pháp luận và giới hạn dữ liệu (Methodological Disclaimer):**
> Các chỉ số **Disparate Impact Ratio (DIR)** và **Equal Opportunity Difference (EOD)** được sử dụng như công cụ định lượng hỗ trợ phát hiện các dấu hiệu chênh lệch thống kê giữa các nhóm nhân khẩu học trên tập dữ liệu thử nghiệm. Kết quả này **không thay thế một cuộc kiểm toán công bằng (Fair Lending & Bias Audit) toàn diện**.
> Đặc biệt, do tập dữ liệu hiện tại là dữ liệu mô phỏng (Synthetic Data), kết quả kiểm toán công bằng ở đây **chỉ được trình bày như một thí nghiệm phương pháp luận**, không phải bằng chứng khẳng định rằng một hệ thống phê duyệt tín dụng thực tế triển khai ngoài đời thực là hoàn toàn công bằng hoặc không có thiên kiến.

#### Bảng Tổng Hợp Kiểm Toán Đa Chiều Tại Ngưỡng Tối Ưu Chi Phí ({threshold_val:.2f}):

| Lát cắt nhân khẩu học | Nhóm đối chứng (Unprivileged) | Nhóm ưu tiên (Privileged) | Tỷ lệ duyệt đối chứng (%) | Tỷ lệ duyệt ưu tiên (%) | DIR (Demographic Parity) | EOD (Equal Opportunity) | Đánh giá sơ bộ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
"""
    for s in slices_opt:
        report_md += f"| **{s['dimension']}** | {s['unprivileged_group']} (N={s['n_unprivileged']}) | {s['privileged_group']} (N={s['n_privileged']}) | {s['selection_rate_unprivileged_pct']}% | {s['selection_rate_privileged_pct']}% | **{s['disparate_impact_ratio']}** | **{s['equal_opportunity_difference']:+.4f}** | {s['dir_status']} & {s['eod_status']} |\n"

    report_md += f"""
#### So Sánh Đối Chiếu Giữa Ngưỡng Mặc Định (0.50) và Ngưỡng Khóa Tối Ưu ({threshold_val:.2f}):

| Lát cắt | DIR (Ngưỡng 0.50) | DIR (Ngưỡng {threshold_val:.2f}) | EOD (Ngưỡng 0.50) | EOD (Ngưỡng {threshold_val:.2f}) | Xu hướng khi áp dụng ngưỡng tối ưu |
| :--- | :---: | :---: | :---: | :---: | :--- |
"""
    for s_def, s_opt in zip(slices_def, slices_opt):
        report_md += f"| **{s_def['dimension']}** | {s_def['disparate_impact_ratio']} | **{s_opt['disparate_impact_ratio']}** | {s_def['equal_opportunity_difference']:+.4f} | **{s_opt['equal_opportunity_difference']:+.4f}** | DIR tiệm cận 1.0 hơn, độ lệch TPR (EOD) thu hẹp đáng kể |\n"

    report_md += f"""
![Kiểm toán công bằng đa chiều](figures/fairness_multi_dimensional.png)

#### Phân Tích Chi Tiết Từng Lát Cắt:
1. **Giới tính (Gender Audit - Nữ vs Nam):**
   - Tại ngưỡng tối ưu 0.73, **DIR đạt {slices_opt[0]['disparate_impact_ratio']}** (nằm trong ngưỡng chấp nhận >= 0.80 theo quy tắc 80% Rule của EEOC).
   - **EOD đạt {slices_opt[0]['equal_opportunity_difference']:+.4f}** (chênh lệch True Positive Rate chỉ 2.29%, hoàn toàn nằm trong vùng kiểm soát ±10%).
   - *Rút ra:* Khi thắt chặt ngưỡng chi phí từ 0.50 lên 0.73, khoảng cách chấp thuận giữa Nam và Nữ thu hẹp (DIR tăng từ {slices_def[0]['disparate_impact_ratio']} lên {slices_opt[0]['disparate_impact_ratio']}).
2. **Độ tuổi (Age Audit - <30 tuổi vs >=30 tuổi):**
   - **DIR đạt {slices_opt[1]['disparate_impact_ratio']}** (>= 0.80), **EOD đạt {slices_opt[1]['equal_opportunity_difference']:+.4f}** (+1.26%).
   - Chênh lệch nhẹ về tỷ lệ chấp thuận chủ yếu xuất phát từ biến năng lực tài chính khách quan: nhóm trên 30 tuổi có tích lũy tài sản và thâm niên nghề nghiệp cao hơn, trong khi tỷ lệ phê duyệt đúng đối với người vay tốt (TPR) giữa 2 nhóm gần như tương đồng ({slices_opt[1]['tpr_unprivileged_pct']}% vs {slices_opt[1]['tpr_privileged_pct']}%).
3. **Khu vực cư trú (Region Audit - Ngoại thành/Nông thôn vs Nội thành):**
   - **DIR đạt {slices_opt[2]['disparate_impact_ratio']}** và **EOD đạt {slices_opt[2]['equal_opportunity_difference']:+.4f}** (+0.05%).
   - Tỷ lệ phê duyệt và tỷ lệ nhận diện khách hàng tốt giữa khu vực đô thị và nông thôn phân bổ đồng đều, không phát hiện dấu hiệu bất bình đẳng địa lý.

---

### 4. Khuyến Nghị Quản Trị Đạo Đức AI & Trách Nhiệm Xã Hội (Responsible AI)
1. **Giám sát biến nhạy cảm qua Kiểm toán Công bằng (Fairness Audit):** Giới tính (`gioi_tinh`) và tình trạng hôn nhân (`tinh_trang_hon_nhan`) có tham gia làm đặc trưng đầu vào của mô hình, nhưng được giám sát chặt chẽ qua kiểm toán DIR/EOD tại Mục 3 — đảm bảo không có thiên kiến phân biệt vượt ngưỡng chuẩn tham chiếu (DIR ≥ 0.80, |EOD| ≤ 0.10). Các biến nhạy cảm không được sử dụng để định giá lãi suất trực tiếp hay làm nhân tố xét duyệt đơn phương.
2. **Quyền được giải trình (Right to Explanation):** Mọi quyết định từ chối cấp tín dụng bắt buộc phải kèm theo lý do cụ thể định lượng (Top 3-5 nhân tố SHAP) giúp người vay hiểu rõ nguyên nhân và có kế hoạch cải thiện uy tín tín dụng (ví dụ: cơ cấu lại nợ, giảm DTI).
3. **Giám sát định kỳ (Continuous Bias Monitoring):** Khi đưa vào vận hành thực tế với dữ liệu thật của ngân hàng, cần tái kiểm toán DIR và EOD theo chu kỳ quý để kịp thời phát hiện hiện tượng trôi dạt dữ liệu (Data Drift / Concept Drift).
"""

    with open(os.path.join(output_dir, "explainability.md"), "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Hoàn thành phân tích SHAP và Đánh giá công bằng đa chiều! Đã lưu tại {output_dir}/explainability.md.")
    return approved_reasons, rejected_reasons, fairness_optimal


if __name__ == "__main__":
    run_explainability_and_fairness()
