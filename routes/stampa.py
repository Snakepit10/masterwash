from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, IPAddress, Length
from models import db, ImpostazioniStampante, Abbonamento, Cliente
from utils.stampante import StampanteTermica, genera_ricevuta_html
import socket
import threading
from datetime import datetime

stampa_bp = Blueprint('stampa', __name__)

class ImpostazioniStampanteForm(FlaskForm):
    """Form per configurazione stampante"""
    nome = StringField('Nome Stampante', validators=[
        DataRequired(message='Inserisci il nome della stampante'),
        Length(min=2, max=100, message='Il nome deve essere tra 2 e 100 caratteri')
    ])
    ip_stampante = StringField('Indirizzo IP', validators=[
        DataRequired(message='Inserisci l\'indirizzo IP'),
        IPAddress(message='Inserisci un indirizzo IP valido')
    ])
    porta = IntegerField('Porta', validators=[
        DataRequired(message='Inserisci la porta'),
        NumberRange(min=1, max=65535, message='La porta deve essere tra 1 e 65535')
    ], default=9100)
    tipo_stampante = SelectField('Tipo Stampante', choices=[
        ('ESC/POS', 'ESC/POS'),
        ('Generic', 'Generica')
    ], default='ESC/POS')
    larghezza_carta = SelectField('Larghezza Carta', choices=[
        (58, '58mm'),
        (80, '80mm')
    ], coerce=int, default=80)
    attiva = BooleanField('Stampante Attiva', default=True)
    submit = SubmitField('Salva Configurazione')

@stampa_bp.route('/configurazione', methods=['GET', 'POST'])
@login_required
def configurazione():
    """Configurazione stampante"""
    
    # Cerca configurazione esistente
    config = ImpostazioniStampante.query.filter_by(attiva=True).first()
    
    if request.method == 'GET':
        if config:
            form = ImpostazioniStampanteForm(obj=config)
        else:
            form = ImpostazioniStampanteForm()
    else:
        form = ImpostazioniStampanteForm()
    
    if form.validate_on_submit():
        try:
            if config:
                # Aggiorna configurazione esistente
                config.nome = form.nome.data
                config.ip_stampante = form.ip_stampante.data
                config.porta = form.porta.data
                config.tipo_stampante = form.tipo_stampante.data
                config.larghezza_carta = form.larghezza_carta.data
                config.attiva = form.attiva.data
            else:
                # Crea nuova configurazione
                config = ImpostazioniStampante(
                    nome=form.nome.data,
                    ip_stampante=form.ip_stampante.data,
                    porta=form.porta.data,
                    tipo_stampante=form.tipo_stampante.data,
                    larghezza_carta=form.larghezza_carta.data,
                    attiva=form.attiva.data
                )
                db.session.add(config)
            
            db.session.commit()
            flash('Configurazione stampante salvata', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante il salvataggio: {str(e)}', 'error')
    
    return render_template('stampa/configurazione.html', form=form, config=config)

@stampa_bp.route('/test')
@login_required
def test():
    """Test stampa"""
    
    config = ImpostazioniStampante.query.filter_by(attiva=True).first()
    
    if not config:
        flash('Nessuna stampante configurata', 'error')
        return redirect(url_for('stampa.configurazione'))
    
    try:
        stampante = StampanteTermica(config.ip_stampante, config.porta)
        
        # Testo di prova
        testo_test = f"""
        {'='*32}
        MASTERWASH - TEST STAMPA
        {'='*32}
        
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        Operatore: {current_user.nome}
        Stampante: {config.nome}
        IP: {config.ip_stampante}:{config.porta}
        
        Test completato con successo!
        
        {'='*32}
        """
        
        if stampante.stampa_testo(testo_test):
            flash('Test stampa completato con successo', 'success')
        else:
            flash('Errore durante il test di stampa', 'error')
            
    except Exception as e:
        flash(f'Errore connessione stampante: {str(e)}', 'error')
    
    return redirect(url_for('stampa.configurazione'))

@stampa_bp.route('/ricevuta/<int:abbonamento_id>')
@login_required
def ricevuta(abbonamento_id):
    """Stampa ricevuta abbonamento"""
    
    abbonamento = Abbonamento.query.get_or_404(abbonamento_id)
    config = ImpostazioniStampante.query.filter_by(attiva=True).first()
    
    if not config:
        flash('Nessuna stampante configurata', 'error')
        return redirect(url_for('abbonamenti.dettaglio', id=abbonamento_id))
    
    try:
        stampante = StampanteTermica(config.ip_stampante, config.porta)
        
        # Genera contenuto ricevuta
        ricevuta_testo = genera_ricevuta_testo(abbonamento, current_user, config.larghezza_carta)
        
        if stampante.stampa_ricevuta(ricevuta_testo):
            flash('Ricevuta stampata con successo', 'success')
        else:
            flash('Errore durante la stampa della ricevuta', 'error')
            
    except Exception as e:
        flash(f'Errore stampa ricevuta: {str(e)}', 'error')
    
    return redirect(url_for('abbonamenti.dettaglio', id=abbonamento_id))

@stampa_bp.route('/anteprima/<int:abbonamento_id>')
@login_required
def anteprima(abbonamento_id):
    """Anteprima ricevuta"""
    
    abbonamento = Abbonamento.query.get_or_404(abbonamento_id)
    config = ImpostazioniStampante.query.filter_by(attiva=True).first()
    
    if not config:
        config = ImpostazioniStampante(larghezza_carta=80)  # Default per anteprima
    
    ricevuta_html = genera_ricevuta_html(abbonamento, current_user, config.larghezza_carta)
    
    return render_template('stampa/anteprima.html', 
                         ricevuta_html=ricevuta_html,
                         abbonamento=abbonamento)

@stampa_bp.route('/api/cerca-stampanti')
@login_required
def api_cerca_stampanti():
    """API per cercare stampanti in rete locale"""
    
    def scan_ip(ip, risultati):
        """Scansiona singolo IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, 9100))
            sock.close()
            
            if result == 0:
                risultati.append({
                    'ip': ip,
                    'porta': 9100,
                    'nome': f'Stampante {ip}',
                    'stato': 'online'
                })
        except:
            pass
    
    # Cerca stampanti nella rete locale (192.168.1.x)
    import subprocess
    import re
    
    stampanti_trovate = []
    
    try:
        # Ottieni IP locale
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ip_locale = result.stdout.strip().split()[0]
            base_ip = '.'.join(ip_locale.split('.')[:-1])
            
            # Scansiona range IP
            threads = []
            risultati = []
            
            for i in range(1, 255):
                ip = f"{base_ip}.{i}"
                t = threading.Thread(target=scan_ip, args=(ip, risultati))
                threads.append(t)
                t.start()
            
            # Attendi completamento (max 5 secondi)
            for t in threads:
                t.join(timeout=0.02)
            
            stampanti_trovate = risultati
            
    except Exception as e:
        print(f"Errore ricerca stampanti: {e}")
    
    return jsonify({
        'stampanti': stampanti_trovate,
        'count': len(stampanti_trovate)
    })

def genera_ricevuta_testo(abbonamento, operatore, larghezza_carta=80):
    """Genera il testo della ricevuta per stampa termica"""
    
    # Larghezza linea in base alla carta
    w = larghezza_carta // 2 if larghezza_carta == 80 else 29
    
    # Header
    testo = f"""
{'=' * w}
      MASTERWASH
   AUTOLAVAGGIO
{'=' * w}

RICEVUTA ABBONAMENTO

Cliente: {abbonamento.cliente.nome_completo}
Telefono: {abbonamento.cliente.telefono}
{'Email: ' + abbonamento.cliente.email if abbonamento.cliente.email else ''}

{'-' * w}

Targa: {abbonamento.targa}
Tipo: {abbonamento.tipo_abbonamento.title()}
Codice NFC: {abbonamento.codice_nfc}

Accessi totali: {abbonamento.accessi_totali}
Accessi utilizzati: {abbonamento.accessi_utilizzati}
Accessi rimanenti: {abbonamento.accessi_rimanenti}

Data inizio: {abbonamento.data_inizio.strftime('%d/%m/%Y')}
Data fine: {abbonamento.data_fine.strftime('%d/%m/%Y')}

{'-' * w}

Prezzo: € {abbonamento.prezzo:.2f}
Stato: {abbonamento.stato_pagamento.replace('_', ' ').title()}

{'-' * w}

Data stampa: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Operatore: {operatore.nome}

{'=' * w}

Conservare questa ricevuta
per eventuale assistenza.

Grazie per aver scelto
MASTERWASH!

{'=' * w}
"""
    
    return testo.strip()