# config.py

import os

# --- NOVO ---
# Pega o diretório base do projeto
basedir = os.path.abspath(os.path.dirname(__file__))

# Classe base de configuração
class Config:
    """
    Configurações base da aplicação Flask.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-outra-chave-qualquer'

    # --- LÓGICA ATUALIZADA DO BANCO DE DADOS ---
    # Prioriza a variável de ambiente DATABASE_URL.
    # Se não existir, usa um banco de dados SQLite local como padrão.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # (O restante das configurações de e-mail permanece o mesmo)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'sandbox.smtp.mailtrap.io'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 2525)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'b955880a5e215f'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '2f80508e979b23'
    MAIL_DEFAULT_SENDER = ('Admin da Plataforma', os.environ.get('MAIL_DEFAULT_SENDER') or 'nao-responda@plataforma.com')
