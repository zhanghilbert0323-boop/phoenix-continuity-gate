@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PHOENIX_EXIT=2"
set "PHOENIX_PYTHON="
set "PHOENIX_MODE="
set "PHOENIX_NO_PAUSE="
set "PHOENIX_PUSHED="
set "PYLAUNCHER_ALLOW_INSTALL="
set "PYLAUNCHER_ALWAYS_INSTALL="
set "PYLAUNCHER_DRYRUN="
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=false"
if /i "%~1"=="--no-pause" set "PHOENIX_NO_PAUSE=1"
if /i "%~2"=="--no-pause" set "PHOENIX_NO_PAUSE=1"
:parse_args
if "%~1"=="" goto prerequisites
if /i "%~1"=="--check" goto check_arg
if /i "%~1"=="--no-pause" goto no_pause_arg
echo ERROR: Usage: START_DEMO.cmd [--check] [--no-pause]
goto finished
:check_arg
set "PHOENIX_MODE=--check"
shift /1
goto parse_args
:no_pause_arg
set "PHOENIX_NO_PAUSE=1"
shift /1
goto parse_args
:prerequisites
echo Phoenix Continuity Gate - Windows demo launcher
echo Checking installed Python runtimes. No installation is requested.
if not exist "%~dp0start_demo.py" goto missing_files
pushd "%~dp0"
if errorlevel 1 goto missing_files
set "PHOENIX_PUSHED=1"
rem List installed runtimes only. Never ask a launcher to install or select one.
for /f "tokens=1,*" %%A in ('py -0p 2^>nul') do (
    set "PHOENIX_CANDIDATE=%%B"
    call :probe_candidate
)
for /f "delims=" %%A in ('where.exe python.exe 2^>nul') do (
    set "PHOENIX_CANDIDATE=%%A"
    call :probe_candidate
)
for /f "delims=" %%A in ('where.exe python3.exe 2^>nul') do (
    set "PHOENIX_CANDIDATE=%%A"
    call :probe_candidate
)
if not defined PHOENIX_PYTHON goto missing_python
"%PHOENIX_PYTHON%" -I -B start_demo.py %PHOENIX_MODE%
set "PHOENIX_EXIT=%errorlevel%"
goto finished

:probe_candidate
if defined PHOENIX_PYTHON exit /b
if "%PHOENIX_CANDIDATE:~0,1%"=="*" set "PHOENIX_CANDIDATE=%PHOENIX_CANDIDATE:~1%"
for /f "tokens=*" %%P in ("%PHOENIX_CANDIDATE%") do set "PHOENIX_CANDIDATE=%%P"
rem Skip Store aliases; an exit code of zero without Python output is not proof.
if /i not "%PHOENIX_CANDIDATE:WindowsApps=%"=="%PHOENIX_CANDIDATE%" exit /b
if not exist "%PHOENIX_CANDIDATE%" exit /b
for /f "delims=" %%R in ('""%PHOENIX_CANDIDATE%" -I -B start_demo.py --probe" 2^>nul') do if "%%R"=="PHOENIX_READY" set "PHOENIX_PYTHON=%PHOENIX_CANDIDATE%"
exit /b

:missing_files
echo ERROR: start_demo.py is missing. Extract the complete ZIP to a new folder.
goto finished

:missing_python
echo ERROR: Could not verify an installed Python 3.11 or newer interpreter.
echo A Store shortcut or an empty command result does not count as Python.
echo Install Python yourself if needed, then reopen this launcher.
echo Advanced: run your full Python executable path with start_demo.py.
echo See QUICKSTART.zh-CN.md for help. Nothing was installed by this script.
goto finished

:finished
echo.
if "%PHOENIX_EXIT%"=="0" (echo Launcher finished successfully.) else echo Launcher stopped with exit code %PHOENIX_EXIT%. Keep the error text above.
if not defined PHOENIX_NO_PAUSE pause
if defined PHOENIX_PUSHED popd
endlocal & exit /b %PHOENIX_EXIT%
