@echo off
echo 🚗 Installazione MasterWash per Windows...
echo.

REM Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python non trovato. Scarica da https://python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python trovato

REM Installa dipendenze base
echo 📦 Installazione dipendenze...
pip install -r requirements-simple.txt

if %errorlevel% neq 0 (
    echo ❌ Errore installazione dipendenze
    pause
    exit /b 1
)

echo ✅ Dipendenze installate

REM Crea file .env
if not exist .env (
    echo 📄 Creazione file .env...
    copy .env.sqlite .env
    echo ✅ File .env creato
) else (
    echo ⚠️ File .env già esistente
)

REM Inizializza database
echo 🗃️ Inizializzazione database...
python init_db.py --demo

if %errorlevel% neq 0 (
    echo ❌ Errore inizializzazione database
    pause
    exit /b 1
)

echo.
echo 🎉 Installazione completata!
echo.
echo 📋 Per avviare l'app:
echo    python app.py
echo.
echo 🌐 Apri: http://localhost:5000
echo.
echo 🔑 Credenziali:
echo    Admin: admin / admin123
echo    Operatore: operatore1 / operatore123
echo.
pause