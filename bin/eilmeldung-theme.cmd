@echo off
setlocal
for %%a in (%*) do (
    if /i "%%~a"=="-c" goto run
    if /i "%%~a"=="--config-dir" goto run
)
echo "%*" | findstr /i /c:"--config-dir=" >nul && goto run
for /f "usebackq delims=" %%p in (`terminal-theme-switch eilmeldung 2^>nul`) do set "CONFIG=%%p"
if not defined CONFIG goto run
eilmeldung.exe -c "%CONFIG%" %*
exit /b %ERRORLEVEL%
:run
eilmeldung.exe %*
