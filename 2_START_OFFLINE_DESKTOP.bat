@echo off
echo =========================================
echo ABIZ POS - OFFLINE DESKTOP SYSTEM
echo =========================================
echo.
cd desktop
echo Installing Desktop dependencies (pehli baar thoda time lagega)...
call npm install
npm start
pause
