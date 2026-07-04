from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {
        "application": "GEST SPORT WEB",
        "status": "OK"
    }