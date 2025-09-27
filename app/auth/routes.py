# app/auth/routes.py

from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from . import auth
from app import db
from app.models import User
from werkzeug.security import check_password_hash # Importa a função para checar a senha
from flask_login import login_user, logout_user, login_required # Importa funções da Flask-Login

# ... (rota de cadastro permanece a mesma) ...
@auth.route('/cadastro', methods=['GET', 'POST'])
def pagina_cadastro():
    # ... (código existente)
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            flash('Este email já está em uso. Por favor, escolha outro.')
            return redirect(url_for('auth.pagina_cadastro'))
        user_username = User.query.filter_by(username=username).first()
        if user_username:
            flash('Este nome de usuário já está em uso. Por favor, escolha outro.')
            return redirect(url_for('auth.pagina_cadastro'))
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        novo_usuario = User(username=username, email=email, password_hash=password_hash, score=0)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Por favor, faça o login.')
        return redirect(url_for('auth.pagina_login'))
    return render_template('auth/register.html')


# --- ROTA DE LOGIN ATUALIZADA COM A LÓGICA ---
@auth.route('/login', methods=['GET', 'POST'])
def pagina_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # É uma boa prática remover espaços em branco do email antes de buscar no banco
        if email:
            email = email.strip()

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.pagina_principal'))
        else:
            flash('Email ou senha inválidos. Por favor, tente novamente.')
            return redirect(url_for('auth.pagina_login'))

    return render_template('auth/login.html')

# --- ROTA DE LOGOUT ---
@auth.route('/logout')
@login_required # Este decorador protege a rota, só usuários logados podem acessá-la
def pagina_logout():
    logout_user() # Função da Flask-Login que encerra a sessão do usuário
    return redirect(url_for('auth.pagina_login'))