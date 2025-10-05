# app/auth/routes.py

from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required

from . import auth
from app import db
from app.models import User
from app.email import send_password_reset_email  # Importa a função de envio de e-mail
from .forms import PasswordResetRequestForm, ResetPasswordForm  # Importa os novos formulários


@auth.route('/cadastro', methods=['GET', 'POST'])
def pagina_cadastro():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_email = User.query.filter_by(email=email).first()
        if user_email:
            flash('Este email já está em uso. Por favor, escolha outro.', 'warning')
            return redirect(url_for('auth.pagina_cadastro'))
        user_username = User.query.filter_by(username=username).first()
        if user_username:
            flash('Este nome de usuário já está em uso. Por favor, escolha outro.', 'warning')
            return redirect(url_for('auth.pagina_cadastro'))
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        novo_usuario = User(username=username, email=email, password_hash=password_hash, score=0)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Por favor, faça o login.', 'success')
        return redirect(url_for('auth.pagina_login'))
    return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
def pagina_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email:
            email = email.strip()

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # Redireciona para a página que o usuário tentou acessar ou para a principal
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.pagina_principal'))
        else:
            flash('Email ou senha inválidos. Por favor, tente novamente.', 'danger')
            return redirect(url_for('auth.pagina_login'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def pagina_logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.pagina_login'))


# --- INÍCIO DAS NOVAS ROTAS DE REDEFINIÇÃO DE SENHA ---

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def pagina_reset_password_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        # A flash message é a mesma para não revelar se um e-mail está ou não cadastrado
        flash('Um e-mail com instruções para redefinir sua senha foi enviado.', 'info')
        return redirect(url_for('auth.pagina_login'))
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def pagina_reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        flash('O link para redefinição de senha é inválido ou expirou.', 'warning')
        return redirect(url_for('auth.pagina_reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Gera o hash da nova senha
        password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user.password_hash = password_hash
        db.session.commit()
        flash('Sua senha foi atualizada com sucesso!', 'success')
        return redirect(url_for('auth.pagina_login'))

    return render_template('auth/reset_password.html', form=form)

# --- FIM DAS NOVAS ROTAS ---