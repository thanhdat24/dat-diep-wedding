@echo off
chcp 65001 >nul
title Wedding HTML Optimizer V2.8.1

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 OPTIMIZE-HTML-V2.8.1.py
  goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
  python OPTIMIZE-HTML-V2.8.1.py
  goto :eof
)

echo.
echo Khong tim thay Python tren may.
echo Hay cai Python 3 roi chay lai file nay.
echo.
pause
