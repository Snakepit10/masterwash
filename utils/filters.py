from datetime import datetime, date
from utils.validators import formato_telefono_display, formato_targa_display

def register_filters(app):
    """Registra i filtri template personalizzati"""
    
    @app.template_filter('datetime')
    def datetime_filter(dt, formato='%d/%m/%Y %H:%M'):
        """Formatta datetime per visualizzazione"""
        if not dt:
            return ''
        if isinstance(dt, str):
            return dt
        return dt.strftime(formato)
    
    @app.template_filter('date')
    def date_filter(d, formato='%d/%m/%Y'):
        """Formatta date per visualizzazione"""
        if not d:
            return ''
        if isinstance(d, str):
            return d
        if isinstance(d, datetime):
            d = d.date()
        return d.strftime(formato)
    
    @app.template_filter('currency')
    def currency_filter(amount):
        """Formatta importi in euro"""
        if not amount:
            return '€ 0,00'
        return f"€ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @app.template_filter('telefono')
    def telefono_filter(telefono):
        """Formatta telefono per visualizzazione"""
        return formato_telefono_display(telefono)
    
    @app.template_filter('targa')
    def targa_filter(targa):
        """Formatta targa per visualizzazione"""
        return formato_targa_display(targa)
    
    @app.template_filter('plurale')
    def plurale_filter(numero, singolare, plurale):
        """Gestisce singolare/plurale in italiano"""
        if numero == 1:
            return f"{numero} {singolare}"
        else:
            return f"{numero} {plurale}"
    
    @app.template_filter('giorni_scadenza')
    def giorni_scadenza_filter(giorni):
        """Formatta i giorni alla scadenza"""
        if giorni < 0:
            return f"Scaduto da {abs(giorni)} giorni"
        elif giorni == 0:
            return "Scade oggi"
        elif giorni == 1:
            return "Scade domani"
        else:
            return f"Scade tra {giorni} giorni"
    
    @app.template_filter('stato_abbonamento')
    def stato_abbonamento_filter(abbonamento):
        """Ritorna lo stato dell'abbonamento con classe CSS"""
        if abbonamento.is_scaduto:
            return {'testo': 'Scaduto', 'classe': 'danger'}
        elif abbonamento.is_in_scadenza:
            return {'testo': 'In scadenza', 'classe': 'warning'}
        elif abbonamento.accessi_rimanenti == 0:
            return {'testo': 'Esaurito', 'classe': 'danger'}
        else:
            return {'testo': 'Attivo', 'classe': 'success'}
    
    @app.template_filter('icona_tipo_abbonamento')
    def icona_tipo_abbonamento_filter(tipo):
        """Ritorna l'icona per il tipo di abbonamento"""
        icone = {
            'mensile': '📅',
            'trimestrale': '🗓️',
            'annuale': '📆'
        }
        return icone.get(tipo, '📄')
    
    @app.template_filter('colore_accessi')
    def colore_accessi_filter(accessi_rimanenti):
        """Ritorna la classe CSS per il colore degli accessi"""
        if accessi_rimanenti > 5:
            return 'success'
        elif accessi_rimanenti >= 2:
            return 'warning'
        else:
            return 'danger'