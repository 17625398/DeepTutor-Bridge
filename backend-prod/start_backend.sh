#!/bin/bash
echo "Starting DeepTutor Backend ..."
echo ""
echo "Skipping dependency installation (no packages included)."
echo "Starting backend server ..."
python -m uvicorn deeptutor.api.main:app --host 0.0.0.0 --port 8001 --log-level info
