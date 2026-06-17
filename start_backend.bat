@echo off
chcp 65001 >nul
echo 🚀 正在启动后端服务器...
cd backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python run.py
pause
