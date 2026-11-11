@echo off
chcp 65001 > nul
title Jahon Kinolari - Server
start "" "http://127.0.0.1:5000"
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app.py
) else (
    python app.py
)
pause

