from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from functools import wraps
from sqlalchemy import func, text
from datetime import datetime, timedelta
from models import db, Operatore, Cliente, Abbonamento, Accesso, ImpostazioniStampante

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decoratore per richiedere privilegi admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Accesso negato. Sono richiesti privilegi di amministratore.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

class OperatoreForm(FlaskForm):
    """Form per gestione operatori"""
    username = StringField('Username', validators=[
        DataRequired(message='Inserisci username'),
        Length(min=3, max=50, message='Username tra 3 e 50 caratteri')
    ])
    nome = StringField('Nome', validators=[
        DataRequired(message='Inserisci nome'),
        Length(min=2, max=100, message='Nome tra 2 e 100 caratteri')
    ])
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=6, message='Password minimo 6 caratteri')
    ])
    ruolo = SelectField('Ruolo', choices=[
        ('operatore', 'Operatore'),
        ('admin', 'Amministratore')
    ], default='operatore')
    attivo = BooleanField('Attivo', default=True)
    submit = SubmitField('Salva')

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Dashboard amministrazione"""
    
    # Statistiche generali
    stats = {
        'operatori_totali': Operatore.query.count(),
        'operatori_attivi': Operatore.query.filter_by(attivo=True).count(),
        'clienti_totali': Cliente.query.count(),
        'clienti_attivi': Cliente.query.filter_by(attivo=True).count(),
        'abbonamenti_attivi': Abbonamento.query.filter_by(attivo=True).count(),
        'accessi_oggi': Accesso.query.filter(
            func.date(Accesso.data_ora) == datetime.now().date()
        ).count(),
        'accessi_mese': Accesso.query.filter(
            Accesso.data_ora >= datetime.now().replace(day=1)
        ).count()
    }
    
    # Statistiche clienti per tipo
    try:
        stats['clienti_privati'] = Cliente.query.filter_by(tipo_cliente='privato').count()
        stats['clienti_business'] = Cliente.query.filter_by(tipo_cliente='business').count()
    except:
        stats['clienti_privati'] = 0
        stats['clienti_business'] = 0
    
    # Ultimi operatori
    operatori_recenti = Operatore.query.order_by(Operatore.data_creazione.desc()).limit(5).all()
    
    # Ultimi accessi
    accessi_recenti = Accesso.query.join(Abbonamento).join(Cliente).order_by(
        Accesso.data_ora.desc()
    ).limit(10).all()
    
    return render_template('admin/index.html',
                         stats=stats,
                         operatori_recenti=operatori_recenti,
                         accessi_recenti=accessi_recenti)

@admin_bp.route('/operatori')
@login_required
@admin_required
def operatori():
    """Gestione operatori"""
    
    # Parametri ricerca
    search = request.args.get('search', '').strip()
    filtro = request.args.get('filtro', 'tutti')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query base
    query = Operatore.query
    
    # Filtro ricerca
    if search:
        query = query.filter(
            Operatore.nome.ilike(f'%{search}%') |
            Operatore.username.ilike(f'%{search}%')
        )
    
    # Filtro stato
    if filtro == 'attivi':
        query = query.filter_by(attivo=True)
    elif filtro == 'inattivi':
        query = query.filter_by(attivo=False)
    elif filtro == 'admin':
        query = query.filter_by(ruolo='admin')
    
    # Ordinamento e paginazione
    query = query.order_by(Operatore.data_creazione.desc())
    operatori = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/operatori.html',
                         operatori=operatori,
                         search=search,
                         filtro=filtro)

@admin_bp.route('/operatori/nuovo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuovo_operatore():
    """Crea nuovo operatore"""
    
    form = OperatoreForm()
    
    if form.validate_on_submit():
        try:
            # Verifica username univoco
            if Operatore.query.filter_by(username=form.username.data).first():
                flash('Username già esistente', 'error')
                return render_template('admin/operatore_form.html', form=form, titolo='Nuovo Operatore')
            
            operatore = Operatore(
                username=form.username.data,
                nome=form.nome.data,
                ruolo=form.ruolo.data,
                attivo=form.attivo.data
            )
            
            if form.password.data:
                operatore.set_password(form.password.data)
            else:
                operatore.set_password('password123')  # Password default
            
            db.session.add(operatore)
            db.session.commit()
            
            flash(f'Operatore {operatore.nome} creato con successo', 'success')
            return redirect(url_for('admin.operatori'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante la creazione: {str(e)}', 'error')
    
    return render_template('admin/operatore_form.html', form=form, titolo='Nuovo Operatore')

@admin_bp.route('/operatori/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
@admin_required
def modifica_operatore(id):
    """Modifica operatore"""
    
    operatore = Operatore.query.get_or_404(id)
    
    if request.method == 'GET':
        form = OperatoreForm(obj=operatore)
    else:
        form = OperatoreForm()
    
    if form.validate_on_submit():
        try:
            # Verifica username univoco (escludendo l'operatore corrente)
            existing = Operatore.query.filter(
                Operatore.username == form.username.data,
                Operatore.id != id
            ).first()
            if existing:
                flash('Username già esistente', 'error')
                return render_template('admin/operatore_form.html', form=form, operatore=operatore, titolo='Modifica Operatore')
            
            operatore.username = form.username.data
            operatore.nome = form.nome.data
            operatore.ruolo = form.ruolo.data
            operatore.attivo = form.attivo.data
            
            if form.password.data:
                operatore.set_password(form.password.data)
            
            db.session.commit()
            flash(f'Operatore {operatore.nome} aggiornato', 'success')
            return redirect(url_for('admin.operatori'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'aggiornamento: {str(e)}', 'error')
    
    return render_template('admin/operatore_form.html', form=form, operatore=operatore, titolo='Modifica Operatore')

@admin_bp.route('/operatori/<int:id>/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_operatore(id):
    """Elimina operatore"""
    
    operatore = Operatore.query.get_or_404(id)
    
    # Non permettere di eliminare se stesso
    if operatore.id == current_user.id:
        flash('Non puoi eliminare il tuo account', 'error')
        return redirect(url_for('admin.operatori'))
    
    try:
        # Controlla se ha accessi registrati
        accessi_count = Accesso.query.filter_by(operatore_id=id).count()
        if accessi_count > 0:
            # Disattiva invece di eliminare
            operatore.attivo = False
            db.session.commit()
            flash(f'Operatore {operatore.nome} disattivato (ha {accessi_count} accessi registrati)', 'warning')
        else:
            # Elimina definitivamente
            db.session.delete(operatore)
            db.session.commit()
            flash(f'Operatore {operatore.nome} eliminato', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {str(e)}', 'error')
    
    return redirect(url_for('admin.operatori'))

@admin_bp.route('/sistema')
@login_required
@admin_required
def sistema():
    """Informazioni sistema e database"""
    
    try:
        # Informazioni database
        db_info = {}
        
        # Statistiche tabelle
        db_info['clienti'] = Cliente.query.count()
        db_info['abbonamenti'] = Abbonamento.query.count()
        db_info['accessi'] = Accesso.query.count()
        db_info['operatori'] = Operatore.query.count()
        
        # Verifica integrità colonna tipo_cliente
        result = db.session.execute(text("PRAGMA table_info(clienti)"))
        columns = [row[1] for row in result]
        db_info['tipo_cliente_exists'] = 'tipo_cliente' in columns
        
        # Spazio database (se SQLite)
        try:
            import os
            db_file = 'masterwash.db'
            if os.path.exists(db_file):
                db_info['db_size'] = os.path.getsize(db_file)
            else:
                db_info['db_size'] = 0
        except:
            db_info['db_size'] = 0
        
        # Ultimo backup (simulato)
        db_info['ultimo_backup'] = 'Mai'
        
        return render_template('admin/sistema.html', db_info=db_info)
        
    except Exception as e:
        flash(f'Errore nel caricamento informazioni sistema: {str(e)}', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Report e statistiche"""
    
    # Periodo (default ultimo mese)
    periodo = request.args.get('periodo', '30')
    
    try:
        giorni = int(periodo)
        data_inizio = datetime.now() - timedelta(days=giorni)
    except:
        giorni = 30
        data_inizio = datetime.now() - timedelta(days=30)
    
    # Accessi per giorno - genera lista manualmente per avere date complete
    accessi_giornalieri_raw = db.session.query(
        func.date(Accesso.data_ora).label('data'),
        func.count(Accesso.id).label('count')
    ).select_from(Accesso).filter(
        Accesso.data_ora >= data_inizio
    ).group_by(
        func.date(Accesso.data_ora)
    ).order_by(func.date(Accesso.data_ora)).all()
    
    # Converte in formato utilizzabile dal template
    accessi_giornalieri = []
    for accesso_raw in accessi_giornalieri_raw:
        # Converte la stringa data in oggetto datetime
        try:
            if isinstance(accesso_raw.data, str):
                data_obj = datetime.strptime(accesso_raw.data, '%Y-%m-%d').date()
            else:
                data_obj = accesso_raw.data
            
            accessi_giornalieri.append({
                'data': data_obj,
                'count': accesso_raw.count
            })
        except:
            # Se c'è un errore, salta questo record
            continue
    
    # Top clienti
    top_clienti_raw = db.session.query(
        Cliente.id,
        Cliente.nome,
        Cliente.cognome,
        func.count(Accesso.id).label('accessi')
    ).select_from(Cliente).join(
        Abbonamento, Cliente.id == Abbonamento.cliente_id
    ).join(
        Accesso, Abbonamento.id == Accesso.abbonamento_id
    ).filter(
        Accesso.data_ora >= data_inizio
    ).group_by(Cliente.id).order_by(func.count(Accesso.id).desc()).limit(10).all()
    
    # Formatta i nomi completi
    top_clienti = []
    for cliente_raw in top_clienti_raw:
        top_clienti.append({
            'cliente': f"{cliente_raw.nome} {cliente_raw.cognome}",
            'accessi': cliente_raw.accessi
        })
    
    # Operatori più attivi
    top_operatori = db.session.query(
        Operatore.nome.label('operatore'),
        func.count(Accesso.id).label('accessi')
    ).select_from(Operatore).join(
        Accesso, Operatore.id == Accesso.operatore_id
    ).filter(
        Accesso.data_ora >= data_inizio
    ).group_by(Operatore.id).order_by(func.count(Accesso.id).desc()).limit(10).all()
    
    return render_template('admin/reports.html',
                         accessi_giornalieri=accessi_giornalieri,
                         top_clienti=top_clienti,
                         top_operatori=top_operatori,
                         periodo=periodo)