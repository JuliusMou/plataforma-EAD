# app/events.py

from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from sqlalchemy import or_

from . import socketio, db
from .models import User, PrivateMessage


online_users = {}

def get_private_room_name(user1_id, user2_id):
    """Gera um nome de sala consistente para dois usuários."""
    return f"sala_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"


@socketio.on('connect')
def handle_connect():
    """Lida com a conexão de um novo cliente."""
    if current_user.is_authenticated:
        online_users[current_user.username] = request.sid
        emit('update_online_users', list(online_users.keys()), broadcast=True)
        print(f'Cliente conectado: {current_user.username} com sid: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    """Lida com a desconexão de um cliente."""
    if current_user.is_authenticated and current_user.username in online_users:
        del online_users[current_user.username]
        emit('update_online_users', list(online_users.keys()), broadcast=True)
        print(f'Cliente desconectado: {current_user.username}')


@socketio.on('join_private_chat')
def join_private_chat(data):
    """Coloca o usuário em uma sala privada para conversar com outro."""
    recipient_username = data['recipient_username']
    recipient = User.query.filter_by(username=recipient_username).first()

    if not recipient or not current_user.is_authenticated:
        return

    room = get_private_room_name(current_user.id, recipient.id)
    join_room(room)

    history = PrivateMessage.query.filter(
        or_(
            (PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == recipient.id),
            (PrivateMessage.sender_id == recipient.id) & (PrivateMessage.recipient_id == current_user.id)
        )
    ).order_by(PrivateMessage.timestamp.asc()).all()

    message_history = [
        {
            'username': msg.sender.username,
            'profile_picture': msg.sender.profile_picture,
            'text': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for msg in history
    ]

    emit('private_message_history', {'history': message_history, 'room': room})


# --- FUNÇÃO ATUALIZADA (CORREÇÃO FINAL) ---
@socketio.on('private_message')
def handle_private_message(data):
    """Lida com o envio de uma mensagem privada."""
    recipient_username = data['recipient_username']
    recipient = User.query.filter_by(username=recipient_username).first()
    message_text = data['message']

    if not recipient or not current_user.is_authenticated:
        return

    new_message = PrivateMessage(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=message_text
    )
    db.session.add(new_message)
    db.session.commit()

    message_payload = {
        'username': current_user.username,
        'profile_picture': current_user.profile_picture,
        'text': message_text,
        'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }

    room = get_private_room_name(current_user.id, recipient.id)

    # --- LÓGICA DE CORREÇÃO ---
    # 1. Garante que o REMETENTE (usuário atual) está na sala.
    #    Isso é redundante se ele acabou de entrar, mas não causa mal e garante a entrega.
    join_room(room)

    # 2. Verifica se o DESTINATÁRIO está online e o adiciona à sala.
    if recipient.username in online_users:
        recipient_sid = online_users[recipient.username]
        join_room(room, sid=recipient_sid)

    # 3. Envia a mensagem para a sala. Agora temos certeza que ambos estão lá (se online).
    emit('new_private_message', message_payload, to=room)


@socketio.on('new_message')
def handle_new_message(data):
    """Lida com o recebimento de uma nova mensagem global."""
    if current_user.is_authenticated:
        message_payload = {
            'username': current_user.username,
            'profile_picture': current_user.profile_picture,
            'text': data['message']
        }
        emit('chat_message', message_payload, broadcast=True)
