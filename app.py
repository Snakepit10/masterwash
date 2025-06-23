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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(abbonamenti_bp, url_prefix='/abbonamenti')
    app.register_blueprint(accessi_bp, url_prefix='/accessi')
    app.register_blueprint(stampa_bp, url_prefix='/stampa')
    
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
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
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