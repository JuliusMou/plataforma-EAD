# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

# --- PASSO 1: Criar as instâncias das extensões ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# --- Configurações do LoginManager ---
# Define para qual rota usuários não logados devem ser redirecionados
login_manager.login_view = 'auth.pagina_login'

# --- NOVA LINHA ADICIONADA AQUI ---
# Define a mensagem em português para a tela de login
login_manager.login_message = 'Por favor, faça o login para acessar esta página.'


# --- PASSO 2: Importar os módulos da aplicação ---
from .admin import admin
from app.auth import auth as auth_blueprint
from app.main import main as main_blueprint

def create_app(config_class=Config):
    """
    Função Factory para criar a aplicação Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- PASSO 3: Inicializar as extensões com a aplicação ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    admin.init_app(app)
    mail.init_app(app)

    # --- PASSO 4: Registrar os Blueprints ---
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(main_blueprint)

    return app