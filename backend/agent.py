from fastapi import FastAPI, Request, HTTPException
import subprocess
import requests
import json
import os
import csv
from pathlib import Path
from datetime import datetime

app = FastAPI()

# Configuration - UPDATE THESE VALUES
SERVER_UPLOAD_URL = "http://167.172.30.134/api/v1/upload-scraped/"
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "MY_SECRET_123")

# Paths - assuming agent.py is in backend directory
BASE_DIR = Path(__file__).parent
MANAGE_PY = BASE_DIR / "manage.py"
CSV_OUTPUT = BASE_DIR / "data" / "soi_candidates.csv"
VENV_PYTHON = BASE_DIR.parent / "venv" / "bin" / "python3"  # Adjust if needed


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "SOI Scraper Agent",
        "manage_py_exists": MANAGE_PY.exists(),
        "python_path": str(VENV_PYTHON),
        "csv_output_dir": str(CSV_OUTPUT.parent)
    }


@app.post("/run-scraper")
async def run_scraper(request: Request):
    """
    Endpoint that Django server calls to trigger scraping.
    This runs on your HOME LAPTOP with residential IP.
    
    Runs Django management command: python manage.py soi_scraper
    """
    # Security check
    token = request.headers.get("X-Secret")
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    print("\n" + "="*70)
    print("🔔 Server triggered the scraper...")
    print("="*70)
    
    try:
        # Check if manage.py exists
        if not MANAGE_PY.exists():
            return {
                "status": "error",
                "message": f"manage.py not found at {MANAGE_PY}"
            }

        # Ensure CSV output directory exists
        CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine which Python to use
        if VENV_PYTHON.exists():
            python_cmd = str(VENV_PYTHON)
            print(f"✓ Using venv Python: {python_cmd}")
        else:
            python_cmd = "python3"
            print(f"✓ Using system Python: {python_cmd}")

        # Run the Django management command
        print(f"▶️  Running: {python_cmd} manage.py soi_scraper")
        print(f"📍 Working directory: {BASE_DIR}")
        print(f"📂 CSV output: {CSV_OUTPUT}")
        print("-"*70)
        
        result = subprocess.run(
            [python_cmd, "manage.py", "soi_scraper", 
             "--csv-output", str(CSV_OUTPUT)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for scraping
        )
        
        print("\n" + "-"*70)
        print("📋 Scraper Output:")
        print("-"*70)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  Scraper Errors/Warnings:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"\n❌ Scraper failed with exit code {result.returncode}")
            return {
                "status": "error",
                "message": "Scraper execution failed",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        print("\n✔️  Scraper finished successfully")

        # Check if CSV file was created
        if not CSV_OUTPUT.exists():
            return {
                "status": "error",
                "message": f"CSV output file not found at {CSV_OUTPUT}"
            }

        # Read CSV and convert to JSON for upload
        print(f"\n📤 Loading CSV data from {CSV_OUTPUT}...")
        candidates = []
        
        with open(CSV_OUTPUT, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates.append({
                    'name': row.get('name', ''),
                    'office': row.get('office', ''),
                    'party': row.get('party', ''),
                    'phone': row.get('phone', ''),
                    'email': row.get('email', ''),
                    'filing_date': datetime.now().date().isoformat(),
                    'source_url': row.get('source_url', '')
                })
        
        print(f"✓ Loaded {len(candidates)} candidates from CSV")

        # Send data back to Django server
        print(f"\n📡 Sending data to server: {SERVER_UPLOAD_URL}")
        response = requests.post(
            SERVER_UPLOAD_URL,
            json=candidates,  # Send as JSON
            headers={
                "X-Secret": SECRET_TOKEN,
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        response.raise_for_status()
        server_response = response.json()
        
        print("✅ Data uploaded successfully!")
        print(f"📊 Server response: {json.dumps(server_response, indent=2)}")
        
        print("\n" + "="*70)
        print("🎉 SCRAPING COMPLETE!")
        print("="*70)
        
        return {
            "status": "success",
            "message": "Scraping completed and data sent to server",
            "stats": {
                "candidates_scraped": len(candidates),
                "csv_path": str(CSV_OUTPUT),
                "server_response": server_response
            },
            "scraper_output": result.stdout
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Scraper timeout (exceeded 10 minutes)"
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "message": f"File not found: {str(e)}"
        }
    except csv.Error as e:
        return {
            "status": "error",
            "message": f"CSV parsing error: {str(e)}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to upload to server: {str(e)}"
        }
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 Starting FastAPI SOI Scraper Agent")
    print("="*70)
    print(f"📍 Base directory: {BASE_DIR}")
    print(f"📍 manage.py: {MANAGE_PY}")
    print(f"📍 Python: {VENV_PYTHON if VENV_PYTHON.exists() else 'python3 (system)'}")
    print(f"📍 CSV output: {CSV_OUTPUT}")
    print(f"🔐 Secret token configured: {bool(SECRET_TOKEN)}")
    print(f"📤 Upload URL: {SERVER_UPLOAD_URL}")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5001)