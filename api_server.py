from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/api/historical_daily_data")
def get_data():
    return {"message": "API working"}
