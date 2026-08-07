#!/bin/bash
# Script to start the backend with correct PYTHONPATH

cd /home/server-gea/Documentos/vehicle-detection-system/backend
export PYTHONPATH="/home/server-gea/Documentos/vehicle-detection-system/backend:$PYTHONPATH"
echo "PYTHONPATH=$PYTHONPATH" >> backend.log
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 "$@" >> backend.log 2>&1
