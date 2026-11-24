@echo off
title VisualSQL Server
cd /d "%~dp0VisualSQL"
echo ============================================================
echo Starting VisualSQL Server...
echo URL: http://127.0.0.1:5000
echo Press Ctrl+C in this window to stop the server.
echo ============================================================
"C:\Users\bhuvaneswari\AppData\Local\Programs\Python\Python313\python.exe" app.py
pause
