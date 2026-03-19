@echo off
:: Проверка и запуск от админа если нужно
cd /d "%~dp0"

:: Добавляем FFmpeg в PATH
set PATH=%PATH%;C:\Users\Anton\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin

:: Проверяем наличие виртуального окружения
if exist "%~dp0venv\Scripts\pythonw.exe" (
    set PYTHON_EXE="%~dp0venv\Scripts\pythonw.exe"
) else if exist "%~dp0.venv\Scripts\pythonw.exe" (
    set PYTHON_EXE="%~dp0.venv\Scripts\pythonw.exe"
) else (
    set PYTHON_EXE=pythonw.exe
)

:: Проверяем, запущен ли от админа
net session >nul 2>&1
if %errorLevel% neq 0 (
    :: Не админ - перезапускаем от админа скрыто
    powershell -WindowStyle Hidden -Command "Start-Process powershell -ArgumentList '-WindowStyle Hidden -Command \"cd \\\"%cd%\\\"; Start-Process %PYTHON_EXE% -ArgumentList \\\"main.py\\\" -WindowStyle Hidden' -Verb RunAs"
    exit /b
)

:: Запуск от админа - запускаем бота скрыто
start /b "" %PYTHON_EXE% "%~dp0main.py"
