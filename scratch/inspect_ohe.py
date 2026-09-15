import joblib, sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
from src.preprocessing import VietnameseCreditFeatureExtractor, Winsorizer

prep = joblib.load('models/preprocessor.joblib')
print('Steps in preprocessor:', list(prep.named_steps.keys()))
ct = prep.named_steps['col_transformer']
for tname, trans, cols in ct.transformers_:
    print(f"\n--- Transformer: {tname} (Cols: {cols}) ---")
    if hasattr(trans, 'categories_'):
        for c, cats in zip(cols, trans.categories_):
            print(f"  Field: '{c}'")
            print(f"  Trained OHE values ({len(cats)}): {list(cats)}")
