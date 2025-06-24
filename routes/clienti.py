from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from models import db, Cliente, Abbonamento

clienti_bp = Blueprint('clienti', __name__)

@clienti_bp.route('/')
@login_required
def index():
    """Lista clienti con informazioni abbonamenti"""
    
    # Parametri di ricerca e filtri
    search = request.args.get('search', '').strip()
    filtro = request.args.get('filtro', 'tutti')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Query base
    query = Cliente.query.filter_by(attivo=True)
    
    # Filtro per ricerca
    if search:
        query = query.filter(
            or_(
                Cliente.nome.ilike(f'%{search}%'),
                Cliente.cognome.ilike(f'%{search}%'),
                Cliente.telefono.ilike(f'%{search}%'),
                Cliente.email.ilike(f'%{search}%')
            )
        )
    
    # Filtri per stato abbonamenti
    today = datetime.now().date()
    
    if filtro == 'con_abbonamenti_attivi':
        # Clienti con almeno un abbonamento attivo
        query = query.join(Abbonamento).filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.data_fine >= today,
                Abbonamento.accessi_rimanenti > 0
            )
        ).distinct()
    elif filtro == 'con_abbonamenti_scaduti':
        # Clienti con abbonamenti scaduti
        query = query.join(Abbonamento).filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.data_fine < today
            )
        ).distinct()
    elif filtro == 'con_abbonamenti_in_scadenza':
        # Clienti con abbonamenti in scadenza (prossimi 7 giorni)
        query = query.join(Abbonamento).filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.data_fine >= today,
                Abbonamento.data_fine <= today + timedelta(days=7)
            )
        ).distinct()
    elif filtro == 'pagamenti_in_sospeso':
        # Clienti con pagamenti in sospeso
        query = query.join(Abbonamento).filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.stato_pagamento != 'pagato'
            )
        ).distinct()
    elif filtro == 'senza_abbonamenti':
        # Clienti senza abbonamenti attivi
        subquery = db.session.query(Abbonamento.cliente_id).filter(
            and_(
                Abbonamento.attivo == True,
                Abbonamento.data_fine >= today
            )
        ).distinct()
        query = query.filter(~Cliente.id.in_(subquery))
    
    # Ordinamento
    query = query.order_by(Cliente.cognome, Cliente.nome)
    
    # Paginazione
    clienti = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Calcola statistiche per ogni cliente
    clienti_con_stats = []
    for cliente in clienti.items:
        # Abbonamenti attivi
        abbonamenti_attivi = Abbonamento.query.filter(
            and_(
                Abbonamento.cliente_id == cliente.id,
                Abbonamento.attivo == True,
                Abbonamento.data_fine >= today
            )
        ).all()
        
        # Abbonamenti totali (inclusi scaduti)
        abbonamenti_totali = Abbonamento.query.filter(
            and_(
                Abbonamento.cliente_id == cliente.id,
                Abbonamento.attivo == True
            )
        ).count()
        
        # Calcola statistiche
        stats = {
            'abbonamenti_attivi': len(abbonamenti_attivi),
            'abbonamenti_totali': abbonamenti_totali,
            'accessi_totali': sum(a.accessi_utilizzati for a in abbonamenti_attivi),
            'accessi_rimanenti': sum(a.accessi_rimanenti for a in abbonamenti_attivi),
            'importo_dovuto': sum(a.prezzo for a in abbonamenti_attivi if a.stato_pagamento != 'pagato'),
            'abbonamenti_in_scadenza': len([a for a in abbonamenti_attivi if a.is_in_scadenza]),
            'abbonamenti_scaduti': Abbonamento.query.filter(
                and_(
                    Abbonamento.cliente_id == cliente.id,
                    Abbonamento.attivo == True,
                    Abbonamento.data_fine < today
                )
            ).count(),
            'prossima_scadenza': min([a.data_fine for a in abbonamenti_attivi], default=None),
            'abbonamenti_dettaglio': abbonamenti_attivi
        }
        
        clienti_con_stats.append({
            'cliente': cliente,
            'stats': stats
        })
    
    return render_template('clienti/index.html',
                         clienti_paginated=clienti,
                         clienti_con_stats=clienti_con_stats,
                         search=search,
                         filtro=filtro)

@clienti_bp.route('/<int:id>')
@login_required
def dettaglio(id):
    """Dettaglio cliente con tutti i suoi abbonamenti"""
    
    cliente = Cliente.query.get_or_404(id)
    
    # Tutti gli abbonamenti del cliente (attivi e non)
    abbonamenti = Abbonamento.query.filter_by(cliente_id=id).order_by(
        Abbonamento.data_creazione.desc()
    ).all()
    
    # Statistiche generali
    today = datetime.now().date()
    
    abbonamenti_attivi = [a for a in abbonamenti if a.attivo and a.data_fine >= today]
    abbonamenti_scaduti = [a for a in abbonamenti if a.attivo and a.data_fine < today]
    abbonamenti_in_scadenza = [a for a in abbonamenti_attivi if a.is_in_scadenza]
    
    stats = {
        'abbonamenti_totali': len(abbonamenti),
        'abbonamenti_attivi': len(abbonamenti_attivi),
        'abbonamenti_scaduti': len(abbonamenti_scaduti),
        'abbonamenti_in_scadenza': len(abbonamenti_in_scadenza),
        'accessi_totali_utilizzati': sum(a.accessi_utilizzati for a in abbonamenti),
        'accessi_totali_disponibili': sum(a.accessi_totali for a in abbonamenti_attivi),
        'accessi_rimanenti': sum(a.accessi_rimanenti for a in abbonamenti_attivi),
        'importo_totale_speso': sum(a.prezzo for a in abbonamenti if a.stato_pagamento == 'pagato'),
        'importo_dovuto': sum(a.prezzo for a in abbonamenti_attivi if a.stato_pagamento != 'pagato'),
        'primo_abbonamento': min([a.data_creazione for a in abbonamenti], default=None),
        'ultimo_abbonamento': max([a.data_creazione for a in abbonamenti], default=None)
    }
    
    return render_template('clienti/dettaglio.html',
                         cliente=cliente,
                         abbonamenti=abbonamenti,
                         abbonamenti_attivi=abbonamenti_attivi,
                         abbonamenti_scaduti=abbonamenti_scaduti,
                         abbonamenti_in_scadenza=abbonamenti_in_scadenza,
                         stats=stats)

@clienti_bp.route('/api/stats')
@login_required
def api_stats():
    """API per statistiche clienti"""
    
    today = datetime.now().date()
    
    # Statistiche generali
    totale_clienti = Cliente.query.filter_by(attivo=True).count()
    
    # Clienti con abbonamenti attivi
    clienti_con_abbonamenti = db.session.query(Cliente.id).join(Abbonamento).filter(
        and_(
            Cliente.attivo == True,
            Abbonamento.attivo == True,
            Abbonamento.data_fine >= today
        )
    ).distinct().count()
    
    # Clienti con pagamenti in sospeso
    clienti_pagamenti_sospeso = db.session.query(Cliente.id).join(Abbonamento).filter(
        and_(
            Cliente.attivo == True,
            Abbonamento.attivo == True,
            Abbonamento.stato_pagamento != 'pagato'
        )
    ).distinct().count()
    
    # Clienti con abbonamenti in scadenza
    clienti_in_scadenza = db.session.query(Cliente.id).join(Abbonamento).filter(
        and_(
            Cliente.attivo == True,
            Abbonamento.attivo == True,
            Abbonamento.data_fine >= today,
            Abbonamento.data_fine <= today + timedelta(days=7)
        )
    ).distinct().count()
    
    return jsonify({
        'totale_clienti': totale_clienti,
        'clienti_con_abbonamenti': clienti_con_abbonamenti,
        'clienti_senza_abbonamenti': totale_clienti - clienti_con_abbonamenti,
        'clienti_pagamenti_sospeso': clienti_pagamenti_sospeso,
        'clienti_in_scadenza': clienti_in_scadenza
    })