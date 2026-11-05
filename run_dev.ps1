# Run ShiftSathi dev servers
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\backend'; python -m uvicorn app.main:app --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\frontend'; npm run dev"
Write-Host "Started backend (8000) and frontend (5173)"