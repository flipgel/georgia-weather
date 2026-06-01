#!/bin/bash
# Georgia Weather Consensus — One-click run script for Linux/Mac

cd "$(dirname "$0")"

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "🔧 First run: creating Python virtual environment..."
    python3 -m venv venv
    venv/bin/pip install -q requests
fi

source venv/bin/activate

echo "📡 Step 1/3 — Collecting fresh forecasts..."
python collect.py

echo ""
echo "🧮 Step 2/3 — Updating accuracy scores (may say '0 days' until archive catches up)..."
python verify.py

echo ""
echo "📊 Step 3/3 — Building dashboard..."
python report.py

echo ""
echo "✅ All done! Open dashboard.html or index.html in your browser."
