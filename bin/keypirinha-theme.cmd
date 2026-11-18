@echo off
setlocal
terminal-theme-switch keypirinha >nul 2>nul
tasklist | findstr /i "keypirinha" >nul && exit /b 0
keypirinha.exe %*
