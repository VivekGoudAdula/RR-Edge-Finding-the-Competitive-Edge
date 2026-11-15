"""Launch script for RR EDGE Cricket Intelligence Platform."""

import sys
import uvicorn
import webbrowser
import threading
import time

def open_browser():
    """Wait for server to start, then open dashboard in default browser."""
    time.sleep(1.2)
    webbrowser.open("http://localhost:8000")

def main():
    """Start uvicorn server on port 8000."""
    print("=" * 70)
    print("  RR EDGE — Explainable Multi-Model Cricket Intelligence System")
    print("  Rajasthan Royals SupeRR Selector Platform")
    print("  Starting unified platform on http://localhost:8000 ...")
    print("=" * 70)
    
    # Auto-open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()

