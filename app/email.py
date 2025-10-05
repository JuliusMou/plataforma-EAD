# app/email.py

from flask_mail import Message
from flask import render_template, current_app
from . import mail


def send_password_reset_email(user):
    """
    Envia o e-mail de redefinição de senha para um usuário.
    """
    token = user.get_reset_password_token()
    msg = Message('Redefinição de Senha - Plataforma EAD',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])

    # Corpo do e-mail em formato texto e HTML
    msg.body = render_template('auth/email/reset_password.txt', user=user, token=token)
    msg.html = render_template('auth/email/reset_password.html', user=user, token=token)

    mail.send(msg)