# config.py (VERSÃO COMPLETA E CORRIGIDA)

import os

# Classe base de configuração
class Config:
    """
    Configurações base da aplicação Flask.
    """
    # Chave secreta para proteger sessões e cookies. Mude isso para algo aleatório e seguro.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-outra-chave-qualquer'

    # -------------------------------------------------------------------------------------
    # LINHA CORRIGIDA ABAIXO
    # -------------------------------------------------------------------------------------
    # Define a string de conexão completa para o banco de dados PostgreSQL.
    # Formato: 'postgresql://<usuario>:<senha>@<host>:<porta>/<nome_do_banco>'
    SQLALCHEMY_DATABASE_URI = 'postgresql://admin_plataforma:290317@localhost:5432/plataforma_db'

    # Desativa uma funcionalidade do SQLAlchemy que emite sinais de modificação.
    # Definir como False melhora a performance.
    SQLALCHEMY_TRACK_MODIFICATIONS = False