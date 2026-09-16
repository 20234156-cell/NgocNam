@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "SERVER_PYTHON="
if exist ".venv\Scripts\python.exe" set SERVER_PYTHON="%~dp0.venv\Scripts\python.exe"
if defined SERVER_PYTHON goto start_server
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set SERVER_PYTHON="%LocalAppData%\Programs\Python\Python313\python.exe"
if defined SERVER_PYTHON goto start_server
py -3.13 --version >nul 2>&1
if not errorlevel 1 set "SERVER_PYTHON=py -3.13"
if defined SERVER_PYTHON goto start_server
python --version >nul 2>&1
if not errorlevel 1 set "SERVER_PYTHON=python"
if defined SERVER_PYTHON goto start_server
echo Python was not found. Install Python 3.13 and enable Add Python to PATH.
pause
exit /b 1

:start_server
set "PORT=8001"
echo ====================================================================
echo  VIETCREDIT SERVER DANG KHOI DONG:
echo  Link truy cap: http://127.0.0.1:8001/cockpit
echo ====================================================================
start "" "http://127.0.0.1:8001/cockpit"
%SERVER_PYTHON% -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --no-server-header
set "SERVER_EXIT=%ERRORLEVEL%"
pause
exit /b %SERVER_EXIT%


