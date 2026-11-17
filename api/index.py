"""Vercel Serverless Function entrypoint for RR EDGE FastAPI application."""
import sys
from pathlib import Path

# Ensure project root is in sys.path so 'src' can be resolved by Vercel Lambda runtime
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api.main import app
