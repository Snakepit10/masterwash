#!/bin/bash

# Script di setup automatico per MasterWash
echo "🚗 Configurazione MasterWash..."

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per stampa colorata
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verifica Python
print_info "Verifica Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 non trovato. Installare Python 3.8+"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python $python_version trovato"

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 non trovato"
    exit 1
fi

# Crea virtual environment
print_info "Creazione virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment creato"
else
    print_warning "Virtual environment già esistente"
fi

# Attiva virtual environment
print_info "Attivazione virtual environment..."
source venv/bin/activate || {
    print_error "Impossibile attivare virtual environment"
    exit 1
}

# Aggiorna pip
print_info "Aggiornamento pip..."
pip install --upgrade pip > /dev/null 2>&1

# Installa dipendenze
print_info "Installazione dipendenze..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "Dipendenze installate"
else
    print_error "Errore installazione dipendenze"
    exit 1
fi

# Crea file .env se non esiste
if [ ! -f ".env" ]; then
    print_info "Creazione file .env..."
    cp .env.example .env
    print_status "File .env creato da template"
    print_warning "Modifica .env con le tue configurazioni"
else
    print_warning "File .env già esistente"
fi

# Chiedi se inizializzare il database
read -p "Vuoi inizializzare il database con dati demo? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Inizializzazione database..."
    python init_db.py --demo
    if [ $? -eq 0 ]; then
        print_status "Database inizializzato con dati demo"
    else
        print_error "Errore inizializzazione database"
        exit 1
    fi
fi

# Informazioni finali
echo
echo "🎉 Setup completato!"
echo
echo "📋 Prossimi passi:"
echo "1. Modifica .env con le tue configurazioni"
echo "2. Per avviare l'app: source venv/bin/activate && python app.py"
echo "3. Apri http://localhost:5000"
echo
echo "🔑 Credenziali di default:"
echo "   Admin: admin / admin123"
echo "   Operatore: operatore1 / operatore123"
echo
print_status "Setup MasterWash completato!"

# Script per Windows (PowerShell)
cat > setup.ps1 << 'EOF'
# Script di setup per Windows PowerShell
Write-Host "🚗 Configurazione MasterWash..." -ForegroundColor Blue

# Verifica Python
Write-Host "Verifica Python..." -ForegroundColor Yellow
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python non trovato. Installare Python 3.8+" -ForegroundColor Red
    exit 1
}

$pythonVersion = python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
Write-Host "✅ Python $pythonVersion trovato" -ForegroundColor Green

# Crea virtual environment
Write-Host "Creazione virtual environment..." -ForegroundColor Yellow
if (!(Test-Path "venv")) {
    python -m venv venv
    Write-Host "✅ Virtual environment creato" -ForegroundColor Green
} else {
    Write-Host "⚠️ Virtual environment già esistente" -ForegroundColor Yellow
}

# Attiva virtual environment
Write-Host "Attivazione virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Aggiorna pip
Write-Host "Aggiornamento pip..." -ForegroundColor Yellow
pip install --upgrade pip *>$null

# Installa dipendenze
Write-Host "Installazione dipendenze..." -ForegroundColor Yellow
pip install -r requirements.txt *>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dipendenze installate" -ForegroundColor Green
} else {
    Write-Host "❌ Errore installazione dipendenze" -ForegroundColor Red
    exit 1
}

# Crea file .env
if (!(Test-Path ".env")) {
    Write-Host "Creazione file .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ File .env creato" -ForegroundColor Green
} else {
    Write-Host "⚠️ File .env già esistente" -ForegroundColor Yellow
}

# Chiedi inizializzazione database
$initDb = Read-Host "Vuoi inizializzare il database con dati demo? (y/N)"
if ($initDb -eq "y" -or $initDb -eq "Y") {
    Write-Host "Inizializzazione database..." -ForegroundColor Yellow
    python init_db.py --demo
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database inizializzato" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🎉 Setup completato!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Prossimi passi:"
Write-Host "1. Modifica .env con le tue configurazioni"
Write-Host "2. Per avviare: venv\Scripts\Activate.ps1 && python app.py"
Write-Host "3. Apri http://localhost:5000"
Write-Host ""
Write-Host "🔑 Credenziali di default:"
Write-Host "   Admin: admin / admin123"
Write-Host "   Operatore: operatore1 / operatore123"
EOF

print_status "Creato anche setup.ps1 per Windows"