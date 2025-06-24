from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import string

db = SQLAlchemy()

class Operatore(UserMixin, db.Model):
    """Modello per gli operatori dell'autolavaggio"""
    __tablename__ = 'operatori'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    ruolo = db.Column(db.String(20), nullable=False, default='operatore')  # admin, operatore
    attivo = db.Column(db.Boolean, default=True, nullable=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    accessi = db.relationship('Accesso', backref='operatore', lazy=True)
    
    def set_password(self, password):
        """Imposta la password hashata"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la password"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica se l'operatore è admin"""
        return self.ruolo == 'admin'
    
    def __repr__(self):
        return f'<Operatore {self.username}>'

class Cliente(db.Model):
    """Modello per i clienti dell'autolavaggio"""
    __tablename__ = 'clienti'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cognome = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    tipo_cliente = db.Column(db.String(20), nullable=True, default='privato')  # privato, business
    data_registrazione = db.Column(db.DateTime, default=datetime.utcnow)
    attivo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relazioni
    abbonamenti = db.relationship('Abbonamento', backref='cliente', lazy=True, cascade='all, delete-orphan')
    
    @property
    def nome_completo(self):
        """Ritorna nome e cognome concatenati"""
        return f"{self.nome} {self.cognome}"
    
    @property
    def abbonamento_attivo(self):
        """Ritorna l'abbonamento attivo del cliente"""
        return Abbonamento.query.filter_by(
            cliente_id=self.id, 
            attivo=True
        ).filter(
            Abbonamento.data_fine >= datetime.now().date()
        ).first()
    
    def ha_accesso_oggi(self):
        """Verifica se il cliente ha già effettuato un accesso oggi"""
        from sqlalchemy import func, and_
        today = datetime.now().date()
        
        # Per i clienti business non c'è limite
        if getattr(self, 'tipo_cliente', 'privato') == 'business':
            return False
        
        # Per i clienti privati, verifica se hanno già fatto un accesso oggi
        accesso_oggi = db.session.query(Accesso).join(Abbonamento).filter(
            and_(
                Abbonamento.cliente_id == self.id,
                func.date(Accesso.data_ora) == today
            )
        ).first()
        
        return accesso_oggi is not None
    
    @property
    def is_business(self):
        """Verifica se il cliente è di tipo business"""
        return getattr(self, 'tipo_cliente', 'privato') == 'business'
    
    @property
    def tipo_cliente_display(self):
        """Ritorna il tipo cliente formattato per la visualizzazione"""
        tipo = getattr(self, 'tipo_cliente', 'privato')
        return 'Business' if tipo == 'business' else 'Privato'
    
    def __repr__(self):
        return f'<Cliente {self.nome_completo}>'

class Abbonamento(db.Model):
    """Modello per gli abbonamenti"""
    __tablename__ = 'abbonamenti'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    targa = db.Column(db.String(10), nullable=False)
    data_inizio = db.Column(db.Date, nullable=False, default=datetime.now().date)
    data_fine = db.Column(db.Date, nullable=False)
    accessi_totali = db.Column(db.Integer, nullable=False)
    accessi_utilizzati = db.Column(db.Integer, default=0, nullable=False)
    codice_nfc = db.Column(db.String(20), unique=True, nullable=False)
    stato_pagamento = db.Column(db.String(20), default='non_pagato', nullable=False)  # pagato, non_pagato
    tipo_abbonamento = db.Column(db.String(20), nullable=False)  # mensile, trimestrale, annuale
    prezzo = db.Column(db.Numeric(10, 2), nullable=False)
    attivo = db.Column(db.Boolean, default=True, nullable=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    accessi = db.relationship('Accesso', backref='abbonamento', lazy=True)
    
    # Indice unico per targa attiva (un solo abbonamento attivo per targa)
    __table_args__ = (
        db.Index('ix_targa_attivo', 'targa', 'attivo'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Se data_inizio non è specificata, usa oggi
        if not self.data_inizio:
            self.data_inizio = datetime.now().date()
        # Genera codice NFC se non specificato
        if not self.codice_nfc:
            self.codice_nfc = self.genera_codice_nfc()
        # Calcola data fine se non specificata
        if not self.data_fine and self.tipo_abbonamento:
            self.calcola_data_fine()
    
    @staticmethod
    def genera_codice_nfc():
        """Genera un codice NFC univoco"""
        while True:
            codice = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Abbonamento.query.filter_by(codice_nfc=codice).first():
                return codice
    
    @property
    def url_nfc(self):
        """Ritorna l'URL completo per il tag NFC"""
        from flask import current_app, url_for
        try:
            with current_app.app_context():
                # Usa il dominio locale configurato
                base_url = current_app.config.get('BASE_URL', 'http://192.168.1.84:5000')
                return f"{base_url}/abbonamenti/nfc/{self.codice_nfc}"
        except:
            # Fallback per quando non c'è app context
            return f"http://192.168.1.84:5000/abbonamenti/nfc/{self.codice_nfc}"
    
    def calcola_data_fine(self):
        """Calcola la data di fine abbonamento in base al tipo"""
        # Se data_inizio non è impostata, usa la data corrente
        if not self.data_inizio:
            self.data_inizio = datetime.now().date()
            
        if self.tipo_abbonamento == 'mensile':
            self.data_fine = self.data_inizio + timedelta(days=30)
        elif self.tipo_abbonamento == 'trimestrale':
            self.data_fine = self.data_inizio + timedelta(days=90)
        elif self.tipo_abbonamento == 'annuale':
            self.data_fine = self.data_inizio + timedelta(days=365)
    
    @property
    def accessi_rimanenti(self):
        """Calcola gli accessi rimanenti"""
        return max(0, self.accessi_totali - self.accessi_utilizzati)
    
    @property
    def giorni_alla_scadenza(self):
        """Calcola i giorni alla scadenza"""
        return (self.data_fine - datetime.now().date()).days
    
    @property
    def is_scaduto(self):
        """Verifica se l'abbonamento è scaduto"""
        return datetime.now().date() > self.data_fine
    
    @property
    def is_in_scadenza(self):
        """Verifica se l'abbonamento è in scadenza (entro 7 giorni)"""
        return 0 <= self.giorni_alla_scadenza <= 7
    
    @property
    def ultimo_accesso(self):
        """Ritorna l'ultimo accesso registrato"""
        return Accesso.query.filter_by(abbonamento_id=self.id).order_by(Accesso.data_ora.desc()).first()
    
    @property
    def colore_accessi(self):
        """Ritorna il colore per visualizzare gli accessi rimanenti"""
        rimanenti = self.accessi_rimanenti
        if rimanenti > 5:
            return 'success'  # verde
        elif rimanenti >= 2:
            return 'warning'  # giallo
        else:
            return 'danger'   # rosso
    
    def registra_accesso(self, operatore_id, note=None):
        """Registra un nuovo accesso"""
        # Verifica condizioni base
        if self.accessi_rimanenti <= 0 or self.is_scaduto:
            return None
        
        # Verifica limite giornaliero per clienti privati
        tipo_cliente = getattr(self.cliente, 'tipo_cliente', 'privato')
        if tipo_cliente == 'privato' and self.cliente.ha_accesso_oggi():
            return None  # Cliente privato che ha già effettuato un accesso oggi
        
        # Registra l'accesso
        accesso = Accesso(
            abbonamento_id=self.id,
            operatore_id=operatore_id,
            note=note
        )
        db.session.add(accesso)
        self.accessi_utilizzati += 1
        db.session.commit()
        return accesso
    
    def __repr__(self):
        return f'<Abbonamento {self.codice_nfc} - {self.cliente.nome_completo}>'

class Accesso(db.Model):
    """Modello per registrare gli accessi"""
    __tablename__ = 'accessi'
    
    id = db.Column(db.Integer, primary_key=True)
    abbonamento_id = db.Column(db.Integer, db.ForeignKey('abbonamenti.id'), nullable=False)
    data_ora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    operatore_id = db.Column(db.Integer, db.ForeignKey('operatori.id'), nullable=False)
    note = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<Accesso {self.data_ora} - {self.abbonamento.codice_nfc}>'

class ImpostazioniStampante(db.Model):
    """Modello per le impostazioni della stampante"""
    __tablename__ = 'impostazioni_stampante'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_stampante = db.Column(db.String(15), nullable=False)
    porta = db.Column(db.Integer, default=9100, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo_stampante = db.Column(db.String(50), default='ESC/POS', nullable=False)
    larghezza_carta = db.Column(db.Integer, default=80, nullable=False)  # mm
    attiva = db.Column(db.Boolean, default=True, nullable=False)
    data_creazione = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stampante {self.nome} - {self.ip_stampante}>'

# Funzioni di utilità per il database
def init_db():
    """Inizializza il database con dati di esempio"""
    db.create_all()
    
    # Crea admin di default se non esiste
    admin = Operatore.query.filter_by(username='admin').first()
    if not admin:
        admin = Operatore(
            username='admin',
            nome='Amministratore',
            ruolo='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin creato - Username: admin, Password: admin123")
    
    # Crea operatore di esempio
    operatore = Operatore.query.filter_by(username='operatore1').first()
    if not operatore:
        operatore = Operatore(
            username='operatore1',
            nome='Mario Rossi',
            ruolo='operatore'
        )
        operatore.set_password('operatore123')
        db.session.add(operatore)
        db.session.commit()
        print("Operatore creato - Username: operatore1, Password: operatore123")
    
    # Crea impostazioni stampante di default
    stampante = ImpostazioniStampante.query.first()
    if not stampante:
        stampante = ImpostazioniStampante(
            ip_stampante='192.168.1.100',
            nome='Stampante Principale',
            tipo_stampante='ESC/POS',
            larghezza_carta=80
        )
        db.session.add(stampante)
        db.session.commit()
        print("Impostazioni stampante create")

def crea_dati_demo():
    """Crea dati di demo per test"""
    # Cliente di esempio
    cliente = Cliente.query.filter_by(telefono='3331234567').first()
    if not cliente:
        cliente = Cliente(
            nome='Giuseppe',
            cognome='Verdi',
            telefono='3331234567',
            email='giuseppe.verdi@email.com'
        )
        db.session.add(cliente)
        db.session.flush()
        
        # Abbonamento di esempio
        abbonamento = Abbonamento(
            cliente_id=cliente.id,
            targa='AB123CD',
            tipo_abbonamento='mensile',
            accessi_totali=10,
            accessi_utilizzati=3,
            prezzo=50.00,
            stato_pagamento='pagato'
        )
        abbonamento.calcola_data_fine()
        db.session.add(abbonamento)
        db.session.commit()
        print(f"Dati demo creati - Cliente: {cliente.nome_completo}, NFC: {abbonamento.codice_nfc}")