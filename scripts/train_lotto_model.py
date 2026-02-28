#!/usr/bin/env python3
"""
Train a simple multi-label model to predict next-draw lotto numbers.

Approach:
- Read `lottoai_data.csv` which must contain columns: round, number1..number6, bonusnumber
- Build a binary vector (length 45) per round indicating which numbers appeared.
- For each round t, use the counts of numbers in the previous `WINDOW` rounds as features (length 45).
- Target is the binary vector for round t (which numbers were drawn).
- Train a One-vs-Rest LogisticRegression and save the model.

Usage:
  python scripts/train_lotto_model.py

Outputs:
  models/lotto_model.joblib
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import hamming_loss, accuracy_score
from sklearn.model_selection import train_test_split

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lottoai_data.csv')
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)
WINDOW = 5
NUM_BALLS = 45

def load_data(path=DATA_PATH):
    df = pd.read_csv(path)
    # Expect columns number1..number6 and optional bonusnumber
    # Sort by round if present
    if 'round' in df.columns:
        df = df.sort_values('round')
    df = df.reset_index(drop=True)
    return df

def make_presence(df):
    # returns (n_rounds, NUM_BALLS) binary array
    n = len(df)
    pres = np.zeros((n, NUM_BALLS), dtype=int)
    for i, row in df.iterrows():
        nums = [int(row.get(f'number{j}')) for j in range(1,7)]
        for v in nums:
            if 1 <= v <= NUM_BALLS:
                pres[i, v-1] = 1
    return pres

def build_features_targets(pres, window=WINDOW):
    X, Y = [], []
    for i in range(window, len(pres)):
        prev = pres[i-window:i]  # shape (window, NUM_BALLS)
        # flatten the windowed one-hot rows into a single vector
        feat = prev.flatten()  # length = window * NUM_BALLS
        X.append(feat)
        Y.append(pres[i])
    return np.array(X, dtype=int), np.array(Y, dtype=int)

def train():
    print('Loading data...')
    df = load_data()
    pres = make_presence(df)
    X, Y = build_features_targets(pres)
    print('Data shapes:', X.shape, Y.shape)

    # train/test split (time-based)
    split = int(len(X)*0.8)
    X_train, X_test = X[:split], X[split:]
    Y_train, Y_test = Y[:split], Y[split:]

    print('Training One-vs-Rest LogisticRegression...')
    base = LogisticRegression(max_iter=1000)
    clf = OneVsRestClassifier(base)
    clf.fit(X_train, Y_train)

    print('Evaluating...')
    preds = clf.predict(X_test)
    print('Hamming loss:', hamming_loss(Y_test, preds))
    # exact match accuracy (rare for lotto)
    print('Exact match accuracy:', accuracy_score(Y_test, preds))

    model_path = os.path.join(MODEL_DIR, 'lotto_model.joblib')
    joblib.dump({'model': clf, 'window': WINDOW}, model_path)
    print('Saved model to', model_path)

if __name__ == '__main__':
    train()
