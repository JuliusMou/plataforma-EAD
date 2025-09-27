# app/__init__.py (VERSÃO CORRIGIDA E REORDENADA)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# --- PASSO 1: Criar as instâncias das extensões ---
# Estes objetos precisam existir antes que outros arquivos (como models.py, routes.py, admin.py)
# tentem importá-los.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.pagina_login'

# --- PASSO 2: Importar os módulos da aplicação (Blueprints e Admin) ---
# Agora que 'db' já existe, podemos importar com segurança os módulos que o utilizam.
from .admin import admin
from app.auth import auth as auth_blueprint
from app.main import main as main_blueprint

def create_app(config_class=Config):
    """
    Função Factory para criar a aplicação Flask.
    Isso mantém nosso código organizado e permite múltiplas configurações.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- PASSO 3: Inicializar as extensões com a aplicação ---
    # Aqui, conectamos as extensões que criamos à nossa instância específica do Flask.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    admin.init_app(app)

    # --- PASSO 4: Registrar os Blueprints ---
    # Blueprints ajudam a organizar as rotas e a estruturar o projeto.
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(main_blueprint)

    return app