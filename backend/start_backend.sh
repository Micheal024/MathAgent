#!/bin/bash
# Script to install dependencies and start backend
cd /Users/micheal024/code/math/backend

echo "⏳ Checking dependencies..."
python3 -m pip install -r requirements.txt

echo "🚀 Starting Backend Server..."
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
