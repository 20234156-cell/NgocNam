"""
Unit Tests for Model Artifacts and Pipeline Structure (tests/test_model.py).
Kiểm tra cấu trúc complete_pipeline.joblib, best_model.joblib và threshold_config.json.
"""

import os
import json
import joblib
import pytest
from sklearn.pipeline import Pipeline
from src.preprocessing import VietnameseCreditFeatureExtractor, Winsorizer


def test_complete_pipeline_structure():
    """Kiểm tra pipeline hoàn chỉnh chứa đủ 2 bước: preprocessor và classifier."""
    pipeline_path = os.path.join("models", "complete_pipeline.joblib")
    assert os.path.exists(pipeline_path), "complete_pipeline.joblib không tồn tại!"
    
    pipeline = joblib.load(pipeline_path)
    assert isinstance(pipeline, Pipeline)
    assert "preprocessor" in pipeline.named_steps
    assert "classifier" in pipeline.named_steps
    
    # Kiểm tra classifier có hàm predict_proba
    classifier = pipeline.named_steps["classifier"]
    assert hasattr(classifier, "predict_proba")


def test_threshold_config_validity():
    """Kiểm tra tính hợp lệ của file cấu hình ngưỡng tối ưu."""
    config_path = os.path.join("models", "threshold_config.json")
    assert os.path.exists(config_path), "threshold_config.json không tồn tại!"
    
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    assert "optimal_threshold" in cfg
    assert "default_threshold" in cfg
    
    opt_thresh = float(cfg["optimal_threshold"])
    assert 0.10 <= opt_thresh <= 0.90, f"Ngưỡng tối ưu bất thường: {opt_thresh}"
    assert cfg["default_threshold"] == 0.50


def test_feature_metadata_validity():
    """Kiểm tra metadata đặc trưng."""
    meta_path = os.path.join("models", "feature_metadata.joblib")
    assert os.path.exists(meta_path), "feature_metadata.joblib không tồn tại!"
    
    meta = joblib.load(meta_path)
    assert "all_feature_names" in meta
    assert len(meta["all_feature_names"]) > 20
