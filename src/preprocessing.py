"""
Data Preprocessing Pipeline for Vietnamese Loan Approval System.
Module tiền xử lý dữ liệu:
1. Trích xuất đặc trưng tài chính nghiệp vụ (Feature Engineering).
2. Xử lý giá trị khuyết thiếu (Imputation).
3. Xử lý giá trị ngoại lai (Winsorization Capping 1% - 99%).
4. Chuẩn hóa One-Hot Encoding cho biến phân loại.
5. Scale biến số với RobustScaler (kháng ngoại lai).
6. Phân chia Train / Validation / Test (70 / 15 / 15) Stratified.
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd

# Đảm bảo root directory có trong sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.model_selection import train_test_split

from src.feature_engineering import add_engineered_features

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


# Danh mục cột đặc trưng
NUMERICAL_COLS = [
    "tuoi", "so_nguoi_phu_thuoc", "thu_nhap_thang_vnd", "thu_nhap_nguoi_dong_vay_vnd",
    "tong_thu_nhap_thang_vnd", "gia_tri_tai_san_dam_bao_vnd", "so_tien_vay_vnd",
    "thoi_han_vay_thang", "diem_tin_dung_cic", "so_lan_tre_han_2_nam",
    "so_khoan_vay_hien_tai", "ty_le_dti", "ty_le_vay_tren_thu_nhap_nam",
    "ty_le_vay_tren_tai_san_ltv", "ty_le_tra_gop_tren_thu_nhap", "chi_so_ap_luc_tai_chinh"
]

CATEGORICAL_COLS = [
    "gioi_tinh", "tinh_trang_hon_nhan", "trinh_do_hoc_van", "loai_hinh_nghe_nghiep",
    "muc_dich_vay", "khu_vuc_sinh_song", "nhom_no_cic", "lich_su_no_xau",
    "nhom_diem_cic", "nhom_tuoi"
]

TARGET_COL = "phe_duyet_khoan_vay"


class Winsorizer(BaseEstimator, TransformerMixin):
    """Giới hạn giá trị ngoại lai trong khoảng phân vị [lower_quantile, upper_quantile]."""
    def __init__(self, lower_quantile: float = 0.01, upper_quantile: float = 0.99):
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}

    def fit(self, X, y=None):
        if isinstance(X, pd.DataFrame):
            for col in X.columns:
                self.lower_bounds_[col] = X[col].quantile(self.lower_quantile)
                self.upper_bounds_[col] = X[col].quantile(self.upper_quantile)
        else:
            X_arr = np.asarray(X)
            self.lower_bounds_ = np.nanpercentile(X_arr, self.lower_quantile * 100, axis=0)
            self.upper_bounds_ = np.nanpercentile(X_arr, self.upper_quantile * 100, axis=0)
        return self

    def transform(self, X):
        X_out = X.copy()
        if isinstance(X_out, pd.DataFrame):
            for col in X_out.columns:
                if col in self.lower_bounds_:
                    X_out[col] = np.clip(X_out[col], self.lower_bounds_[col], self.upper_bounds_[col])
            return X_out
        else:
            return np.clip(X_out, self.lower_bounds_, self.upper_bounds_)


class VietnameseCreditFeatureExtractor(BaseEstimator, TransformerMixin):
    """Transformer tự động thêm đặc trưng phái sinh từ dữ liệu thô."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input to VietnameseCreditFeatureExtractor must be a pandas DataFrame.")
        return add_engineered_features(X)


def build_preprocessing_pipeline() -> Pipeline:
    """
    Khởi tạo Pipeline tiền xử lý hoàn chỉnh tương thích Scikit-Learn.
    """
    # Pipeline cho biến số
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("winsorizer", Winsorizer(lower_quantile=0.01, upper_quantile=0.99)),
        ("scaler", RobustScaler())
    ])

    # Pipeline cho biến phân loại
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    # ColumnTransformer kết hợp
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, NUMERICAL_COLS),
            ("cat", cat_pipeline, CATEGORICAL_COLS)
        ],
        remainder="drop"
    )

    full_pipeline = Pipeline([
        ("feature_engineering", VietnameseCreditFeatureExtractor()),
        ("col_transformer", preprocessor)
    ])

    return full_pipeline


def prepare_data_and_save(
    raw_data_path: str = "data/raw/loan_data.csv",
    output_dir: str = "data/processed",
    models_dir: str = "models",
    random_state: int = 42
):
    """
    Đọc dữ liệu thô, phân chia train/val/test và fit preprocessor.
    Lưu dữ liệu và preprocessor.joblib.
    """
    from src.integrity import require_experiment_directory
    require_experiment_directory(output_dir)
    require_experiment_directory(models_dir)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    print(f"Đọc dữ liệu từ: {raw_data_path}")
    df_raw = pd.read_csv(raw_data_path, encoding="utf-8-sig")

    y = df_raw[TARGET_COL].values

    # Phân chia 70% Train, 15% Validation, 15% Test (Stratified)
    train_df, temp_df, y_train, y_temp = train_test_split(
        df_raw, y, test_size=0.30, random_state=random_state, stratify=y
    )
    val_df, test_df, y_val, y_test = train_test_split(
        temp_df, y_temp, test_size=0.50, random_state=random_state, stratify=y_temp
    )

    print(f"Kích thước tập dữ liệu:")
    print(f"- Tập huấn luyện (Train): {train_df.shape[0]} mẫu ({train_df.shape[0]/len(df_raw):.1%}) - Tỷ lệ duyệt: {y_train.mean():.2%}")
    print(f"- Tập kiểm định (Val):   {val_df.shape[0]} mẫu ({val_df.shape[0]/len(df_raw):.1%}) - Tỷ lệ duyệt: {y_val.mean():.2%}")
    print(f"- Tập kiểm thử (Test):    {test_df.shape[0]} mẫu ({test_df.shape[0]/len(df_raw):.1%}) - Tỷ lệ duyệt: {y_test.mean():.2%}")

    # Xây dựng và fit pipeline tiền xử lý trên tập train
    pipeline = build_preprocessing_pipeline()
    pipeline.fit(train_df)

    # Lưu preprocessor pipeline
    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    joblib.dump(pipeline, preprocessor_path)
    print(f"Đã lưu pipeline tiền xử lý tại: {preprocessor_path}")

    # Lưu các tập dữ liệu
    train_df.to_csv(os.path.join(output_dir, "train.csv"), index=False, encoding="utf-8-sig")
    val_df.to_csv(os.path.join(output_dir, "val.csv"), index=False, encoding="utf-8-sig")
    test_df.to_csv(os.path.join(output_dir, "test.csv"), index=False, encoding="utf-8-sig")
    print(f"Đã lưu các tập train.csv, val.csv, test.csv vào thư mục: {output_dir}")

    # Lấy danh sách tên cột sau khi One-Hot Encoding
    ohe = pipeline.named_steps["col_transformer"].named_transformers_["cat"].named_steps["onehot"]
    cat_feature_names = list(ohe.get_feature_names_out(CATEGORICAL_COLS))
    all_feature_names = NUMERICAL_COLS + cat_feature_names
    
    # Lưu metadata danh sách feature names để phục vụ SHAP và giải thích mô hình
    metadata = {
        "numerical_cols": NUMERICAL_COLS,
        "categorical_cols": CATEGORICAL_COLS,
        "all_feature_names": all_feature_names,
        "n_features": len(all_feature_names)
    }
    joblib.dump(metadata, os.path.join(models_dir, "feature_metadata.joblib"))
    print(f"Tổng số đặc trưng sau biến đổi One-Hot: {len(all_feature_names)} features.")

    return pipeline, metadata


if __name__ == "__main__":
    prepare_data_and_save()
