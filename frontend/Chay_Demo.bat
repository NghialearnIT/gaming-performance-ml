@echo off
chcp 65001 >nul
where py >nul 2>nul
if errorlevel 1 (
  python "%~dp0run_demo.py"
) else (
  py -3 "%~dp0run_demo.py"
)
if errorlevel 1 pause
