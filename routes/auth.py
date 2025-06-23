from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length
from models import db, Operatore

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    """Form per il login degli operatori"""
    username = StringField('Username', validators=[
        DataRequired(message='Inserisci il nome utente'),
        Length(min=3, max=50, message='Il nome utente deve essere tra 3 e 50 caratteri')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Inserisci la password')
    ])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina di login"""
    # Se l'utente è già autenticato, reindirizza alla dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Cerca l'operatore nel database
        operatore = Operatore.query.filter_by(username=form.username.data).first()
        
        # Verifica credenziali e stato attivo
        if operatore and operatore.check_password(form.password.data) and operatore.attivo:
            login_user(operatore, remember=form.remember_me.data)
            flash(f'Benvenuto, {operatore.nome}!', 'success')
            
            # Reindirizza alla pagina richiesta o alla dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Nome utente o password non corretti', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout dell'operatore"""
    nome = current_user.nome
    logout_user()
    flash(f'Arrivederci, {nome}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/')
def index():
    """Redirect alla dashboard se autenticato, altrimenti al login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))