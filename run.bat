@echo off
setlocal enabledelayedexpansion
title Reference Fixer

:: ─────────────────────────────────────────────
::  Reference Fixer — Interactive Launcher
:: ─────────────────────────────────────────────

echo.
echo  ╔═════════════════════════════════════════════════╗
echo  ║              REFERENCE FIXER  v1.0              ║
echo  ║   APA Citation Audit Tool for Research Papers   ║
echo  ╚═════════════════════════════════════════════════╝
echo.
echo  This tool checks your research paper against your reference list and:
echo    ^• Finds references NOT cited in the research paper
echo    ^• Finds citations in the research paper NOT in the references
echo    ^• Ranks citations by mention frequency
echo    ^• Extracts grouped parenthetical citation blocks for analysis
echo.
echo  Output files generated:
echo    output.csv          — Full forward-check table
echo    rankings.csv        — First-author mention count rankings
echo    orphans.csv         — Citations not found in references
echo    paren_groups.csv    — Parenthetical groups ranked by size
echo.
echo ══════════════════════════════════════════════════
echo.

:: ── Check if arguments were passed directly ──────────────────────────────
if not "%~1"=="" (
    if /i "%~1"=="--help" goto :show_help
    if /i "%~1"=="-h"     goto :show_help
    goto :run_with_args
)

:: ── Interactive mode ──────────────────────────────────────────────────────
:prompt_refs
set /p REFS_PDF= Enter path to REFERENCES PDF: 
if "!REFS_PDF!"=="" (
    echo  [!] Path cannot be empty. Please try again.
    goto :prompt_refs
)
if not exist "!REFS_PDF!" (
    echo  [!] File not found: !REFS_PDF!
    goto :prompt_refs
)

:prompt_disc
set /p DISC_PDF= Enter path to DISCUSSION PDF:  
if "!DISC_PDF!"=="" (
    echo  [!] Path cannot be empty. Please try again.
    goto :prompt_disc
)
if not exist "!DISC_PDF!" (
    echo  [!] File not found: !DISC_PDF!
    goto :prompt_disc
)

echo.
set /p VERBOSE= Enable verbose output? (shows all parsed refs) [y/N]:  
set VERBOSE_FLAG=
if /i "!VERBOSE!"=="y" set VERBOSE_FLAG=-v

echo.
echo ══════════════════════════════════════════════════
echo  Running reference-fixer...
echo ══════════════════════════════════════════════════
echo.
reference-fixer "!REFS_PDF!" "!DISC_PDF!" !VERBOSE_FLAG!
goto :done

:: ── Direct argument passthrough ───────────────────────────────────────────
:run_with_args
reference-fixer %*
goto :done

:: ── Help text ─────────────────────────────────────────────────────────────
:show_help
echo  USAGE:
echo    run.bat                              — interactive mode (guided)
echo    run.bat ^<refs.pdf^> ^<discussion.pdf^>  — direct mode
echo    run.bat ^<refs.pdf^> ^<discussion.pdf^> -v — direct mode with verbose output
echo.
echo  OPTIONS:
echo    -v, --verbose    Show all parsed references and their extracted authors
echo    -h, --help       Show this help message
echo.
echo  EXAMPLES:
echo    run.bat References.pdf RRL.pdf
echo    run.bat "C:\Thesis\References.pdf" "C:\Thesis\RRL.pdf" -v
echo.
goto :done

:: ── Done ──────────────────────────────────────────────────────────────────
:done
echo.
echo ══════════════════════════════════════════════════
echo  Done! Check the CSV files in the current folder.
echo ══════════════════════════════════════════════════
echo.
pause
endlocal
