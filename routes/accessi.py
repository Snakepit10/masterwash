from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from models import db, Abbonamento, Accesso, Cliente

accessi_bp = Blueprint('accessi', __name__)

class VerificaAccessoForm(FlaskForm):
    """Form per verifica e registrazione accesso"""
    codice_nfc = StringField('Codice NFC', validators=[
        DataRequired(message='Inserisci il codice NFC'),
        Length(min=8, max=8, message='Il codice NFC deve essere di 8 caratteri')
    ])
    submit = SubmitField('Verifica')

class RegistraAccessoForm(FlaskForm):
    """Form per registrare l'accesso"""
    abbonamento_id = StringField('ID Abbonamento', validators=[DataRequired()])
    note = TextAreaField('Note (facoltativo)', validators=[
        Optional(),
        Length(max=500, message='Le note non possono superare i 500 caratteri')
    ])
    submit = SubmitField('Registra Accesso')

@accessi_bp.route('/')
@login_required
def index():
    """Pagina principale verifica accessi"""
    
    form = VerificaAccessoForm()
    return render_template('accessi/index.html', form=form)

@accessi_bp.route('/verifica', methods=['POST'])
@login_required
def verifica():
    """Verifica codice NFC e mostra dettagli abbonamento"""
    
    form = VerificaAccessoForm()
    
    if form.validate_on_submit():
        codice_nfc = form.codice_nfc.data.upper().strip()
        
        # Cerca abbonamento per codice NFC
        abbonamento = Abbonamento.query.filter_by(
            codice_nfc=codice_nfc,
            attivo=True
        ).first()
        
        if not abbonamento:
            flash('Codice NFC non trovato o abbonamento non attivo', 'error')
            return render_template('accessi/index.html', form=form)
        
        # Verifica stato abbonamento
        stato_ok = True
        messaggi = []
        
        if abbonamento.is_scaduto:
            stato_ok = False
            messaggi.append(f'Abbonamento scaduto il {abbonamento.data_fine.strftime("%d/%m/%Y")}')
        
        if abbonamento.accessi_rimanenti == 0:
            stato_ok = False
            messaggi.append('Accessi esauriti')
        
        if abbonamento.is_in_scadenza and stato_ok:
            messaggi.append(f'Attenzione: abbonamento in scadenza ({abbonamento.giorni_alla_scadenza} giorni)')
        
        if abbonamento.accessi_rimanenti <= 2 and abbonamento.accessi_rimanenti > 0:
            messaggi.append(f'Attenzione: rimangono solo {abbonamento.accessi_rimanenti} accessi')
        
        # Form per registrare accesso
        registra_form = RegistraAccessoForm()
        registra_form.abbonamento_id.data = str(abbonamento.id)
        
        return render_template('accessi/verifica.html',
                             abbonamento=abbonamento,
                             stato_ok=stato_ok,
                             messaggi=messaggi,
                             registra_form=registra_form,
                             form=form)
    
    # Se form non valido, ritorna alla pagina principale
    return render_template('accessi/index.html', form=form)

@accessi_bp.route('/registra', methods=['POST'])
@login_required
def registra():
    """Registra un nuovo accesso"""
    
    form = RegistraAccessoForm()
    
    if form.validate_on_submit():
        try:
            abbonamento_id = int(form.abbonamento_id.data)
            abbonamento = Abbonamento.query.get_or_404(abbonamento_id)
            
            # Verifica che l'abbonamento possa essere utilizzato
            if abbonamento.is_scaduto:
                flash('Impossibile registrare accesso: abbonamento scaduto', 'error')
                return redirect(url_for('accessi.index'))
            
            if abbonamento.accessi_rimanenti == 0:
                flash('Impossibile registrare accesso: accessi esauriti', 'error')
                return redirect(url_for('accessi.index'))
            
            # Registra l'accesso
            accesso = abbonamento.registra_accesso(
                operatore_id=current_user.id,
                note=form.note.data.strip() if form.note.data else None
            )
            
            if accesso:
                flash(f'Accesso registrato per {abbonamento.cliente.nome_completo} - Accessi rimanenti: {abbonamento.accessi_rimanenti}', 'success')
                
                # Se è l'ultimo accesso o in scadenza, mostra avviso
                if abbonamento.accessi_rimanenti == 0:
                    flash('Attenzione: accessi esauriti! Necessario rinnovo.', 'warning')
                elif abbonamento.accessi_rimanenti <= 2:
                    flash(f'Attenzione: rimangono solo {abbonamento.accessi_rimanenti} accessi', 'info')
            else:
                # Verifica perché l'accesso è stato rifiutato
                if abbonamento.accessi_rimanenti <= 0:
                    flash('Accesso negato: accessi esauriti!', 'error')
                elif abbonamento.is_scaduto:
                    flash('Accesso negato: abbonamento scaduto!', 'error')
                elif getattr(abbonamento.cliente, 'tipo_cliente', 'privato') == 'privato' and abbonamento.cliente.ha_accesso_oggi():
                    flash('Accesso negato: cliente privato ha già effettuato un accesso oggi!', 'warning')
                else:
                    flash('Errore durante la registrazione dell\'accesso', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la registrazione: {str(e)}', 'error')
    
    return redirect(url_for('accessi.index'))

@accessi_bp.route('/storico')
@login_required
def storico():
    """Storico accessi con filtri"""
    
    # Parametri di ricerca
    search = request.args.get('search', '').strip()
    data_da = request.args.get('data_da', '')
    data_a = request.args.get('data_a', '')
    operatore_id = request.args.get('operatore_id', '', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Query base
    query = Accesso.query.join(
        Abbonamento, Accesso.abbonamento_id == Abbonamento.id
    ).join(
        Cliente, Abbonamento.cliente_id == Cliente.id
    )
    
    # Filtro per ricerca
    if search:
        query = query.filter(
            or_(
                Cliente.nome.ilike(f'%{search}%'),
                Cliente.cognome.ilike(f'%{search}%'),
                Abbonamento.targa.ilike(f'%{search}%'),
                Abbonamento.codice_nfc.ilike(f'%{search}%')
            )
        )
    
    # Filtro per data
    if data_da:
        try:
            data_da_obj = datetime.strptime(data_da, '%Y-%m-%d').date()
            query = query.filter(func.date(Accesso.data_ora) >= data_da_obj)
        except ValueError:
            pass
    
    if data_a:
        try:
            data_a_obj = datetime.strptime(data_a, '%Y-%m-%d').date()
            query = query.filter(func.date(Accesso.data_ora) <= data_a_obj)
        except ValueError:
            pass
    
    # Filtro per operatore
    if operatore_id:
        query = query.filter(Accesso.operatore_id == operatore_id)
    
    # Ordinamento
    query = query.order_by(Accesso.data_ora.desc())
    
    # Paginazione
    accessi = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Lista operatori per filtro
    from models import Operatore
    operatori = Operatore.query.filter_by(attivo=True).order_by(Operatore.nome).all()
    
    return render_template('accessi/storico.html',
                         accessi=accessi,
                         operatori=operatori,
                         search=search,
                         data_da=data_da,
                         data_a=data_a,
                         operatore_id=operatore_id)

@accessi_bp.route('/api/verifica-nfc')
@login_required
def api_verifica_nfc():
    """API per verifica rapida codice NFC"""
    
    codice_nfc = request.args.get('codice', '').upper().strip()
    
    if not codice_nfc or len(codice_nfc) != 8:
        return jsonify({
            'success': False,
            'message': 'Codice NFC non valido'
        })
    
    # Cerca abbonamento
    abbonamento = Abbonamento.query.filter_by(
        codice_nfc=codice_nfc,
        attivo=True
    ).first()
    
    if not abbonamento:
        return jsonify({
            'success': False,
            'message': 'Codice NFC non trovato'
        })
    
    # Prepara dati risposta
    data = {
        'success': True,
        'abbonamento': {
            'id': abbonamento.id,
            'cliente': abbonamento.cliente.nome_completo,
            'targa': abbonamento.targa,
            'accessi_rimanenti': abbonamento.accessi_rimanenti,
            'giorni_scadenza': abbonamento.giorni_alla_scadenza,
            'is_scaduto': abbonamento.is_scaduto,
            'is_in_scadenza': abbonamento.is_in_scadenza,
            'colore_accessi': abbonamento.colore_accessi,
            'ultimo_accesso': None
        }
    }
    
    # Ultimo accesso
    if abbonamento.ultimo_accesso:
        data['abbonamento']['ultimo_accesso'] = {
            'data_ora': abbonamento.ultimo_accesso.data_ora.strftime('%d/%m/%Y %H:%M'),
            'operatore': abbonamento.ultimo_accesso.operatore.nome
        }
    
    # Messaggi di stato
    messaggi = []
    if abbonamento.is_scaduto:
        messaggi.append('Abbonamento scaduto')
        data['success'] = False
    elif abbonamento.accessi_rimanenti == 0:
        messaggi.append('Accessi esauriti')
        data['success'] = False
    else:
        if abbonamento.is_in_scadenza:
            messaggi.append(f'In scadenza tra {abbonamento.giorni_alla_scadenza} giorni')
        if abbonamento.accessi_rimanenti <= 2:
            messaggi.append(f'Solo {abbonamento.accessi_rimanenti} accessi rimanenti')
    
    data['messaggi'] = messaggi
    
    return jsonify(data)

@accessi_bp.route('/api/registra-accesso', methods=['POST'])
@login_required
def api_registra_accesso():
    """API per registrare accesso via AJAX"""
    
    data = request.get_json()
    
    if not data or 'abbonamento_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Dati mancanti'
        })
    
    try:
        abbonamento = Abbonamento.query.get(data['abbonamento_id'])
        
        if not abbonamento:
            return jsonify({
                'success': False,
                'message': 'Abbonamento non trovato'
            })
        
        # Verifica stato
        if abbonamento.is_scaduto:
            return jsonify({
                'success': False,
                'message': 'Abbonamento scaduto'
            })
        
        if abbonamento.accessi_rimanenti <= 0:
            return jsonify({
                'success': False,
                'message': 'Accessi esauriti'
            })
        
        # Verifica limite giornaliero per clienti normali
        tipo_cliente = getattr(abbonamento.cliente, 'tipo_cliente', 'normale')
        if tipo_cliente == 'normale' and abbonamento.cliente.ha_accesso_oggi():
            return jsonify({
                'success': False,
                'message': 'Cliente normale: già un accesso oggi'
            })
        
        # Registra accesso
        accesso = abbonamento.registra_accesso(
            operatore_id=current_user.id,
            note=data.get('note', '').strip() or None
        )
        
        if accesso:
            return jsonify({
                'success': True,
                'message': f'Accesso registrato - Rimanenti: {abbonamento.accessi_rimanenti}',
                'accessi_rimanenti': abbonamento.accessi_rimanenti
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Errore durante la registrazione'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Errore: {str(e)}'
        })

@accessi_bp.route('/rapido')
@login_required
def rapido():
    """Pagina per accesso rapido (solo input NFC)"""
    return render_template('accessi/rapido.html')

@accessi_bp.route('/api/verifica-unified')
@login_required
def api_verifica_unified():
    """API unificata per verifica tramite NFC o targa"""
    
    nfc_code = request.args.get('nfc', '').upper().strip()
    targa = request.args.get('targa', '').upper().strip()
    
    abbonamento = None
    search_type = None
    search_value = None
    
    # Cerca per codice NFC
    if nfc_code:
        if len(nfc_code) != 8:
            return jsonify({
                'success': False,
                'message': 'Codice NFC non valido (deve essere di 8 caratteri)',
                'search_type': 'nfc',
                'search_value': nfc_code
            })
        
        abbonamento = Abbonamento.query.filter_by(
            codice_nfc=nfc_code,
            attivo=True
        ).first()
        search_type = 'nfc'
        search_value = nfc_code
        
    # Cerca per targa
    elif targa:
        if len(targa) < 5:
            return jsonify({
                'success': False,
                'message': 'Targa non valida (minimo 5 caratteri)',
                'search_type': 'targa',
                'search_value': targa
            })
        
        abbonamento = Abbonamento.query.filter_by(
            targa=targa,
            attivo=True
        ).filter(
            Abbonamento.data_fine >= datetime.now().date()
        ).first()
        search_type = 'targa'
        search_value = targa
        
    else:
        return jsonify({
            'success': False,
            'message': 'Specificare codice NFC o targa'
        })
    
    if not abbonamento:
        message = f"{'Codice NFC' if search_type == 'nfc' else 'Targa'} non trovato"
        return jsonify({
            'success': False,
            'message': message,
            'search_type': search_type,
            'search_value': search_value
        })
    
    # Verifica stato
    stato_ok = not abbonamento.is_scaduto and abbonamento.accessi_rimanenti > 0
    
    # Messaggi di avviso
    messaggi = []
    if abbonamento.is_scaduto:
        messaggi.append(f"Abbonamento scaduto il {abbonamento.data_fine.strftime('%d/%m/%Y')}")
    elif abbonamento.is_in_scadenza:
        messaggi.append(f"In scadenza tra {abbonamento.giorni_alla_scadenza} giorni")
    
    if abbonamento.accessi_rimanenti <= 2 and abbonamento.accessi_rimanenti > 0:
        messaggi.append(f"Rimangono solo {abbonamento.accessi_rimanenti} accessi")
    elif abbonamento.accessi_rimanenti == 0:
        messaggi.append("Accessi esauriti")
    
    if abbonamento.stato_pagamento != 'pagato':
        messaggi.append("Pagamento in sospeso")
    
    return jsonify({
        'success': True,
        'stato_ok': stato_ok,
        'messaggi': messaggi,
        'search_type': search_type,
        'search_value': search_value,
        'abbonamento': {
            'id': abbonamento.id,
            'cliente': abbonamento.cliente.nome_completo,
            'targa': abbonamento.targa,
            'codice_nfc': abbonamento.codice_nfc,
            'tipo_abbonamento': abbonamento.tipo_abbonamento,
            'accessi_rimanenti': abbonamento.accessi_rimanenti,
            'accessi_totali': abbonamento.accessi_totali,
            'accessi_utilizzati': abbonamento.accessi_utilizzati,
            'giorni_scadenza': abbonamento.giorni_alla_scadenza,
            'is_scaduto': abbonamento.is_scaduto,
            'is_in_scadenza': abbonamento.is_in_scadenza,
            'colore_accessi': abbonamento.colore_accessi,
            'ultimo_accesso': {
                'data_ora': abbonamento.ultimo_accesso.data_ora.strftime('%d/%m/%Y %H:%M')
            } if abbonamento.ultimo_accesso else None
        }
    })