@echo off
chcp 65001 >nul
cd /d "%~dp0"
python PATCH-INDEX.py
if errorlevel 1 (
  echo.
  echo Loi: khong the cap nhat index.html.
  echo Dam bao Python da duoc cai va index.html nam cung thu muc.
) else (
  echo.
  echo Hoan tat. Bam Ctrl+F5 khi mo lai website.
)
pause
