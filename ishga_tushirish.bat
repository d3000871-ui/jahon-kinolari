@echo off
chcp 65001 > nul
title Jahon Kinolari - Server
echo ========================================================
echo        🎬 JAHON KINOLARI VEB SAYTI ISHGA TUSHMOQDA
echo ========================================================
echo.
echo Server manzili: http://127.0.0.1:5000
echo Brauzer avtomatik ochilmoqda...
echo.

start "" "http://127.0.0.1:5000"

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app.py
) else (
    python app.py
)

pause

