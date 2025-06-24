#!/usr/bin/env python3
"""
Script per verificare e correggere i tipi di cliente nel database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Cliente

def check_and_fix_client_types():
    """Verifica e corregge i tipi di cliente"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            print("🔍 Verificando stato database...")
            
            # Verifica se la colonna tipo_cliente esiste
            result = db.session.execute(text("PRAGMA table_info(clienti)"))
            columns = [row[1] for row in result]
            
            if 'tipo_cliente' not in columns:
                print("❌ Colonna tipo_cliente non trovata. Eseguire prima la migrazione!")
                return False
            
            # Mostra tutti i clienti con i loro tipi
            print("\n📊 Clienti nel database:")
            clienti = Cliente.query.all()
            
            if not clienti:
                print("   Nessun cliente trovato")
                return True
            
            for cliente in clienti:
                tipo = getattr(cliente, 'tipo_cliente', 'NULL')
                attivo = "Attivo" if cliente.attivo else "Inattivo"
                print(f"   {cliente.id}: {cliente.nome_completo} - Tipo: '{tipo}' - {attivo}")
            
            # Conta per tipo
            privati = Cliente.query.filter_by(tipo_cliente='privato').count()
            business = Cliente.query.filter_by(tipo_cliente='business').count()
            normali = db.session.execute(text("SELECT COUNT(*) FROM clienti WHERE tipo_cliente = 'normale'")).scalar()
            nulli = db.session.execute(text("SELECT COUNT(*) FROM clienti WHERE tipo_cliente IS NULL")).scalar()
            
            print(f"\n📈 Statistiche:")
            print(f"   Clienti privati: {privati}")
            print(f"   Clienti business: {business}")
            print(f"   Clienti 'normale' (da correggere): {normali}")
            print(f"   Clienti con tipo NULL: {nulli}")
            
            # Correggi i tipi errati
            correzioni = 0
            if normali > 0:
                print(f"\n🔧 Correggendo {normali} clienti con tipo 'normale'...")
                result = db.session.execute(text("UPDATE clienti SET tipo_cliente = 'privato' WHERE tipo_cliente = 'normale'"))
                correzioni += normali
            
            if nulli > 0:
                print(f"🔧 Correggendo {nulli} clienti con tipo NULL...")
                result = db.session.execute(text("UPDATE clienti SET tipo_cliente = 'privato' WHERE tipo_cliente IS NULL"))
                correzioni += nulli
            
            if correzioni > 0:
                db.session.commit()
                print(f"✅ {correzioni} clienti corretti!")
            else:
                print("✅ Tutti i clienti hanno già il tipo corretto")
            
            # Verifica finale
            print("\n🔍 Verifica finale:")
            privati_finali = Cliente.query.filter_by(tipo_cliente='privato').count()
            business_finali = Cliente.query.filter_by(tipo_cliente='business').count()
            print(f"   Clienti privati: {privati_finali}")
            print(f"   Clienti business: {business_finali}")
            
            # Test visibilità
            print("\n👁️ Test visibilità clienti attivi:")
            clienti_attivi = Cliente.query.filter_by(attivo=True).all()
            for cliente in clienti_attivi:
                tipo_display = cliente.tipo_cliente_display
                print(f"   {cliente.nome_completo} - {tipo_display}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore: {e}")
            return False

if __name__ == "__main__":
    print("🔄 Verifica e correzione tipi cliente...")
    
    if check_and_fix_client_types():
        print("✅ Operazione completata!")
    else:
        print("❌ Operazione fallita!")
        sys.exit(1)