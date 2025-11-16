from fastapi import FastAPI, Request
import subprocess
import requests
import json

app = FastAPI()

SERVER_UPLOAD_URL = "http://167.172.30.134/api/v1/upload-scraped/"
SECRET_TOKEN = "MY_SECRET_123"


@app.post("/run-scraper")
async def run_scraper(request: Request):
    token = request.headers.get("X-Secret")
    if token != SECRET_TOKEN:
        return {"error": "unauthorized"}

    print("🔔 Trigger received — running scraper...")

    # Run your laptop scraper script
    subprocess.run(["python3", "scraper.py"])

    print("✔ Scraper finished — sending results back...")

    # Load generated results
    with open("output.json", "r") as f:
        data = f.read()

    # Upload to server
    requests.post(
        SERVER_UPLOAD_URL,
        data=data,
        headers={"X-Secret": SECRET_TOKEN}
    )

    print("✔ Upload complete.")
    return {"status": "OK"}
