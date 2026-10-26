# Starts the whole Adaptive RAG stack, each service in its own window.
# MongoDB must already be running (it is installed as a Windows service here).
$root = $PSScriptRoot
$rag = Join-Path $root "rag-service"
$bff = Join-Path $root "auth-gateway"

# 1. Python RAG API on :8000
Start-Process pwsh -WorkingDirectory $rag -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\python.exe -m uvicorn src.main:app --port 8000"

# 2. NestJS BFF (login/signup) on :8080
Start-Process pwsh -WorkingDirectory $bff -ArgumentList "-NoExit", "-Command", "npm run start:prod"

# 3. Streamlit UI on :8501 (run from project root so both import styles resolve)
Start-Process pwsh -WorkingDirectory $rag -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\python.exe -m streamlit run streamlit_app/home.py"

Write-Host "Starting... open http://localhost:8501 in a few seconds."
