# 🚗 MasterWash - Sistema Gestione Abbonamenti Autolavaggio

Web app completa per la gestione degli abbonamenti di un autolavaggio, ottimizzata per uso mobile da parte degli operatori.

## 🌟 Caratteristiche Principali

- **📱 Mobile-First**: Interfaccia ottimizzata per smartphone con PWA
- **🔍 Verifica Accessi**: Scansione/inserimento codici NFC per controllo abbonamenti
- **➕ Gestione Abbonamenti**: Creazione, modifica e rinnovo abbonamenti
- **📊 Dashboard Avanzata**: Statistiche in tempo reale con grafici interattivi
- **🖨️ Stampa Termica**: Ricevute su stampanti ESC/POS da 80mm
- **👥 Multi-Operatore**: Sistema di autenticazione per operatori e admin
- **🔄 Offline Support**: Funzionamento offline per operazioni critiche

## 🛠️ Tecnologie Utilizzate

- **Backend**: Flask + SQLAlchemy + PostgreSQL
- **Frontend**: Vanilla JavaScript + CSS3 (Mobile-first)
- **PWA**: Service Worker per funzionamento offline
- **Stampa**: Protocollo ESC/POS per stampanti termiche
- **Deploy**: Ottimizzato per Railway.app

## 📦 Installazione

### Locale

1. **Clona il repository**
   ```bash
   git clone <repo-url>
   cd masterwash
   ```

2. **Crea virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Installa dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura variabili ambiente**
   ```bash
   cp .env.example .env
   # Modifica .env con i tuoi valori
   ```

5. **Inizializza database**
   ```bash
   python init_db.py --demo
   ```

6. **Avvia l'applicazione**
   ```bash
   python app.py
   ```

7. **Accedi all'app**
   - URL: http://localhost:5000
   - Admin: `admin` / `admin123`
   - Operatore: `operatore1` / `operatore123`

### Deploy su Railway

1. **Connetti Repository**
   - Vai su [Railway.app](https://railway.app)
   - Crea nuovo progetto da GitHub

2. **Configura Database**
   - Aggiungi PostgreSQL service
   - Railway configurerà automaticamente `DATABASE_URL`

3. **Configura Variabili Ambiente**
   ```
   SECRET_KEY=your-production-secret-key
   FLASK_ENV=production
   ```

4. **Deploy Automatico**
   - Railway rileverà automaticamente Python
   - Userà `Procfile` e `requirements.txt`

## 🗃️ Struttura Database

### Operatori
- Gestione utenti con ruoli (admin/operatore)
- Autenticazione sicura con bcrypt

### Clienti
- Anagrafica completa con telefono univoco
- Integrazione con sistema abbonamenti

### Abbonamenti
- Tipologie: mensile, trimestrale, annuale
- Codici NFC univoci per identificazione
- Gestione stato pagamento e scadenze

### Accessi
- Log completo di tutti gli accessi
- Tracciabilità operatore e timestamp

### Stampanti
- Configurazione stampanti di rete
- Supporto protocollo ESC/POS

## 📱 Funzionalità Mobile

### Verifica Accessi
- Input rapido codice NFC (8 caratteri)
- Visualizzazione immediata stato abbonamento
- Registrazione accesso con un tap
- Feedback visivo e vibrazione

### Nuovo Abbonamento
- Autocompletamento clienti esistenti
- Suggerimenti prezzi in base al tipo
- Generazione automatica codici NFC
- Anteprima ricevuta

### Dashboard
- Statistiche in tempo reale
- Grafici accessi per fascia oraria
- Alert abbonamenti in scadenza
- Top clienti del mese

## 🖨️ Sistema Stampa

### Configurazione
- Ricerca automatica stampanti in rete locale
- Test connessione e stampa
- Supporto stampanti ESC/POS 80mm

### Ricevute
- Logo ASCII MasterWash
- Dati completi abbonamento
- QR Code per verifica rapida
- Layout ottimizzato per carta termica

## 🔧 API Endpoints

### Accessi
- `POST /accessi/verifica` - Verifica codice NFC
- `POST /accessi/registra` - Registra nuovo accesso
- `GET /accessi/api/verifica-nfc` - API AJAX verifica

### Abbonamenti
- `GET /abbonamenti/` - Lista con filtri e ricerca
- `POST /abbonamenti/nuovo` - Crea nuovo abbonamento
- `GET /abbonamenti/<id>` - Dettaglio abbonamento

### Dashboard
- `GET /api/accessi-orari` - Dati grafico accessi
- `GET /api/abbonamenti-mensili` - Dati grafico mensile
- `GET /api/stats-realtime` - Statistiche live

## 🎨 Personalizzazione

### Colori e Branding
Modifica le variabili CSS in `/static/css/style.css`:
```css
:root {
    --primary-color: #2563eb;  /* Blu principale */
    --success-color: #10b981;  /* Verde successo */
    --warning-color: #f59e0b;  /* Giallo warning */
    --danger-color: #ef4444;   /* Rosso errore */
}
```

### Logo e Icone
- Sostituisci `/static/icon-192.png` e `/static/icon-512.png`
- Modifica `manifest.json` per il nome dell'app
- Aggiorna logo ASCII in `utils/stampante.py`

## 🔒 Sicurezza

- Password hashate con bcrypt
- CSRF protection su tutti i form
- Validazione rigorosa input utente
- Session management sicuro
- Log degli accessi operatori

## 📊 Monitoraggio

### Log Applicazione
```bash
# Visualizza log in produzione
railway logs
```

### Metriche Database
- Contatori abbonamenti attivi/scaduti
- Statistiche accessi per periodo
- Performance query con SQLAlchemy

## 🚀 Performance

### Ottimizzazioni Frontend
- CSS minificato e compresso
- Service Worker per cache offline
- Lazy loading immagini
- Debouncing input di ricerca

### Ottimizzazioni Backend
- Connection pooling PostgreSQL
- Query ottimizzate con indici
- Paginazione su liste lunghe
- Cache API con headers appropriati

## 🔧 Troubleshooting

### Problemi Comuni

1. **Errore connessione database**
   ```bash
   # Verifica DATABASE_URL
   echo $DATABASE_URL
   ```

2. **Stampante non rilevata**
   - Verifica IP e porta (default 9100)
   - Controlla firewall di rete
   - Testa connessione manuale

3. **PWA non si installa**
   - Verifica HTTPS in produzione
   - Controlla `manifest.json`
   - Vedi console browser per errori

### Debug Mode
```bash
# Abilita debug locale
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

## 📞 Supporto

Per problemi o domande:
- Controlla i log dell'applicazione
- Verifica la documentazione API
- Testa in ambiente locale prima di produzione

## 📄 Licenza

Progetto sviluppato per uso interno autolavaggio.
Tutti i diritti riservati.

---

**MasterWash** - Sistema professionale per la gestione di abbonamenti autolavaggio 🚗✨