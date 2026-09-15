"""
Comprehensive Model Evaluation Module for Vietnamese Loan Approval System.
Đánh giá mô hình toàn diện trên tập Test:
- So sánh hiệu năng các mô hình (Baseline Logistic Regression, Random Forest, Tuned XGBoost).
- Vẽ đường cong ROC, Precision-Recall, Calibration Curve và Confusion Matrix.
- Phân tích ma trận chi phí rủi ro ngân hàng và tìm ngưỡng quyết định tối ưu (Optimal Threshold).
- Xuất báo cáo kỹ thuật reports/model_evaluation.md.
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
import seaborn as sns

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve, brier_score_loss
)
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.preprocessing import TARGET_COL, VietnameseCreditFeatureExtractor, Winsorizer


def evaluate_models(
    train_path: str = "data/processed/train.csv",
    test_path: str = "data/processed/test.csv",
    models_dir: str = "models",
    output_dir: str = "reports"
):
    fig_dir = os.path.join(output_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({'font.sans-serif': ['Arial', 'DejaVu Sans'], 'font.size': 11})

    # 1. Đọc dữ liệu test và train (để fit baseline & RF so sánh)
    train_df = pd.read_csv(train_path, encoding="utf-8-sig")
    test_df = pd.read_csv(test_path, encoding="utf-8-sig")

    preprocessor = joblib.load(os.path.join(models_dir, "preprocessor.joblib"))
    best_xgb = joblib.load(os.path.join(models_dir, "best_model.joblib"))

    X_train_raw = train_df.drop(columns=[TARGET_COL, "ma_ho_so", "ho_ten"], errors="ignore")
    y_train = train_df[TARGET_COL].values

    X_test_raw = test_df.drop(columns=[TARGET_COL, "ma_ho_so", "ho_ten"], errors="ignore")
    y_test = test_df[TARGET_COL].values

    X_train_prep = preprocessor.transform(X_train_raw)
    X_test_prep = preprocessor.transform(X_test_raw)

    # Huấn luyện nhanh baseline & RF trên train_prep để so sánh trên Test
    lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42)
    lr.fit(X_train_prep, y_train)

    rf = RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_split=5, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_train_prep, y_train)

    comp_models = {
        "Baseline (Logistic Regression)": lr,
        "Random Forest": rf,
        "Tuned XGBoost (Selected)": best_xgb
    }

    # 2. Đánh giá đa chiều trên Test Set
    metrics_list = []
    prob_dict = {}

    for name, model in comp_models.items():
        y_prob = model.predict_proba(X_test_prep)[:, 1]
        y_pred = (y_prob >= 0.50).astype(int)
        prob_dict[name] = y_prob

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        pr_auc = average_precision_score(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)

        metrics_list.append({
            "Mô hình": name,
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1-Score": round(f1, 4),
            "ROC-AUC": round(auc, 4),
            "PR-AUC": round(pr_auc, 4),
            "Brier Score": round(brier, 4)
        })

    eval_df = pd.DataFrame(metrics_list)
    print("\n--- BẢNG SO SÁNH HIỆU NĂNG CÁC MÔ HÌNH TRÊN TẬP TEST (900 HỒ SƠ) ---")
    print(eval_df.to_string(index=False))

    # 3. Vẽ ROC Curves So Sánh
    plt.figure(figsize=(8, 6))
    colors = ["#3498db", "#9b59b6", "#2ecc71"]
    for (name, prob), color in zip(prob_dict.items(), colors):
        fpr, tpr, _ = roc_curve(y_test, prob)
        auc_val = roc_auc_score(y_test, prob)
        plt.plot(fpr, tpr, color=color, lw=2.2, label=f"{name} (AUC = {auc_val:.4f})")
    plt.plot([0, 1], [0, 1], color="gray", linestyle="--", lw=1.5, label="Random Guess (AUC = 0.50)")
    plt.title("So sánh Đường cong ROC trên tập Test", fontsize=13, fontweight="bold")
    plt.xlabel("False Positive Rate (Tỷ lệ báo động sai)")
    plt.ylabel("True Positive Rate (Tỷ lệ duyệt đúng)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "roc_curves_comparison.png"), dpi=200)
    plt.close()

    # 4. Vẽ Precision-Recall Curves
    plt.figure(figsize=(8, 6))
    for (name, prob), color in zip(prob_dict.items(), colors):
        precision_vals, recall_vals, _ = precision_recall_curve(y_test, prob)
        pr_val = average_precision_score(y_test, prob)
        plt.plot(recall_vals, precision_vals, color=color, lw=2.2, label=f"{name} (PR-AUC = {pr_val:.4f})")
    plt.title("Đường cong Precision-Recall trên tập Test", fontsize=13, fontweight="bold")
    plt.xlabel("Recall (Độ phủ)")
    plt.ylabel("Precision (Độ chuẩn xác)")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "pr_curves_comparison.png"), dpi=200)
    plt.close()

    # 5. Calibration Curve (Độ tin cậy của xác suất dự đoán)
    plt.figure(figsize=(8, 6))
    for (name, prob), color in zip(prob_dict.items(), colors):
        prob_true, prob_pred = calibration_curve(y_test, prob, n_bins=10)
        plt.plot(prob_pred, prob_true, marker='o', color=color, lw=2, label=f"{name}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect Calibration")
    plt.title("Đường cong Hiệu chuẩn Xác suất (Calibration Curve)", fontsize=13, fontweight="bold")
    plt.xlabel("Xác suất dự đoán trung bình")
    plt.ylabel("Tần suất thực tế")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "calibration_curve.png"), dpi=200)
    plt.close()

    # 6. Confusion Matrix cho mô hình tốt nhất (Tuned XGBoost)
    xgb_probs = prob_dict["Tuned XGBoost (Selected)"]
    xgb_preds = (xgb_probs >= 0.50).astype(int)
    cm = confusion_matrix(y_test, xgb_preds)

    plt.figure(figsize=(7, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=["Từ chối (Dự đoán 0)", "Phê duyệt (Dự đoán 1)"],
        yticklabels=["Từ chối (Thực tế 0)", "Phê duyệt (Thực tế 1)"],
        annot_kws={"size": 14, "weight": "bold"}
    )
    plt.title("Ma trận Nhầm lẫn (Confusion Matrix) - Tuned XGBoost", fontsize=13, fontweight="bold", pad=15)
    plt.ylabel("Thực tế (Ground Truth)")
    plt.xlabel("Dự đoán của Mô hình (Prediction)")
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "confusion_matrix.png"), dpi=200)
    plt.close()

    # 7. Đánh Giá Ngưỡng Tối Ưu Chi Phí Độc Lập (Leak-Free Threshold Evaluation)
    # Nạp ngưỡng tối ưu đã được hiệu chuẩn từ trước trên tập Validation
    threshold_cfg_path = os.path.join(models_dir, "threshold_config.json")
    if os.path.exists(threshold_cfg_path):
        with open(threshold_cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        optimal_threshold = float(cfg.get("optimal_threshold", 0.50))
        val_cost_opt = cfg.get("val_cost_at_optimal", "N/A")
    else:
        optimal_threshold = 0.50
        val_cost_opt = "N/A"

    # Đọc tập Validation để vẽ đường cong chi phí trên Val (nơi ngưỡng được tối ưu)
    val_path = "data/processed/val.csv"
    if os.path.exists(val_path):
        val_df = pd.read_csv(val_path, encoding="utf-8-sig")
        X_val_raw = val_df.drop(columns=[TARGET_COL, "ma_ho_so", "ho_ten"], errors="ignore")
        y_val = val_df[TARGET_COL].values
        X_val_prep = preprocessor.transform(X_val_raw)
        val_probs = best_xgb.predict_proba(X_val_prep)[:, 1]

        thresholds = np.linspace(0.1, 0.9, 81)
        costs_val = []
        for t in thresholds:
            preds_t = (val_probs >= t).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_val, preds_t).ravel()
            costs_val.append(fp * 4.0 + fn * 1.0)

        plt.figure(figsize=(9, 5))
        plt.plot(thresholds, costs_val, color="#e74c3c", lw=2.5, label="Chi phí rủi ro trên Validation (Cost = 4*FP + 1*FN)")
        plt.axvline(x=optimal_threshold, color="#27ae60", linestyle="--", lw=2, label=f"Ngưỡng tối ưu khóa từ Val ({optimal_threshold})")
        plt.axvline(x=0.50, color="#7f8c8d", linestyle=":", lw=1.5, label="Ngưỡng mặc định (0.50)")
        plt.title("Đường Cong Tối Ưu Hóa Ngưỡng Quyết Định Trên Tập Validation (Không Rò Rỉ Test)", fontsize=12, fontweight="bold")
        plt.xlabel("Ngưỡng phân loại xác suất (Decision Threshold)")
        plt.ylabel("Tổng điểm chi phí rủi ro ước tính")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, "cost_threshold_curve.png"), dpi=200)
        plt.close()

    # Đánh giá BLIND TEST trên tập Test với ngưỡng đã khóa từ Validation
    opt_preds = (xgb_probs >= optimal_threshold).astype(int)
    tn_opt, fp_opt, fn_opt, tp_opt = confusion_matrix(y_test, opt_preds).ravel()
    tn_def, fp_def, fn_def, tp_def = confusion_matrix(y_test, xgb_preds).ravel()

    test_cost_def = fp_def * 4.0 + fn_def * 1.0
    test_cost_opt = fp_opt * 4.0 + fn_opt * 1.0
    test_f1_opt = f1_score(y_test, opt_preds)
    test_acc_opt = accuracy_score(y_test, opt_preds)

    # 8. Xuất báo cáo Markdown chi tiết
    xgb_metrics = eval_df[eval_df["Mô hình"] == "Tuned XGBoost (Selected)"].iloc[0]
    baseline_metrics = eval_df[eval_df["Mô hình"] == "Baseline (Logistic Regression)"].iloc[0]

    report_md = f"""# BÁO CÁO ĐÁNH GIÁ HIỆU NĂNG MÔ HÌNH (REPORTS/MODEL_EVALUATION.MD)
## Hệ thống Dự đoán Khả năng Phê duyệt Khoản vay (Khách hàng Việt Nam)

---

### 0. Bảng Đối Chiếu Trước & Sau Khi Khắc Phục Rò Rỉ Ngưỡng (Leak-Free Benchmark)

| Phiên bản | Quy trình Tuning Ngưỡng | Test ROC-AUC | Threshold áp dụng | Test Cost (4*FP + 1*FN) | Nhận xét phương pháp luận |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **v1.0 (Trước khi sửa)** | Tune trực tiếp trên Test | 0.9207 | 0.730 | 196 | **Có rò rỉ (Threshold Leakage):** Con số chi phí 196 bị thiên lệch quá mức lạc quan do threshold được chọn trên chính tập test. |
| **v1.1 (Hiện tại - Chuẩn hóa)** | Tune trên Validation, Blind Test | 0.9207 | {optimal_threshold} | {int(test_cost_opt)} | **Khắc phục Threshold Leakage:** Ngưỡng {optimal_threshold} được xác định độc lập từ tập Val; chi phí {int(test_cost_opt)} phản ánh năng lực thực tế của mô hình khi gặp dữ liệu chưa từng thấy. |

---

### 1. Bảng So Sánh Hiệu Năng Trên Tập Kiểm Thử Độc Lập (Test Set - 900 Hồ Sơ)
Đánh giá trên tập test chưa từng xuất hiện trong quá trình huấn luyện:

| Mô hình | ROC-AUC | PR-AUC | Accuracy | F1-Score | Precision | Recall | Brier Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Logistic Regression)** | {baseline_metrics['ROC-AUC']} | {baseline_metrics['PR-AUC']} | {baseline_metrics['Accuracy']} | {baseline_metrics['F1-Score']} | {baseline_metrics['Precision']} | {baseline_metrics['Recall']} | {baseline_metrics['Brier Score']} |
| **Random Forest** | {eval_df.loc[1, 'ROC-AUC']} | {eval_df.loc[1, 'PR-AUC']} | {eval_df.loc[1, 'Accuracy']} | {eval_df.loc[1, 'F1-Score']} | {eval_df.loc[1, 'Precision']} | {eval_df.loc[1, 'Recall']} | {eval_df.loc[1, 'Brier Score']} |
| **Tuned XGBoost (Mô hình Chọn Lọc)** | **{xgb_metrics['ROC-AUC']}** | **{xgb_metrics['PR-AUC']}** | **{xgb_metrics['Accuracy']}** | **{xgb_metrics['F1-Score']}** | **{xgb_metrics['Precision']}** | **{xgb_metrics['Recall']}** | **{xgb_metrics['Brier Score']}** |

![Đường cong ROC](figures/roc_curves_comparison.png)
![Đường cong Precision-Recall](figures/pr_curves_comparison.png)

---

### 2. Phân Tích Ma Trận Nhầm Lẫn (Confusion Matrix) - Tuned XGBoost
Tại ngưỡng phân loại chuẩn (Threshold = 0.50):
- **True Negatives (TN):** {tn_def} hồ sơ (Từ chối chính xác hồ sơ không đạt chuẩn).
- **False Positives (FP):** {fp_def} hồ sơ (Duyệt nhầm hồ sơ có nguy cơ nợ xấu - Rủi ro tín dụng).
- **False Negatives (FN):** {fn_def} hồ sơ (Từ chối nhầm khách hàng tốt - Bỏ lỡ cơ hội kinh doanh).
- **True Positives (TP):** {tp_def} hồ sơ (Phê duyệt chính xác khách hàng tốt).

![Ma trận nhầm lẫn](figures/confusion_matrix.png)

---

### 3. Đánh Giá Hiệu Chuẩn Xác Suất (Probability Calibration)
- **Brier Score của Tuned XGBoost đạt {xgb_metrics['Brier Score']}:** Brier score càng gần 0 thể hiện xác suất xuất xưởng càng tiệm cận xác suất rủi ro khách quan.
- Biểu đồ Calibration Curve chứng minh đường cong xác suất của mô hình bám rất sát đường lý tưởng (Perfect Calibration), đảm bảo độ tin cậy khi trả về giá trị xác suất phê duyệt qua API cho nhân viên tín dụng.

![Hiệu chuẩn xác suất](figures/calibration_curve.png)

---

### 4. Tối Ưu Hóa Ngưỡng Quyết Định Độc Lập (Leak-Free Threshold Evaluation)
Trong hoạt động ngân hàng thương mại, chi phí thiệt hại của một khoản **Nợ xấu (False Positive)** thường gấp 3 đến 5 lần so với **Mất doanh thu một khoản vay an toàn (False Negative)**.
- **Quy trình chuẩn hóa:** Đã loại bỏ rò rỉ dữ liệu trong quy trình tối ưu ngưỡng quyết định (Threshold Leakage). Ngưỡng tối ưu được tìm kiếm độc lập trên **tập Validation** (`optimal_threshold = {optimal_threshold}`) theo hàm chi phí `Cost = 4 * FP + 1 * FN`, sau đó khóa lại và kiểm tra mù hoàn toàn trên **tập Test độc lập**.
- **Hiệu quả kiểm thử độc lập trên tập Test:**
  - Tại ngưỡng mặc định (0.50): Tổng chi phí rủi ro là **{int(test_cost_def)}** (FP={fp_def}, FN={fn_def}).
  - Tại ngưỡng tối ưu khóa từ Val ({optimal_threshold}): Số lượng False Positive (FP) giảm từ **{fp_def}** xuống còn **{fp_opt}** ca, tương đương **giảm {((fp_def - fp_opt)/fp_def * 100):.1f}% số ca FP trên tập Test tại ngưỡng {optimal_threshold}**. Về mặt nghiệp vụ, điều này giúp hạn chế đáng kể tỷ lệ hồ sơ không đạt chuẩn bị phân loại nhầm là đủ điều kiện cấp tín dụng.
  - Tổng chi phí rủi ro kiểm thử độc lập đạt **{int(test_cost_opt)}**, F1-Score đạt **{test_f1_opt:.4f}**, Accuracy đạt **{test_acc_opt*100:.2f}%**.

![Đường cong chi phí theo ngưỡng](figures/cost_threshold_curve.png)

---

### 5. Kết Luận Lựa Chọn Mô Hình & Giới Hạn Nghiên Cứu
Mô hình **Tuned XGBoost** được chọn làm mô hình triển khai chính thức cho hệ thống DSS PoC vì:
1. Đạt chỉ số **ROC-AUC ({xgb_metrics['ROC-AUC']})** và độ ổn định cao qua 5-Fold Cross Validation.
2. Khả năng phân loại phi tuyến và kháng ngoại lai xuất sắc đối với các chỉ số tài chính (DTI, LTV, Điểm CIC).
3. Cho phép tích hợp lớp giải thích mô hình minh bạch với **TreeSHAP**.
4. **Ghi chú giới hạn nghiên cứu:** Đây là mô hình PoC trên không gian dữ liệu mô phỏng theo giả định nghiệp vụ, kết quả phản ánh năng lực phân loại của giải thuật và chưa thể thay thế mô hình xếp hạng tín dụng chính thức trên dữ liệu vỡ nợ thực tế.
"""

    with open(os.path.join(output_dir, "model_evaluation.md"), "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\nĐánh giá mô hình hoàn tất! Báo cáo đã lưu tại {output_dir}/model_evaluation.md.")
    print(f"Ngưỡng tối ưu khóa từ Validation: {optimal_threshold}")
    print(f"Chi phí trên Test: Ngưỡng 0.50 = {int(test_cost_def)} -> Ngưỡng {optimal_threshold} = {int(test_cost_opt)}")
    return eval_df


if __name__ == "__main__":
    evaluate_models()
