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
    echo [提示] 未检测到 .env 配置文件，DeepSeek 将处于未就绪状态。
    echo 请先运行 setup.bat 并填写 DEEPSEEK_API_KEY，再重新启动服务。
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
echo DeepSeek 就绪检查：http://127.0.0.1:5000/ready
echo DeepSeek 将自动连接并心跳保活，无需手动操作。
echo 按 Ctrl + C 可停止服务。
echo.

:run_service
python app.py
set "EXIT_CODE=%ERRORLEVEL%"

if "%EXIT_CODE%"=="0" goto service_stopped

echo.
echo [警告] 后端异常退出（代码 %EXIT_CODE%），5 秒后自动重启。
echo 按 Ctrl + C 可停止自动重启。
echo.
timeout /t 5 /nobreak >nul
goto run_service

:service_stopped
echo.
echo ============================================================
echo 后端服务已正常退出。
echo ============================================================
pause
endlocal