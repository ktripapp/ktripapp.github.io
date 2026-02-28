#!/usr/bin/env python3
"""
Load saved model and predict next-round numbers given recent rounds from `lottoai_data.csv`.

Usage:
  python scripts/predict_lotto.py --topk 6

This script prints top-k numbers by predicted probability.
"""
import os
import argparse
import joblib
import json
import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'lotto_model.joblib')
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lottoai_data.csv')

def load_model(path=MODEL_PATH):
    obj = joblib.load(path)
    return obj['model'], obj.get('window', 5)

def load_recent_features(df, window):
    # make presence and aggregate last `window` rounds
    nums = []
    for i, row in df.iterrows():
        nums.append([int(row.get(f'number{j}')) for j in range(1,7)])
    pres = np.zeros((len(nums),45), dtype=int)
    for i, ns in enumerate(nums):
        for v in ns:
            if 1 <= v <= 45:
                pres[i, v-1] = 1
    last = pres[-window:]
    # flatten the windowed one-hot rows to match training (WINDOW x 45 -> flattened)
    feat = last.flatten().reshape(1, -1)
    return feat

def main(topk=6):
    model, window = load_model()
    df = pd.read_csv(DATA_PATH).sort_values('round') if 'round' in pd.read_csv(DATA_PATH).columns else pd.read_csv(DATA_PATH)
    df = df.reset_index(drop=True)
    X_feat = load_recent_features(df, window)
    probs = model.predict_proba(X_feat)
    # OneVsRestClassifier may return a 2D array (n_samples, n_labels)
    if isinstance(probs, list):
        # stack list-of-arrays into (n_samples, n_labels)
        probs = np.vstack([p for p in probs]).T
    probs = np.asarray(probs).ravel()
    top_idx = np.argsort(probs)[-topk:][::-1]
    print('Top-{} predicted numbers:'.format(topk))
    for i in top_idx:
        print(i+1, '(p={:.6f})'.format(probs[i]))

    # also write to models/last_prediction.json for frontend
    out = {'probs': [float(x) for x in probs.tolist()]}
    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'last_prediction.json')
    with open(out_path, 'w', encoding='utf8') as f:
        json.dump(out, f, ensure_ascii=False)
    print('Wrote probabilities to', out_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--topk', type=int, default=6)
    args = parser.parse_args()
    main(args.topk)
