# app/email.py

from flask_mail import Message
from flask import render_template, current_app
from . import mail
from threading import Thread
# --- NOVA IMPORTAÇÃO ---
# Adicionamos o módulo de logging do Python
import logging

# --- CONFIGURAÇÃO BÁSICA DO LOGGING ---
# Isso fará com que as mensagens de log apareçam no seu console
logging.basicConfig(level=logging.INFO)


def send_async_email(app, msg):
    """ Função que será executada em uma thread separada para enviar o e-mail. """
    with app.app_context():
        try:
            # --- LOG ADICIONADO ---
            logging.info(f"Tentando enviar e-mail para: {msg.recipients}")
            mail.send(msg)
            # --- LOG ADICIONADO ---
            logging.info(f"E-mail para {msg.recipients} enviado com sucesso!")
        except Exception as e:
            # --- LOG DE ERRO ADICIONADO ---
            # Se algo der errado, isso irá imprimir a exceção no console
            logging.error(f"Falha ao enviar e-mail para {msg.recipients}: {e}")


def send_email_wrapper(subject, sender, recipients, text_body, html_body):
    """ Função wrapper para preparar e disparar a thread de e-mail. """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    # Obtém a app atual para passar para a thread
    app = current_app._get_current_object()

    # --- LOG ADICIONADO ---
    logging.info(f"Disparando thread de envio de e-mail para: {recipients}")
    # Cria e inicia a thread
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    """ Envia o e-mail de redefinição de senha de forma assíncrona. """
    token = user.get_reset_password_token()
    app = current_app._get_current_object()  # Precisamos da app para renderizar o template

    # --- LOG ADICIONADO ---
    logging.info(f"Preparando e-mail de redefinição de senha para o usuário: {user.email}")
    send_email_wrapper(
        subject='Redefinição de Senha - Plataforma EAD',
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('auth/email/reset_password.txt', user=user, token=token),
        html_body=render_template('auth/email/reset_password.html', user=user, token=token)
    )


def send_confirmation_email(user):
    """ Envia o e-mail de confirmação de conta de forma assíncrona. """
    token = user.get_confirmation_token()
    app = current_app._get_current_object()  # Precisamos da app para renderizar o template

    # --- LOG ADICIONADO ---
    logging.info(f"Preparando e-mail de confirmação para o usuário: {user.email}")
    send_email_wrapper(
        subject='Confirme sua Conta - Plataforma EAD',
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('auth/email/confirm_email.txt', user=user, token=token),
        html_body=render_template('auth/email/confirm_email.html', user=user, token=token)
    )
