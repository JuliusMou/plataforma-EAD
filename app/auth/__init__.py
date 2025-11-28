# app/auth/__init__.py

from flask import Blueprint

# Cria uma instância de Blueprint.
# 'auth' é o nome do blueprint.
# __name__ ajuda o Flask a localizar a pasta de templates/static do blueprint.
auth = Blueprint('auth', __name__)

# A importação do routes.py é feita no final para evitar importações circulares.
from . import routes