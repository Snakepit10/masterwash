from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, DecimalField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from models import db, Cliente, Abbonamento
from utils.validators import valida_telefono, valida_targa, valida_prezzo, valida_accessi, pulisci_telefono, pulisci_targa

abbonamenti_bp = Blueprint('abbonamenti', __name__)

class ClienteForm(FlaskForm):
    """Form per la registrazione/modifica cliente"""
    nome = StringField('Nome', validators=[
        DataRequired(message='Inserisci il nome'),
        Length(min=2, max=50, message='Il nome deve essere tra 2 e 50 caratteri')
    ])
    cognome = StringField('Cognome', validators=[
        DataRequired(message='Inserisci il cognome'),
        Length(min=2, max=50, message='Il cognome deve essere tra 2 e 50 caratteri')
    ])
    telefono = StringField('Telefono', validators=[
        DataRequired(message='Inserisci il numero di telefono'),
        valida_telefono
    ])
    email = StringField('Email (facoltativo)', validators=[
        Optional(),
        Email(message='Inserisci un indirizzo email valido')
    ])
    tipo_cliente = SelectField('Tipo Cliente', choices=[
        ('privato', 'Privato (1 accesso/giorno)'),
        ('business', 'Business (accessi illimitati)')
    ], default='privato')

class AbbonamentoForm(FlaskForm):
    """Form per la creazione/modifica abbonamento"""
    # Dati cliente (per nuovo abbonamento)
    cliente_id = SelectField('Cliente esistente', coerce=int, validators=[Optional()])
    
    # Nuovo cliente
    nome = StringField('Nome', validators=[Optional()])
    cognome = StringField('Cognome', validators=[Optional()])
    telefono = StringField('Telefono', validators=[Optional()])
    email = StringField('Email (facoltativo)', validators=[Optional(), Email()])
    tipo_cliente = SelectField('Tipo Cliente', choices=[
        ('privato', 'Privato (1 accesso/giorno)'),
        ('business', 'Business (accessi illimitati)')
    ], default='privato', validators=[Optional()])
    
    # Dati abbonamento
    targa = StringField('Targa', validators=[
        DataRequired(message='Inserisci la targa'),
        valida_targa
    ])
    tipo_abbonamento = SelectField('Tipo Abbonamento', choices=[
        ('mensile', 'Mensile (30 giorni)'),
        ('trimestrale', 'Trimestrale (90 giorni)'),
        ('annuale', 'Annuale (365 giorni)')
    ], validators=[DataRequired()])
    
    accessi_totali = IntegerField('Numero Accessi', validators=[
        DataRequired(message='Inserisci il numero di accessi'),
        NumberRange(min=1, max=1000, message='Gli accessi devono essere tra 1 e 1000')
    ])
    
    prezzo = DecimalField('Prezzo (€)', validators=[
        DataRequired(message='Inserisci il prezzo'),
        NumberRange(min=0.01, message='Il prezzo deve essere maggiore di zero')
    ])
    
    stato_pagamento = SelectField('Stato Pagamento', choices=[
        ('non_pagato', 'Non Pagato'),
        ('pagato', 'Pagato')
    ], default='non_pagato')
    
    codice_nfc = StringField('Codice NFC (lascia vuoto per generazione automatica)', validators=[Optional()])
    
    submit = SubmitField('Salva Abbonamento')

@abbonamenti_bp.route('/')
@login_required
def index():
    """Lista abbonamenti con ricerca e filtri"""
    
    # Parametri di ricerca
    search = request.args.get('search', '').strip()
    filtro = request.args.get('filtro', 'tutti')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query base
    query = Abbonamento.query.join(Cliente)
    
    # Filtro per ricerca
    if search:
        query = query.filter(
            or_(
                Cliente.nome.ilike(f'%{search}%'),
                Cliente.cognome.ilike(f'%{search}%'),
                Cliente.telefono.ilike(f'%{search}%'),
                Abbonamento.targa.ilike(f'%{search}%'),
                Abbonamento.codice_nfc.ilike(f'%{search}%')
            )
        )
    
    # Filtri per stato
    today = datetime.now().date()
    if filtro == 'attivi':
        query = query.filter(
            and_(Abbonamento.attivo == True, Abbonamento.data_fine >= today)
        )
    elif filtro == 'scaduti':
        query = query.filter(
            and_(Abbonamento.attivo == True, Abbonamento.data_fine < today)
        )
    elif filtro == 'in_scadenza':
        query = query.filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.data_fine >= today,
                Abbonamento.data_fine <= today + timedelta(days=7)
            )
        )
    elif filtro == 'esauriti':
        query = query.filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.accessi_utilizzati >= Abbonamento.accessi_totali
            )
        )
    
    # Ordinamento
    query = query.order_by(Abbonamento.data_creazione.desc())
    
    # Paginazione
    abbonamenti = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('abbonamenti/index.html',
                         abbonamenti=abbonamenti,
                         search=search,
                         filtro=filtro)

@abbonamenti_bp.route('/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo():
    """Crea nuovo abbonamento"""
    
    form = AbbonamentoForm()
    
    # Popola select clienti
    clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.cognome, Cliente.nome).all()
    form.cliente_id.choices = [(0, 'Nuovo Cliente')] + [(c.id, f"{c.nome_completo} - {c.telefono}") for c in clienti]
    
    if form.validate_on_submit():
        try:
            cliente = None
            
            # Se è selezionato un cliente esistente
            if form.cliente_id.data > 0:
                cliente = Cliente.query.get(form.cliente_id.data)
            else:
                # Crea nuovo cliente
                telefono_pulito = pulisci_telefono(form.telefono.data)
                
                # Verifica se il telefono esiste già
                cliente_esistente = Cliente.query.filter_by(telefono=telefono_pulito).first()
                if cliente_esistente:
                    flash('Esiste già un cliente con questo numero di telefono', 'error')
                    return render_template('abbonamenti/nuovo.html', form=form)
                
                cliente_data = {
                    'nome': form.nome.data.strip().title(),
                    'cognome': form.cognome.data.strip().title(),
                    'telefono': telefono_pulito,
                    'email': form.email.data.strip().lower() if form.email.data else None
                }
                
                # Aggiungi tipo_cliente solo se il modello lo supporta
                if hasattr(Cliente, 'tipo_cliente'):
                    cliente_data['tipo_cliente'] = form.tipo_cliente.data
                
                cliente = Cliente(**cliente_data)
                db.session.add(cliente)
                db.session.flush()  # Per ottenere l'ID
            
            # Verifica targa univoca per abbonamenti attivi
            targa_pulita = pulisci_targa(form.targa.data)
            abbonamento_esistente = Abbonamento.query.filter(
                and_(
                    Abbonamento.targa == targa_pulita,
                    Abbonamento.attivo == True,
                    Abbonamento.data_fine >= datetime.now().date()
                )
            ).first()
            
            if abbonamento_esistente:
                flash('Esiste già un abbonamento attivo per questa targa', 'error')
                return render_template('abbonamenti/nuovo.html', form=form)
            
            # Crea abbonamento
            abbonamento = Abbonamento(
                cliente_id=cliente.id,
                targa=targa_pulita,
                data_inizio=datetime.now().date(),  # Imposta esplicitamente la data di inizio
                tipo_abbonamento=form.tipo_abbonamento.data,
                accessi_totali=form.accessi_totali.data,
                prezzo=form.prezzo.data,
                stato_pagamento=form.stato_pagamento.data,
                codice_nfc=form.codice_nfc.data.upper() if form.codice_nfc.data else None
            )
            
            # Calcola data fine
            abbonamento.calcola_data_fine()
            
            db.session.add(abbonamento)
            db.session.commit()
            
            flash(f'Abbonamento creato per {cliente.nome_completo} - Codice NFC: {abbonamento.codice_nfc}', 'success')
            return redirect(url_for('abbonamenti.dettaglio', id=abbonamento.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
    return render_template('abbonamenti/nuovo.html', form=form)

@abbonamenti_bp.route('/<int:id>')
@login_required
def dettaglio(id):
    """Dettaglio abbonamento"""
    
    abbonamento = Abbonamento.query.get_or_404(id)
    
    # Ultimi accessi
    accessi = abbonamento.accessi[-10:]  # Ultimi 10 accessi
    
    return render_template('abbonamenti/dettaglio.html',
                         abbonamento=abbonamento,
                         accessi=accessi)

@abbonamenti_bp.route('/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica(id):
    """Modifica abbonamento"""
    
    abbonamento = Abbonamento.query.get_or_404(id)
    
    # Popola select clienti
    clienti = Cliente.query.filter_by(attivo=True).order_by(Cliente.cognome, Cliente.nome).all()
    
    if request.method == 'GET':
        # Pre-popola form con dati esistenti
        form = AbbonamentoForm(obj=abbonamento)
        form.cliente_id.choices = [(0, 'Nuovo Cliente')] + [(c.id, f"{c.nome_completo} - {c.telefono}") for c in clienti]
        form.nome.data = abbonamento.cliente.nome
        form.cognome.data = abbonamento.cliente.cognome
        form.telefono.data = abbonamento.cliente.telefono
        form.email.data = abbonamento.cliente.email
        form.tipo_cliente.data = getattr(abbonamento.cliente, 'tipo_cliente', 'privato')
        form.cliente_id.data = 0  # Non usare cliente esistente
    else:
        form = AbbonamentoForm()
        form.cliente_id.choices = [(0, 'Nuovo Cliente')] + [(c.id, f"{c.nome_completo} - {c.telefono}") for c in clienti]
    
    if form.validate_on_submit():
        try:
            # Aggiorna cliente
            if form.nome.data and form.cognome.data:
                abbonamento.cliente.nome = form.nome.data.strip().title()
                abbonamento.cliente.cognome = form.cognome.data.strip().title()
                if form.telefono.data:
                    telefono_pulito = pulisci_telefono(form.telefono.data)
                    # Verifica univocità telefono (escludendo cliente corrente)
                    cliente_esistente = Cliente.query.filter(
                        and_(Cliente.telefono == telefono_pulito, Cliente.id != abbonamento.cliente.id)
                    ).first()
                    if cliente_esistente:
                        flash('Esiste già un cliente con questo numero di telefono', 'error')
                        return render_template('abbonamenti/modifica.html', form=form, abbonamento=abbonamento)
                    abbonamento.cliente.telefono = telefono_pulito
                if form.email.data:
                    abbonamento.cliente.email = form.email.data.strip().lower()
                if form.tipo_cliente.data and hasattr(abbonamento.cliente, 'tipo_cliente'):
                    abbonamento.cliente.tipo_cliente = form.tipo_cliente.data
            
            # Aggiorna abbonamento
            if form.targa.data:
                targa_pulita = pulisci_targa(form.targa.data)
                # Verifica univocità targa (escludendo abbonamento corrente)
                abbonamento_esistente = Abbonamento.query.filter(
                    and_(
                        Abbonamento.targa == targa_pulita,
                        Abbonamento.attivo == True,
                        Abbonamento.data_fine >= datetime.now().date(),
                        Abbonamento.id != abbonamento.id
                    )
                ).first()
                if abbonamento_esistente:
                    flash('Esiste già un abbonamento attivo per questa targa', 'error')
                    return render_template('abbonamenti/modifica.html', form=form, abbonamento=abbonamento)
                abbonamento.targa = targa_pulita
            
            abbonamento.tipo_abbonamento = form.tipo_abbonamento.data
            abbonamento.accessi_totali = form.accessi_totali.data
            abbonamento.prezzo = form.prezzo.data
            abbonamento.stato_pagamento = form.stato_pagamento.data
            
            if form.codice_nfc.data:
                abbonamento.codice_nfc = form.codice_nfc.data.upper()
            
            # Ricalcola data fine se cambiato tipo
            abbonamento.calcola_data_fine()
            
            db.session.commit()
            flash('Abbonamento aggiornato con successo', 'success')
            return redirect(url_for('abbonamenti.dettaglio', id=abbonamento.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('abbonamenti/modifica.html', form=form, abbonamento=abbonamento)

@abbonamenti_bp.route('/<int:id>/rinnova', methods=['POST'])
@login_required
def rinnova(id):
    """Rinnova abbonamento"""
    
    abbonamento = Abbonamento.query.get_or_404(id)
    
    try:
        # Estendi la data di fine
        if abbonamento.tipo_abbonamento == 'mensile':
            abbonamento.data_fine += timedelta(days=30)
        elif abbonamento.tipo_abbonamento == 'trimestrale':
            abbonamento.data_fine += timedelta(days=90)
        elif abbonamento.tipo_abbonamento == 'annuale':
            abbonamento.data_fine += timedelta(days=365)
        
        # Reset accessi utilizzati
        abbonamento.accessi_utilizzati = 0
        abbonamento.stato_pagamento = 'non_pagato'
        
        db.session.commit()
        flash('Abbonamento rinnovato con successo', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante il rinnovo: {str(e)}', 'error')
    
    return redirect(url_for('abbonamenti.dettaglio', id=id))

@abbonamenti_bp.route('/<int:id>/elimina', methods=['POST'])
@login_required
def elimina(id):
    """Elimina abbonamento"""
    
    abbonamento = Abbonamento.query.get_or_404(id)
    
    try:
        # Prima elimina tutti gli accessi collegati
        from models import Accesso
        Accesso.query.filter_by(abbonamento_id=id).delete()
        
        # Poi elimina l'abbonamento
        db.session.delete(abbonamento)
        db.session.commit()
        flash('Abbonamento eliminato', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('abbonamenti.index'))

@abbonamenti_bp.route('/api/cliente/<telefono>')
@login_required
def api_cliente_by_telefono(telefono):
    """API per ottenere cliente da numero di telefono"""
    
    telefono_pulito = pulisci_telefono(telefono)
    cliente = Cliente.query.filter_by(telefono=telefono_pulito).first()
    
    if cliente:
        return jsonify({
            'found': True,
            'cliente': {
                'id': cliente.id,
                'nome': cliente.nome,
                'cognome': cliente.cognome,
                'telefono': cliente.telefono,
                'email': cliente.email or ''
            }
        })
    else:
        return jsonify({'found': False})

@abbonamenti_bp.route('/nfc/<codice_nfc>')
def nfc_page(codice_nfc):
    """Pagina dedicata abbonamento tramite scansione NFC"""
    
    # Cerca abbonamento per codice NFC
    abbonamento = Abbonamento.query.filter_by(
        codice_nfc=codice_nfc.upper(),
        attivo=True
    ).first()
    
    if not abbonamento:
        return render_template('abbonamenti/nfc_non_trovato.html', 
                             codice_nfc=codice_nfc)
    
    # Determina stato specifico dell'abbonamento
    stato_ok = True
    stato_tipo = 'attivo'
    stato_messaggio = 'Abbonamento Attivo'
    motivo_blocco = None
    
    # Verifica limite giornaliero per clienti privati
    tipo_cliente = getattr(abbonamento.cliente, 'tipo_cliente', 'privato')
    ha_accesso_oggi = abbonamento.cliente.ha_accesso_oggi() if tipo_cliente == 'privato' else False
    
    # Controlli di stato in ordine di priorità
    if abbonamento.is_scaduto:
        stato_ok = False
        stato_tipo = 'scaduto'
        stato_messaggio = 'Abbonamento Scaduto'
        motivo_blocco = f"Scaduto il {abbonamento.data_fine.strftime('%d/%m/%Y')}"
    elif abbonamento.accessi_rimanenti == 0:
        stato_ok = False
        stato_tipo = 'esaurito'
        stato_messaggio = 'Accessi Esauriti'
        motivo_blocco = "Numero di accessi terminato"
    elif ha_accesso_oggi:
        stato_ok = False
        stato_tipo = 'limite_giornaliero'
        stato_messaggio = 'Limite Giornaliero Raggiunto'
        motivo_blocco = "Cliente privato: già un accesso oggi"
    elif abbonamento.stato_pagamento != 'pagato':
        stato_ok = False
        stato_tipo = 'non_pagato'
        stato_messaggio = 'Pagamento in Sospeso'
        motivo_blocco = "Abbonamento non ancora pagato"
    
    # Messaggi di avviso aggiuntivi
    messaggi = []
    if stato_ok:
        if abbonamento.is_in_scadenza:
            messaggi.append(f"⚠️ Abbonamento in scadenza tra {abbonamento.giorni_alla_scadenza} giorni")
        if abbonamento.accessi_rimanenti <= 2:
            messaggi.append(f"⚠️ Rimangono solo {abbonamento.accessi_rimanenti} accessi")
        if tipo_cliente == 'privato':
            messaggi.append("ℹ️ Cliente privato: limite 1 accesso/giorno")
    
    # Ultimi accessi per la timeline
    accessi_recenti = abbonamento.accessi[-5:]  # Ultimi 5 accessi
    
    return render_template('abbonamenti/nfc_page.html',
                         abbonamento=abbonamento,
                         stato_ok=stato_ok,
                         stato_tipo=stato_tipo,
                         stato_messaggio=stato_messaggio,
                         motivo_blocco=motivo_blocco,
                         messaggi=messaggi,
                         accessi_recenti=accessi_recenti)

@abbonamenti_bp.route('/targa/<targa>')
def targa_page(targa):
    """Pagina dedicata abbonamento tramite ricerca targa"""
    
    # Cerca abbonamento per targa
    abbonamento = Abbonamento.query.filter_by(
        targa=targa.upper(),
        attivo=True
    ).filter(
        Abbonamento.data_fine >= datetime.now().date()
    ).first()
    
    if not abbonamento:
        return render_template('abbonamenti/targa_non_trovata.html', 
                             targa=targa.upper())
    
    # Calcola stato abbonamento
    stato_ok = not abbonamento.is_scaduto and abbonamento.accessi_rimanenti > 0
    
    # Messaggi di avviso
    messaggi = []
    if abbonamento.is_scaduto:
        messaggi.append(f"⚠️ Abbonamento scaduto il {abbonamento.data_fine.strftime('%d/%m/%Y')}")
    elif abbonamento.is_in_scadenza:
        messaggi.append(f"⚠️ Abbonamento in scadenza tra {abbonamento.giorni_alla_scadenza} giorni")
    
    if abbonamento.accessi_rimanenti <= 2 and abbonamento.accessi_rimanenti > 0:
        messaggi.append(f"⚠️ Rimangono solo {abbonamento.accessi_rimanenti} accessi")
    elif abbonamento.accessi_rimanenti == 0:
        messaggi.append("❌ Accessi esauriti")
    
    if abbonamento.stato_pagamento != 'pagato':
        messaggi.append("💰 Pagamento in sospeso")
    
    # Ultimi accessi per la timeline
    accessi_recenti = abbonamento.accessi[-5:]  # Ultimi 5 accessi
    
    return render_template('abbonamenti/targa_page.html',
                         abbonamento=abbonamento,
                         stato_ok=stato_ok,
                         messaggi=messaggi,
                         accessi_recenti=accessi_recenti,
                         ricerca_targa=targa.upper())

@abbonamenti_bp.route('/guida-nfc')
@login_required
def guida_nfc():
    """Guida per la programmazione dei tag NFC"""
    return render_template('abbonamenti/guida_nfc.html')

