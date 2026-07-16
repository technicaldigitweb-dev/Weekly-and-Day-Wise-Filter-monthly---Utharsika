@echo off
REM UAWSO daily automation - Windows entry point wrapper.
REM Invokes the uawso_daily package as a module; contains no business logic
REM of its own. Sets the working directory to 05_IMPLEMENTATION so the
REM `config` and `src` sibling packages resolve correctly.
REM
REM Usage:
REM   commands\update_for_today.bat
REM   commands\update_for_today.bat --dry-run --verbose
REM   commands\update_for_today.bat --no-publish --verbose
REM
REM Exit code: 0 on any success-family outcome (SUCCESS, ALREADY_COMPLETE,
REM DRY_RUN_COMPLETE, NO_PUBLISH_COMPLETE); 1 on any failure code.

setlocal
set SCRIPT_DIR=%~dp0
set IMPL_ROOT=%SCRIPT_DIR%..
pushd "%IMPL_ROOT%"

python -m uawso_daily update-for-today %*
set EXIT_CODE=%ERRORLEVEL%

popd
exit /b %EXIT_CODE%
