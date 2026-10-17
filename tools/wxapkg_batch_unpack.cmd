@echo off
setlocal
set SCRIPT_DIR=%~dp0
node "%SCRIPT_DIR%wxapkg_batch_unpack.js" %*
endlocal
