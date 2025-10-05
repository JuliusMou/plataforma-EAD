# app/auth/routes.py

from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from app import db
from app.models import User
from app.email import send_password_reset_email, send_confirmation_email
from .forms import PasswordResetRequestForm, ResetPasswordForm


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

        send_confirmation_email(novo_usuario)

        flash('Cadastro realizado com sucesso! Um e-mail de confirmação foi enviado para você.', 'success')
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
            if not user.confirmed:
                flash('Sua conta ainda não foi confirmada. Por favor, verifique seu e-mail.', 'warning')
                return redirect(url_for('auth.pagina_login'))

            login_user(user)
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


# --- ROTA DE CONFIRMAÇÃO CORRIGIDA ---
# Removido o @login_required e lógica ajustada para usar o token.
@auth.route('/confirm/<token>')
def confirm_email(token):
    # Primeiro, verificamos se o usuário já está logado e confirmado
    if current_user.is_authenticated and current_user.confirmed:
        return redirect(url_for('main.pagina_principal'))

    # Verificamos o token para encontrar o usuário
    user = User.verify_confirmation_token(token)
    if not user:
        flash('O link de confirmação é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.pagina_login'))

    if user.confirmed:
        flash('Sua conta já foi confirmada. Por favor, faça o login.', 'info')
    else:
        user.confirmed = True
        db.session.commit()
        flash('Obrigado por confirmar sua conta! Agora você pode fazer o login.', 'success')

    return redirect(url_for('auth.pagina_login'))


@auth.route('/resend_confirmation')
@login_required
def resend_confirmation():
    if current_user.confirmed:
        flash('Sua conta já está confirmada!', 'info')
        return redirect(url_for('main.pagina_principal'))

    send_confirmation_email(current_user)
    flash('Um novo e-mail de confirmação foi enviado para sua caixa de entrada.', 'success')
    return redirect(url_for('auth.pagina_login'))


@auth.route('/reset_password_request', methods=['GET', 'POST'])
def pagina_reset_password_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
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
        password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha266')
        user.password_hash = password_hash
        db.session.commit()
        flash('Sua senha foi atualizada com sucesso!', 'success')
        return redirect(url_for('auth.pagina_login'))

    return render_template('auth/reset_password.html', form=form)