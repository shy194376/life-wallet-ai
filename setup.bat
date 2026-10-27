@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   全场景生活消费决策智能体 - 环境初始化
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    where py >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未检测到 Python，请先安装 Python 3.9 或更高版本。
        echo 下载地址：https://www.python.org/downloads/
        echo 安装时请勾选 Add Python to PATH。
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)

echo [1/5] 正在检查 Python 版本...
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 (
    echo [错误] 当前 Python 版本低于 3.9，请升级后重试。
    pause
    exit /b 1
)
echo Python 检查通过。
echo.

echo [2/5] 正在创建 Python 虚拟环境 venv...
if not exist "venv\Scripts\python.exe" (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败，请检查 Python 安装是否完整。
        pause
        exit /b 1
    )
) else (
    echo 已检测到 venv，跳过创建。
)

echo.
echo [3/5] 正在激活虚拟环境并升级 pip...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败。
    pause
    exit /b 1
)

python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [提示] 清华镜像升级 pip 失败，尝试使用默认源...
    python -m pip install --upgrade pip
    if errorlevel 1 (
        echo [错误] pip 升级失败，请检查网络连接。
        pause
        exit /b 1
    )
)

echo.
echo [4/5] 正在使用清华镜像安装 requirements.txt...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [提示] 清华镜像安装失败，尝试使用默认源...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接或 requirements.txt。
        pause
        exit /b 1
    )
)

echo.
echo [5/5] 正在检查 .env 配置文件...
if not exist ".env" (
    copy /Y ".env.example" ".env" >nul
    if errorlevel 1 (
        echo [错误] 无法创建 .env 文件。
        pause
        exit /b 1
    )
    echo 已根据 .env.example 创建 .env。
    echo 即将打开记事本，请填写 OPENAI_API_KEY 后保存并关闭记事本。
    start "" notepad ".env"
) else (
    echo 已检测到 .env，跳过复制。
)

echo.
echo ============================================================
echo   环境初始化完成
echo ============================================================
echo 请确认 .env 中已经填写自己的 OPENAI_API_KEY。
echo 然后双击运行 start.bat 启动后端服务。
echo 后端启动后，再双击打开 index.html 即可使用。
echo ============================================================
echo.
pause
endlocal