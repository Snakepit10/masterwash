import re
from wtforms import ValidationError

def valida_telefono(form, field):
    """Valida il formato del numero di telefono italiano"""
    telefono = field.data.replace(' ', '').replace('-', '').replace('+39', '')
    
    # Pattern per cellulari italiani (3xx xxxxxxx)
    pattern_cellulare = r'^3\d{9}$'
    # Pattern per fissi italiani (0xx xxxxxxx)
    pattern_fisso = r'^0\d{8,10}$'
    
    if not (re.match(pattern_cellulare, telefono) or re.match(pattern_fisso, telefono)):
        raise ValidationError('Inserisci un numero di telefono italiano valido')

def valida_targa(form, field):
    """Valida il formato della targa italiana"""
    targa = field.data.upper().replace(' ', '')
    
    # Pattern per targhe italiane moderne (AA123BB)
    pattern_moderna = r'^[A-Z]{2}\d{3}[A-Z]{2}$'
    # Pattern per targhe vecchie (AA123A)
    pattern_vecchia = r'^[A-Z]{2}\d{3}[A-Z]$'
    # Pattern per targhe prova (AA123)
    pattern_prova = r'^[A-Z]{2}\d{3}$'
    
    if not (re.match(pattern_moderna, targa) or 
            re.match(pattern_vecchia, targa) or 
            re.match(pattern_prova, targa)):
        raise ValidationError('Inserisci una targa italiana valida (es. AB123CD)')

def valida_codice_nfc(form, field):
    """Valida il formato del codice NFC"""
    codice = field.data.upper()
    
    # Pattern per codici NFC (8 caratteri alfanumerici)
    pattern = r'^[A-Z0-9]{8}$'
    
    if not re.match(pattern, codice):
        raise ValidationError('Il codice NFC deve essere di 8 caratteri alfanumerici')

def valida_prezzo(form, field):
    """Valida che il prezzo sia positivo"""
    if field.data <= 0:
        raise ValidationError('Il prezzo deve essere maggiore di zero')

def valida_accessi(form, field):
    """Valida che il numero di accessi sia positivo"""
    if field.data <= 0:
        raise ValidationError('Il numero di accessi deve essere maggiore di zero')

def pulisci_telefono(telefono):
    """Pulisce e standardizza il numero di telefono"""
    if not telefono:
        return None
    
    # Rimuovi spazi, trattini e prefisso internazionale
    telefono = telefono.replace(' ', '').replace('-', '').replace('+39', '')
    
    # Aggiungi zero iniziale se manca per i fissi
    if len(telefono) == 9 and telefono[0] in '0123456789' and telefono[0] != '3':
        telefono = '0' + telefono
    
    return telefono

def pulisci_targa(targa):
    """Pulisce e standardizza la targa"""
    if not targa:
        return None
    
    return targa.upper().replace(' ', '')

def formato_telefono_display(telefono):
    """Formatta il telefono per la visualizzazione"""
    if not telefono:
        return ''
    
    if len(telefono) == 10 and telefono.startswith('3'):
        # Cellulare: 333 123 4567
        return f"{telefono[:3]} {telefono[3:6]} {telefono[6:]}"
    elif len(telefono) >= 9 and telefono.startswith('0'):
        # Fisso: 06 1234 5678
        if len(telefono) == 10:
            return f"{telefono[:3]} {telefono[3:7]} {telefono[7:]}"
        else:
            return f"{telefono[:2]} {telefono[2:6]} {telefono[6:]}"
    
    return telefono

def formato_targa_display(targa):
    """Formatta la targa per la visualizzazione"""
    if not targa:
        return ''
    
    targa = targa.upper()
    if len(targa) == 7:  # AA123BB
        return f"{targa[:2]} {targa[2:5]} {targa[5:]}"
    elif len(targa) == 6:  # AA123A
        return f"{targa[:2]} {targa[2:5]} {targa[5:]}"
    elif len(targa) == 5:  # AA123
        return f"{targa[:2]} {targa[2:]}"
    
    return targa