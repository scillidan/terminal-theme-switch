@echo off
setlocal
for /f "usebackq delims=" %%I in (`call terminal-theme-switch alacritty`) do set "ALACRITTY_THEME=%%I"
if not defined ALACRITTY_THEME (
    echo alacritty-theme.cmd: terminal-theme-switch returned no theme path >&2
    exit /b 1
)
set "ALACRITTY_THEME=%ALACRITTY_THEME:\=/%"

REM Keep --option unquoted and attached: cmd passes outer quotes to Alacritty.
alacritty.exe --option=general.import=['%ALACRITTY_THEME%'] %*
