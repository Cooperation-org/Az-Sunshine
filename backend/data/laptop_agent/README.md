# SOI Laptop Scraper Agent

This agent runs on your laptop and receives scrape requests from the Az-Sunshine server via SSH tunnel. It uses your laptop's residential IP to bypass Cloudflare protection on the Arizona SOI pages.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SERVER (167.172.30.134)                                        │
│  ┌─────────────────┐     ┌──────────────────────┐              │
│  │ Django Web UI   │────▶│ Call localhost:5001  │              │
│  │ /soi page       │     │ (via SSH tunnel)     │              │
│  └─────────────────┘     └──────────┬───────────┘              │
└─────────────────────────────────────│───────────────────────────┘
                                      │
                    SSH Reverse Tunnel│
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  YOUR LAPTOP                                                    │
│  ┌─────────────────┐     ┌──────────────────────┐              │
│  │ FastAPI Agent   │────▶│ Playwright + Chrome  │              │
│  │ port 5001       │     │ (residential IP)     │              │
│  └─────────────────┘     └──────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Setup (5 minutes)

### Step 1: Download Files to Your Laptop

Copy these files to a folder on your laptop:
- `soi_laptop_agent.py`
- `requirements.txt`

Or clone just this folder:
```bash
mkdir soi_agent && cd soi_agent
curl -O http://167.172.30.134/static/laptop_agent/soi_laptop_agent.py
curl -O http://167.172.30.134/static/laptop_agent/requirements.txt
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 3: Set Up SSH Tunnel

Open a terminal and run:
```bash
ssh -R 5001:localhost:5001 root@167.172.30.134
```

This creates a reverse tunnel so the server can reach your laptop's port 5001.

**Keep this terminal open!** The tunnel stays active as long as this SSH session is running.

### Step 4: Start the Agent

In a new terminal:
```bash
source venv/bin/activate  # If using venv
python soi_laptop_agent.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════════════╗
║                  SOI LAPTOP SCRAPER AGENT                         ║
╚═══════════════════════════════════════════════════════════════════╝
INFO:     Uvicorn running on http://0.0.0.0:5001
```

### Step 5: Test from Server

Go to: http://167.172.30.134/soi

Click "Run Scraper" - it should work now!

Or test the API directly:
```bash
# On the server
curl http://localhost:5001/health
```

## Keeping Tunnel Alive (Optional)

To auto-reconnect the SSH tunnel, use `autossh`:

### On Mac:
```bash
brew install autossh
autossh -M 0 -f -N -R 5001:localhost:5001 root@167.172.30.134
```

### On Linux:
```bash
sudo apt install autossh
autossh -M 0 -f -N -R 5001:localhost:5001 root@167.172.30.134
```

### On Windows:
Use PuTTY with "Keep-alives" enabled, or install Windows Subsystem for Linux (WSL).

## Troubleshooting

### "Cannot connect to laptop agent"
- Check if the SSH tunnel is running
- Check if the agent is running on port 5001
- Try: `curl http://localhost:5001/health` on your laptop

### "Cloudflare blocked"
- The agent runs Chrome in visible mode to bypass Cloudflare
- Make sure you can see the Chrome window when it scrapes
- If still blocked, you may need to solve a CAPTCHA manually the first time

### "Playwright not found"
```bash
pip install playwright
playwright install chromium
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/scrape` | POST | Trigger scrape (called by server) |
| `/` | GET | Agent info |

## Files

- `soi_laptop_agent.py` - Main agent script
- `requirements.txt` - Python dependencies
- `README.md` - This file
