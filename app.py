import os
from flask import Flask, render_template
from flask_login import LoginManager
from dotenv import load_dotenv
from models import db, Operatore, init_db, crea_dati_demo

# Carica variabili d'ambiente
load_dotenv()

def create_app():
    """Factory function per creare l'app Flask"""
    app = Flask(__name__)
    
    # Configurazione
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///masterwash.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['BASE_URL'] = os.environ.get('BASE_URL', 'https://masterwash.up.railway.app')
    
    # Fix per Railway PostgreSQL URL
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    
    # Inizializza estensioni
    db.init_app(app)
    
    # Configurazione Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Operatore.query.get(int(user_id))
    
    # Registra blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.abbonamenti import abbonamenti_bp
    from routes.accessi import accessi_bp
    from routes.stampa import stampa_bp
    from routes.clienti import clienti_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(abbonamenti_bp, url_prefix='/abbonamenti')
    app.register_blueprint(accessi_bp, url_prefix='/accessi')
    app.register_blueprint(stampa_bp, url_prefix='/stampa')
    app.register_blueprint(clienti_bp, url_prefix='/clienti')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Context processors globali
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'MasterWash',
            'app_version': '1.0.0'
        }
    
    # Gestione errori
    @app.errorhandler(404)
    def not_found_error(error):
        try:
            return render_template('errors/404.html'), 404
        except:
            return '<h1>404 - Pagina Non Trovata</h1><a href="/">Torna alla Home</a>', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        try:
            return render_template('errors/500.html'), 500
        except:
            return '<h1>500 - Errore del Server</h1><a href="/">Torna alla Home</a>', 500
    
    # Comandi CLI personalizzati
    @app.cli.command()
    def init_database():
        """Inizializza il database"""
        init_db()
        print("Database inizializzato!")
    
    @app.cli.command()
    def create_demo_data():
        """Crea dati di demo"""
        crea_dati_demo()
        print("Dati demo creati!")
    
    @app.cli.command()
    def reset_database():
        """Reset completo del database"""
        db.drop_all()
        db.create_all()
        init_db()
        crea_dati_demo()
        print("Database resettato e ricreato!")
    
    @app.cli.command()
    def migrate_cliente_type():
        """Aggiungi colonna tipo_cliente ai clienti esistenti"""
        try:
            from sqlalchemy import text
            
            # Verifica se la colonna esiste già
            result = db.session.execute(text("PRAGMA table_info(clienti)"))
            columns = [row[1] for row in result]
            
            if 'tipo_cliente' not in columns:
                # Aggiungi la colonna
                db.session.execute(text("ALTER TABLE clienti ADD COLUMN tipo_cliente VARCHAR(20) DEFAULT 'privato'"))
                db.session.commit()
                print("Colonna tipo_cliente aggiunta con successo!")
            else:
                print("Colonna tipo_cliente già presente.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Errore durante la migrazione: {e}")
    
    @app.cli.command()
    def update_database():
        """Aggiorna il database con le nuove modifiche"""
        try:
            # Esegui tutte le migrazioni necessarie
            migrate_cliente_type.callback()
            print("Database aggiornato con successo!")
        except Exception as e:
            print(f"Errore durante l'aggiornamento: {e}")
    
    # Route temporanea per migrazione (rimuovere dopo l'uso)
    @app.route('/migrate-db')
    def migrate_db_route():
        """Route temporanea per migrare il database"""
        try:
            from sqlalchemy import text
            
            # Verifica se la colonna esiste già
            result = db.session.execute(text("PRAGMA table_info(clienti)"))
            columns = [row[1] for row in result]
            
            if 'tipo_cliente' not in columns:
                # Aggiungi la colonna
                db.session.execute(text("ALTER TABLE clienti ADD COLUMN tipo_cliente VARCHAR(20) DEFAULT 'privato'"))
                db.session.commit()
                
                from models import Cliente
                count = Cliente.query.count()
                
                return f"<h1>✅ Migrazione completata!</h1><p>Colonna tipo_cliente aggiunta con successo.</p><p>{count} clienti aggiornati.</p><p><a href='/check-clients'>Verifica clienti</a> | <a href='/'>Torna alla home</a></p>"
            else:
                return f"<h1>✅ Migrazione già completata</h1><p>La colonna tipo_cliente è già presente nel database.</p><p><a href='/check-clients'>Verifica clienti</a> | <a href='/'>Torna alla home</a></p>"
                
        except Exception as e:
            db.session.rollback()
            return f"<h1>❌ Errore durante la migrazione</h1><p>{str(e)}</p><p><a href='/'>Torna alla home</a></p>"
    
    @app.route('/check-clients')
    def check_clients():
        """Route per verificare lo stato dei clienti"""
        try:
            from sqlalchemy import text
            from models import Cliente
            
            html = "<h1>🔍 Stato Clienti nel Database</h1>"
            
            # Verifica colonna
            result = db.session.execute(text("PRAGMA table_info(clienti)"))
            columns = [row[1] for row in result]
            
            if 'tipo_cliente' not in columns:
                return html + "<p>❌ Colonna tipo_cliente non presente. <a href='/migrate-db'>Esegui migrazione</a></p>"
            
            html += "<h2>📊 Tutti i clienti:</h2><table border='1' style='border-collapse: collapse; width: 100%;'>"
            html += "<tr><th>ID</th><th>Nome</th><th>Telefono</th><th>Tipo Cliente</th><th>Attivo</th></tr>"
            
            clienti = Cliente.query.all()
            for cliente in clienti:
                tipo = getattr(cliente, 'tipo_cliente', 'NULL')
                attivo = "Sì" if cliente.attivo else "No"
                tipo_display = cliente.tipo_cliente_display
                html += f"<tr><td>{cliente.id}</td><td>{cliente.nome_completo}</td><td>{cliente.telefono}</td><td>{tipo} ({tipo_display})</td><td>{attivo}</td></tr>"
            
            html += "</table>"
            
            # Statistiche
            privati = Cliente.query.filter_by(tipo_cliente='privato').count()
            business = Cliente.query.filter_by(tipo_cliente='business').count()
            try:
                normali = db.session.execute(text("SELECT COUNT(*) FROM clienti WHERE tipo_cliente = 'normale'")).scalar()
                nulli = db.session.execute(text("SELECT COUNT(*) FROM clienti WHERE tipo_cliente IS NULL")).scalar()
            except:
                normali = 0
                nulli = 0
            
            html += f"<h2>📈 Statistiche:</h2>"
            html += f"<p>Clienti privati: {privati}</p>"
            html += f"<p>Clienti business: {business}</p>"
            html += f"<p>Clienti 'normale' (da correggere): {normali}</p>"
            html += f"<p>Clienti con tipo NULL: {nulli}</p>"
            
            if normali > 0 or nulli > 0:
                html += f"<p><a href='/fix-client-types' style='background: orange; color: white; padding: 10px; text-decoration: none;'>🔧 Correggi tipi errati</a></p>"
            
            html += "<p><a href='/clienti'>Vai alla gestione clienti</a> | <a href='/'>Torna alla home</a></p>"
            
            return html
            
        except Exception as e:
            return f"<h1>❌ Errore</h1><p>{str(e)}</p><p><a href='/'>Torna alla home</a></p>"
    
    @app.route('/fix-client-types')
    def fix_client_types():
        """Route per correggere i tipi di cliente errati"""
        try:
            from sqlalchemy import text
            
            correzioni = 0
            
            # Correggi 'normale' -> 'privato'
            result1 = db.session.execute(text("UPDATE clienti SET tipo_cliente = 'privato' WHERE tipo_cliente = 'normale'"))
            correzioni += result1.rowcount
            
            # Correggi NULL -> 'privato'  
            result2 = db.session.execute(text("UPDATE clienti SET tipo_cliente = 'privato' WHERE tipo_cliente IS NULL"))
            correzioni += result2.rowcount
            
            db.session.commit()
            
            return f"<h1>✅ Correzione completata!</h1><p>{correzioni} clienti corretti.</p><p><a href='/check-clients'>Verifica risultati</a> | <a href='/clienti'>Gestione clienti</a></p>"
            
        except Exception as e:
            db.session.rollback()
            return f"<h1>❌ Errore durante la correzione</h1><p>{str(e)}</p><p><a href='/check-clients'>Torna alla verifica</a></p>"
    
    # Inizializza database al primo avvio
    with app.app_context():
        try:
            db.create_all()
            init_db()
        except Exception as e:
            print(f"Errore inizializzazione database: {e}")
    
    return app

# Crea istanza app
app = create_app()

# Importa template filters
from utils.filters import register_filters
register_filters(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)