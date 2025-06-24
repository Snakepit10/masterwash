@echo off
echo ============================================
echo  MASTERWASH DATABASE MIGRATION
echo ============================================
echo.

echo Attivazione ambiente virtuale...
call venv\Scripts\activate

echo.
echo Esecuzione migrazione database...
python migrate_db.py

echo.
echo Migrazione completata!
echo.
pause