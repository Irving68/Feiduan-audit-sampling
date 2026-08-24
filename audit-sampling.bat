@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%;%PYTHONPATH%"
pushd "%ROOT%"
"%ROOT%runtime\python\python.exe" -m audit_sampling %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
endlocal & exit /b %EXIT_CODE%
