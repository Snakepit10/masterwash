#!/usr/bin/env python3
"""
Script per migrare il database aggiungendo la colonna tipo_cliente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

def migrate_database():
    """Esegue la migrazione del database"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Verifica se la colonna esiste già
            result = db.session.execute(text("PRAGMA table_info(clienti)"))
            columns = [row[1] for row in result]
            
            if 'tipo_cliente' not in columns:
                print("Aggiungendo colonna tipo_cliente...")
                
                # Aggiungi la colonna con valore default
                db.session.execute(text("ALTER TABLE clienti ADD COLUMN tipo_cliente VARCHAR(20) DEFAULT 'privato'"))
                db.session.commit()
                
                print("✅ Colonna tipo_cliente aggiunta con successo!")
                print("Tutti i clienti esistenti sono stati impostati come 'privato'")
                
                # Mostra quanti clienti sono stati aggiornati
                from models import Cliente
                count = Cliente.query.count()
                print(f"📊 {count} clienti aggiornati")
                
            else:
                print("✅ Colonna tipo_cliente già presente nel database")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore durante la migrazione: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("🔄 Avvio migrazione database...")
    
    if migrate_database():
        print("✅ Migrazione completata con successo!")
    else:
        print("❌ Migrazione fallita!")
        sys.exit(1)