"""
Model Training & Hyperparameter Optimization Module.
Huấn luyện và so sánh đa mô hình (Baseline Logistic Regression, Random Forest, XGBoost),
Cross-Validation 5-Fold, tối ưu siêu tham số bằng Optuna và đóng gói Pipeline tốt nhất.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.base import clone
import optuna

# Đảm bảo root directory có trong sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.preprocessing import TARGET_COL, VietnameseCreditFeatureExtractor, Winsorizer


def train_and_compare_models(
    train_path: str = "data/processed/train.csv",
    val_path: str = "data/processed/val.csv",
    models_dir: str = "models",
    random_state: int = 42
):
    from src.integrity import require_experiment_directory
    require_experiment_directory(models_dir)
    print("=" * 60)
    print("BẮT ĐẦU GIAI ĐOẠN 4: HUẤN LUYỆN VÀ SO SÁNH MÔ HÌNH")
    print("=" * 60)

    # 1. Nạp dữ liệu
    train_df = pd.read_csv(train_path, encoding="utf-8-sig")
    val_df = pd.read_csv(val_path, encoding="utf-8-sig")

    preprocessor = joblib.load(os.path.join(models_dir, "preprocessor.joblib"))

    X_train_raw = train_df.drop(columns=[TARGET_COL, "ma_ho_so", "ho_ten"], errors="ignore")
    y_train = train_df[TARGET_COL].values

    X_val_raw = val_df.drop(columns=[TARGET_COL, "ma_ho_so", "ho_ten"], errors="ignore")
    y_val = val_df[TARGET_COL].values

    # Biến đổi qua preprocessor
    print("Đang biến đổi ma trận đặc trưng qua Preprocessor Pipeline...")
    X_train_prep = preprocessor.transform(X_train_raw)
    X_val_prep = preprocessor.transform(X_val_raw)

    # 2. Định nghĩa các mô hình ứng viên
    models = {
        "Baseline (Logistic Regression)": LogisticRegression(
            max_iter=1000, 
            C=1.0, 
            class_weight="balanced", 
            random_state=random_state
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, 
            max_depth=12, 
            min_samples_split=5, 
            class_weight="balanced", 
            random_state=random_state, 
            n_jobs=-1
        ),
        "XGBoost (Gradient Boosting)": XGBClassifier(
            n_estimators=200, 
            max_depth=5, 
            learning_rate=0.05, 
            subsample=0.85, 
            colsample_bytree=0.85, 
            eval_metric="logloss", 
            random_state=random_state, 
            n_jobs=-1
        )
    }

    # 3. Đánh giá 5-Fold Stratified Cross Validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_results_summary = {}

    scoring = ["roc_auc", "f1", "accuracy", "precision", "recall"]

    print("\n--- KẾT QUẢ 5-FOLD STRATIFIED CROSS-VALIDATION TRÊN TẬP TRAIN ---")
    for name, model in models.items():
        cv_pipeline = Pipeline([("preprocessor", clone(preprocessor)), ("classifier", model)])
        scores = cross_validate(cv_pipeline, X_train_raw, y_train, cv=cv, scoring=scoring, n_jobs=-1)
        mean_auc = scores['test_roc_auc'].mean()
        std_auc = scores['test_roc_auc'].std()
        mean_f1 = scores['test_f1'].mean()
        mean_acc = scores['test_accuracy'].mean()
        mean_prec = scores['test_precision'].mean()
        mean_rec = scores['test_recall'].mean()

        cv_results_summary[name] = {
            "ROC-AUC": f"{mean_auc:.4f} ± {std_auc:.4f}",
            "F1-Score": f"{mean_f1:.4f}",
            "Accuracy": f"{mean_acc:.4f}",
            "Precision": f"{mean_prec:.4f}",
            "Recall": f"{mean_rec:.4f}",
            "raw_mean_auc": mean_auc
        }
        print(f"[{name}]")
        print(f"  ROC-AUC: {mean_auc:.4f} (±{std_auc:.4f}) | F1: {mean_f1:.4f} | Acc: {mean_acc:.4f} | Recall: {mean_rec:.4f}")

    # 4. Tối ưu siêu tham số bằng Optuna cho XGBoost
    print("\n--- BẮT ĐẦU TỐI ƯU SIÊU THAM SỐ (OPTUNA HYPERPARAMETER TUNING) CHO XGBOOST ---")
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 400, step=50),
            "max_depth": trial.suggest_int("max_depth", 3, 9),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.20, log=True),
            "subsample": trial.suggest_float("subsample", 0.65, 0.95),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.60, 0.95),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 8),
            "gamma": trial.suggest_float("gamma", 0.0, 3.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 5.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "eval_metric": "logloss",
            "random_state": random_state,
            "n_jobs": -1
        }
        clf = XGBClassifier(**params)
        cv_pipeline = Pipeline([("preprocessor", clone(preprocessor)), ("classifier", clf)])
        scores = cross_validate(cv_pipeline, X_train_raw, y_train, cv=cv, scoring="roc_auc", n_jobs=-1)
        return float(scores["test_score"].mean())

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=random_state))
    study.optimize(objective, n_trials=30, timeout=180)

    print(f"Tối ưu hoàn thành sau 30 trials.")
    print(f"Tham số tốt nhất (Best Params):")
    for k, v in study.best_params.items():
        print(f"  - {k}: {v}")
    print(f"ROC-AUC CV tốt nhất: {study.best_value:.4f}")

    # 5. Huấn luyện mô hình tối ưu trên toàn bộ tập train
    best_params = study.best_params
    best_params["eval_metric"] = "logloss"
    best_params["random_state"] = random_state
    best_params["n_jobs"] = -1

    best_xgb = XGBClassifier(**best_params)
    best_xgb.fit(X_train_prep, y_train)

    # Đánh giá nhanh trên tập Validation
    val_preds_prob = best_xgb.predict_proba(X_val_prep)[:, 1]
    from sklearn.metrics import roc_auc_score, f1_score, accuracy_score, confusion_matrix
    val_auc = roc_auc_score(y_val, val_preds_prob)
    val_f1 = f1_score(y_val, (val_preds_prob >= 0.5).astype(int))
    val_acc = accuracy_score(y_val, (val_preds_prob >= 0.5).astype(int))
    print(f"\nHiệu năng trên tập Validation độc lập:")
    print(f"  ROC-AUC: {val_auc:.4f} | F1-Score: {val_f1:.4f} | Accuracy: {val_acc:.4f}")

    # 6. Tối ưu hóa Ngưỡng Quyết định theo Ma trận Chi phí trên tập Validation (Chống Threshold Leakage)
    thresholds = np.linspace(0.1, 0.9, 81)
    costs_val = []
    f1_val_list = []
    for t in thresholds:
        preds_t = (val_preds_prob >= t).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val, preds_t).ravel()
        cost = fp * 4.0 + fn * 1.0
        costs_val.append(cost)
        f1_val_list.append(f1_score(y_val, preds_t))

    opt_idx = int(np.argmin(costs_val))
    optimal_threshold = round(float(thresholds[opt_idx]), 3)
    min_cost_val = float(costs_val[opt_idx])
    val_f1_at_opt = float(f1_val_list[opt_idx])

    print(f"\nTối ưu hóa ngưỡng quyết định trên tập Validation (Chi phí: 4*FP + 1*FN):")
    print(f"  Ngưỡng tối ưu: {optimal_threshold} (Cost Val: {min_cost_val}, F1: {val_f1_at_opt:.4f})")

    # Lưu cấu hình ngưỡng vào models/threshold_config.json
    threshold_config = {
        "optimal_threshold": optimal_threshold,
        "default_threshold": 0.50,
        "cost_ratio_fp_to_fn": 4.0,
        "cost_function": "4*FP + 1*FN",
        "val_cost_at_optimal": min_cost_val,
        "val_f1_at_optimal": round(val_f1_at_opt, 4),
        "val_roc_auc": round(float(val_auc), 4),
        "tuned_on": "validation_set",
        "methodology": "Validation Cost-Sensitive Threshold Tuning (Leak-free)"
    }
    threshold_path = os.path.join(models_dir, "threshold_config.json")
    with open(threshold_path, "w", encoding="utf-8") as f:
        json.dump(threshold_config, f, indent=2, ensure_ascii=False)
    print(f"Đã lưu cấu hình ngưỡng tối ưu tại: {threshold_path}")

    # 7. Đóng gói mô hình
    # A. Lưu estimator độc lập
    best_model_path = os.path.join(models_dir, "best_model.joblib")
    joblib.dump(best_xgb, best_model_path)
    print(f"Đã lưu mô hình XGBoost tốt nhất tại: {best_model_path}")

    # B. Lưu end-to-end Pipeline hoàn chỉnh (Preprocessor + Estimator)
    complete_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", best_xgb)
    ])
    pipeline_path = os.path.join(models_dir, "complete_pipeline.joblib")
    joblib.dump(complete_pipeline, pipeline_path)
    print(f"Đã lưu Pipeline End-to-End hoàn chỉnh tại: {pipeline_path}")

    # C. Lưu kết quả CV vào file JSON
    cv_summary_path = os.path.join(models_dir, "cv_results.json")
    with open(cv_summary_path, "w", encoding="utf-8") as f:
        json.dump(cv_results_summary, f, indent=2, ensure_ascii=False)

    return complete_pipeline, cv_results_summary, study.best_params


if __name__ == "__main__":
    train_and_compare_models()
