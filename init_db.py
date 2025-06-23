#!/usr/bin/env python3
"""
Script di inizializzazione database per MasterWash
"""

import os
import sys
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

# Aggiungi il path corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, init_db, crea_dati_demo

def main():
    """Inizializza il database"""
    app = create_app()
    
    with app.app_context():
        print("🗃️  Inizializzazione database MasterWash...")
        
        try:
            # Crea tutte le tabelle
            db.create_all()
            print("✅ Tabelle create con successo")
            
            # Inizializza dati base
            init_db()
            print("✅ Dati base inseriti")
            
            # Crea dati demo se richiesto
            if len(sys.argv) > 1 and sys.argv[1] == '--demo':
                crea_dati_demo()
                print("✅ Dati demo creati")
            
            print("🎉 Database inizializzato con successo!")
            print("\n📋 Credenziali di accesso:")
            print("   Admin: admin / admin123")
            print("   Operatore: operatore1 / operatore123")
            
        except Exception as e:
            print(f"❌ Errore durante l'inizializzazione: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()