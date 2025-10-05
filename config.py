# config.py

import os

# Classe base de configuração
class Config:
    """
    Configurações base da aplicação Flask.
    """
    # Chave secreta para proteger sessões e cookies. Mude isso para algo aleatório e seguro.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-outra-chave-qualquer'

    # Define a string de conexão completa para o banco de dados PostgreSQL.
    SQLALCHEMY_DATABASE_URI = 'postgresql://admin_plataforma:290317@localhost:5432/plataforma_db'

    # Desativa uma funcionalidade do SQLAlchemy que emite sinais de modificação.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- INÍCIO DAS NOVAS CONFIGURAÇÕES DE E-MAIL ---
    # Configurações para o Flask-Mail.
    # É ALTAMENTE RECOMENDÁVEL usar variáveis de ambiente para dados sensíveis.
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'sandbox.smtp.mailtrap.io'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 2525)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'b955880a5e215f'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '2f80508e979b23'
    MAIL_DEFAULT_SENDER = ('Admin da Plataforma', os.environ.get('MAIL_DEFAULT_SENDER') or 'nao-responda@plataforma.com')
    # --- FIM DAS NOVAS CONFIGURAÇÕES DE E-MAIL ---