@echo off
setlocal
if /i "%~1"=="migrate" (
    alacritty.exe %*
    exit /b %ERRORLEVEL%
)
if /i "%~1"=="help" (
    alacritty.exe %*
    exit /b %ERRORLEVEL%
)
if "%~1"=="-h" goto :cli
if "%~1"=="--help" goto :cli
if "%~1"=="-V" goto :cli
if "%~1"=="--version" goto :cli
goto :launch

:cli
alacritty.exe %*
exit /b %ERRORLEVEL%

:launch
if not defined USERHOME set "USERHOME=%USERPROFILE%"
set "CONFIG=%USERHOME%\Share\dotfiles\.config\alacritty\alacritty.toml"

if not exist "%CONFIG%" (
    echo alacritty.cmd: missing %CONFIG% >&2
    exit /b 1
)
for /f "usebackq delims=" %%I in (`call terminal-theme-switch alacritty`) do set "ALACRITTY_THEME=%%I"
if not defined ALACRITTY_THEME (
    echo alacritty.cmd: terminal-theme-switch returned no theme path >&2
    exit /b 1
)
set "ALACRITTY_THEME=%ALACRITTY_THEME:\=/%"

REM Keep --option unquoted and attached: cmd passes outer quotes to Alacritty.
start "" alacritty.exe --config-file "%CONFIG%" --option=general.import=['%ALACRITTY_THEME%'] --working-directory "%USERHOME%\Downloads" %* --command cmd.exe /k "%USERHOME%\Share\dotfiles.win\Scoop\clink\init.cmd"
exit /b 0
