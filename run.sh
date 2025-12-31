#!/bin/bash
# Finarius - Run script
# Activates virtual environment and starts Streamlit app

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo "📦 Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Set PYTHONPATH to include project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run Streamlit app
echo "🚀 Starting Finarius..."
echo "📍 App will be available at http://localhost:8501"
echo ""
streamlit run finarius_app/app.py

