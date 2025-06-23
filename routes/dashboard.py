from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from models import db, Cliente, Abbonamento, Accesso, Operatore

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Dashboard principale con statistiche"""
    
    # Statistiche generali
    today = datetime.now().date()
    this_month_start = today.replace(day=1)
    this_week_start = today - timedelta(days=today.weekday())
    
    # Contatori principali
    stats = {
        'abbonamenti_attivi': Abbonamento.query.filter(
            and_(Abbonamento.attivo == True, Abbonamento.data_fine >= today)
        ).count(),
        
        'abbonamenti_scaduti': Abbonamento.query.filter(
            and_(Abbonamento.attivo == True, Abbonamento.data_fine < today)
        ).count(),
        
        'abbonamenti_in_scadenza': Abbonamento.query.filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.data_fine >= today,
                Abbonamento.data_fine <= today + timedelta(days=7)
            )
        ).count(),
        
        'nuovi_abbonamenti_mese': Abbonamento.query.filter(
            Abbonamento.data_creazione >= this_month_start
        ).count(),
        
        'accessi_oggi': Accesso.query.filter(
            func.date(Accesso.data_ora) == today
        ).count(),
        
        'accessi_settimana': Accesso.query.filter(
            func.date(Accesso.data_ora) >= this_week_start
        ).count(),
        
        'accessi_mese': Accesso.query.filter(
            func.date(Accesso.data_ora) >= this_month_start
        ).count(),
        
        'clienti_totali': Cliente.query.filter_by(attivo=True).count()
    }
    
    # Abbonamenti in scadenza (prossimi 7 giorni)
    abbonamenti_scadenza = Abbonamento.query.filter(
        and_(
            Abbonamento.attivo == True,
            Abbonamento.data_fine >= today,
            Abbonamento.data_fine <= today + timedelta(days=7)
        )
    ).order_by(Abbonamento.data_fine.asc()).limit(10).all()
    
    # Ultimi accessi
    ultimi_accessi = Accesso.query.join(Abbonamento).join(Cliente).order_by(
        Accesso.data_ora.desc()
    ).limit(10).all()
    
    # Top clienti per numero accessi (ultimo mese)
    top_clienti = db.session.query(
        Cliente.nome,
        Cliente.cognome,
        func.count(Accesso.id).label('accessi_count')
    ).join(Abbonamento).join(Accesso).filter(
        Accesso.data_ora >= this_month_start
    ).group_by(Cliente.id, Cliente.nome, Cliente.cognome).order_by(
        func.count(Accesso.id).desc()
    ).limit(10).all()
    
    return render_template('dashboard/index.html', 
                         stats=stats,
                         abbonamenti_scadenza=abbonamenti_scadenza,
                         ultimi_accessi=ultimi_accessi,
                         top_clienti=top_clienti)

@dashboard_bp.route('/api/accessi-orari')
@login_required
def api_accessi_orari():
    """API per i dati del grafico accessi per fascia oraria"""
    
    # Ultimi 7 giorni
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Query per accessi raggruppati per ora
    accessi_orari = db.session.query(
        func.extract('hour', Accesso.data_ora).label('ora'),
        func.count(Accesso.id).label('accessi')
    ).filter(
        func.date(Accesso.data_ora) >= week_ago
    ).group_by(
        func.extract('hour', Accesso.data_ora)
    ).order_by('ora').all()
    
    # Prepara dati per Chart.js
    ore = list(range(24))
    accessi = [0] * 24
    
    for ora, count in accessi_orari:
        accessi[int(ora)] = count
    
    return jsonify({
        'labels': [f"{ora:02d}:00" for ora in ore],
        'data': accessi
    })

@dashboard_bp.route('/api/abbonamenti-mensili')
@login_required
def api_abbonamenti_mensili():
    """API per i dati del grafico abbonamenti mensili"""
    
    # Ultimi 12 mesi
    today = datetime.now().date()
    
    mesi_dati = []
    for i in range(12):
        if i == 0:
            mese_start = today.replace(day=1)
            mese_end = today
        else:
            mese_corrente = today.replace(day=1) - timedelta(days=i*30)
            mese_start = mese_corrente.replace(day=1)
            # Ultimo giorno del mese
            if mese_corrente.month == 12:
                mese_end = mese_corrente.replace(year=mese_corrente.year+1, month=1, day=1) - timedelta(days=1)
            else:
                mese_end = mese_corrente.replace(month=mese_corrente.month+1, day=1) - timedelta(days=1)
        
        count = Abbonamento.query.filter(
            and_(
                Abbonamento.data_creazione >= mese_start,
                Abbonamento.data_creazione <= mese_end
            )
        ).count()
        
        mesi_dati.append({
            'mese': mese_start.strftime('%b %Y'),
            'count': count
        })
    
    # Inverti per avere ordine cronologico
    mesi_dati.reverse()
    
    return jsonify({
        'labels': [m['mese'] for m in mesi_dati],
        'data': [m['count'] for m in mesi_dati]
    })

@dashboard_bp.route('/api/stats-realtime')
@login_required
def api_stats_realtime():
    """API per statistiche in tempo reale"""
    
    today = datetime.now().date()
    
    # Statistiche aggiornate
    stats = {
        'accessi_oggi': Accesso.query.filter(
            func.date(Accesso.data_ora) == today
        ).count(),
        
        'abbonamenti_attivi': Abbonamento.query.filter(
            and_(Abbonamento.attivo == True, Abbonamento.data_fine >= today)
        ).count(),
        
        'ultimo_accesso': None
    }
    
    # Ultimo accesso
    ultimo_accesso = Accesso.query.join(Abbonamento).join(Cliente).order_by(
        Accesso.data_ora.desc()
    ).first()
    
    if ultimo_accesso:
        stats['ultimo_accesso'] = {
            'cliente': ultimo_accesso.abbonamento.cliente.nome_completo,
            'targa': ultimo_accesso.abbonamento.targa,
            'data_ora': ultimo_accesso.data_ora.strftime('%H:%M')
        }
    
    return jsonify(stats)