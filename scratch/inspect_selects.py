import re
import sys
import os
import joblib

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

print("\n--- FIELD_CONSTRAINTS IN SRC/DECISION.PY ---")
from src.decision import FIELD_CONSTRAINTS
for col, vals in FIELD_CONSTRAINTS.items():
    print(f"{col}: {vals}")

print("\n--- PREPROCESSOR ONE-HOT ENCODER CATEGORIES ---")
prep = joblib.load('models/preprocessor.joblib')
col_tx = prep.named_transformers_
ohe = col_tx.get('cat')
if ohe is None:
    print("Transformers available:", col_tx.keys())
    for name, trans, cols in prep.transformers_:
        print(f"Transformer: {name}, type: {type(trans)}, cols: {cols}")
        if hasattr(trans, 'categories_'):
            for c, cats in zip(cols, trans.categories_):
                print(f"  Col '{c}': {list(cats)}")
