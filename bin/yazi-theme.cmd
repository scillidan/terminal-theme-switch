@echo off
setlocal
if defined YAZI_CONFIG_HOME goto run
for /f "usebackq delims=" %%p in (`terminal-theme-switch yazi 2^>nul`) do set "YAZI_CONFIG_HOME=%%p"
:run
yazi.exe %*
