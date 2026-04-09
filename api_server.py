from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/api/historical_daily_data")
def get_data():
    file_path = os.path.join(os.path.dirname(__file__), "data.parquet")
    df = pd.read_parquet(file_path)
    return df.to_dict(orient="records")