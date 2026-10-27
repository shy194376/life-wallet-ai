@echo off
chcp 65001 >nul
setlocal EnableExtensions
title 全场景生活消费决策智能体 - 网页服务
cd /d "%~dp0"

echo ============================================================
echo   全场景生活消费决策智能体 - 网页服务
echo ============================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未检测到虚拟环境，请先双击运行 setup.bat。
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [提示] 未检测到 .env 配置文件，将使用本地演示模式启动。
    echo 如需连接真实大模型，请先运行 setup.bat 并填写 OPENAI_API_KEY。
    echo.
)

call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败，请重新运行 setup.bat。
    echo.
    pause
    exit /b 1
)

set "LAN_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do set "LAN_IP=%%a"
set "LAN_IP=%LAN_IP: =%"

echo 正在启动网页服务...
echo 本机访问：http://127.0.0.1:5000
if defined LAN_IP echo 局域网分享：http://%LAN_IP%:5000
echo 公网分享：完成云端部署后使用平台生成的 HTTPS 地址
echo 健康检查：http://127.0.0.1:5000/health
echo 按 Ctrl + C 可停止服务。
echo.

python app.py

echo.
echo ============================================================
echo 后端服务已退出，请查看上方错误信息（如有）。
echo ============================================================
pause
endlocal