# app/events.py

# --- 'request' FOI ADICIONADO À IMPORTAÇÃO ---
from flask import session, request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from . import socketio

# Este dicionário irá armazenar os usuários online
# A chave será o username e o valor o session ID (sid)
online_users = {}


# --- FUNÇÃO CORRIGIDA ---
@socketio.on('connect')
def handle_connect():
    """
    Lida com um novo cliente se conectando.
    Este evento é disparado automaticamente quando a conexão é estabelecida.
    """
    if current_user.is_authenticated:
        # AQUI ESTÁ A CORREÇÃO: Usamos 'request.sid' em vez de 'session['sid']'
        # O 'request.sid' nos dá o ID de sessão único para esta conexão específica.
        online_users[current_user.username] = request.sid
        
        # Emite a lista atualizada de usuários online para todos os clientes
        emit('update_online_users', list(online_users.keys()), broadcast=True)
        print(f'Cliente conectado: {current_user.username} com sid: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    """
    Lida com um cliente se desconectando.
    Este evento é disparado automaticamente quando o cliente fecha a conexão.
    """
    # A lógica aqui já estava correta, pois usa 'current_user' para remover.
    if current_user.is_authenticated and current_user.username in online_users:
        # Remove o usuário do dicionário
        del online_users[current_user.username]
        # Emite a lista atualizada de usuários online para todos os clientes
        emit('update_online_users', list(online_users.keys()), broadcast=True)
        print(f'Cliente desconectado: {current_user.username}')


@socketio.on('new_message')
def handle_new_message(data):
    """
    Lida com o recebimento de uma nova mensagem de um cliente.
    O parâmetro 'data' é o dicionário de dados enviado pelo cliente.
    """
    if current_user.is_authenticated:
        # Prepara a mensagem a ser enviada para os outros clientes
        message_payload = {
            'username': current_user.username,
            'profile_picture': current_user.profile_picture,
            'text': data['message']
        }
        # Emite a mensagem para todos os clientes, incluindo o remetente
        emit('chat_message', message_payload, broadcast=True)
