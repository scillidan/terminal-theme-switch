@echo off
setlocal
if defined OPENCODE_CLI_CONFIG_CONTENT goto run
for /f "tokens=2" %%m in ('terminal-theme-switch get 2^>nul') do set "MODE=%%m"
if not defined MODE goto run
set "OPENCODE_CLI_CONFIG_CONTENT={"theme":{"mode":"%MODE%"}}"
:run
opencode.exe %*
