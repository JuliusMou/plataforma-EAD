# app/events.py

from flask import request
from flask_socketio import emit, join_room
from flask_login import current_user
from sqlalchemy import or_

from . import socketio, db
from .models import User, PrivateMessage


# Dicionário para rastrear usuários online e seus session IDs
online_users = {}

def get_private_room_name(user1_id, user2_id):
    """Gera um nome de sala consistente para dois usuários, garantindo a ordem dos IDs."""
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
    """Lida com a desconexão de um cliente de forma robusta."""
    disconnected_user = None
    for username, sid in list(online_users.items()):
        if sid == request.sid:
            disconnected_user = username
            break

    if disconnected_user:
        del online_users[disconnected_user]
        emit('user_typing_stop', {'username': disconnected_user}, broadcast=True)
        emit('update_online_users', list(online_users.keys()), broadcast=True)
        print(f'Cliente desconectado: {disconnected_user}')


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


@socketio.on('private_message')
def handle_private_message(data):
    """Lida com o envio de uma mensagem privada."""
    recipient_username = data['recipient_username']
    recipient = User.query.filter_by(username=recipient_username).first()
    message_text = data['message']

    if not recipient or not current_user.is_authenticated:
        return

    # Salva a mensagem no banco de dados com status 'read=False'
    new_message = PrivateMessage(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=message_text,
        read=False # Explicitamente definido como não lida
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
    join_room(room)

    # Envia a mensagem para a sala (para que ambos os usuários a vejam se estiverem na conversa)
    emit('new_private_message', message_payload, to=room)

    # --- NOVA LÓGICA DE NOTIFICAÇÃO ---
    # Se o destinatário estiver online, envia uma notificação diretamente para ele
    if recipient.username in online_users:
        recipient_sid = online_users[recipient.username]
        # Emite um evento separado de notificação
        emit('unread_message_notification', {'sender': current_user.username}, to=recipient_sid)


# --- NOVO EVENTO PARA MARCAR MENSAGENS COMO LIDAS ---
@socketio.on('mark_messages_as_read')
def mark_messages_as_read(data):
    """Marca as mensagens de um remetente específico como lidas no banco de dados."""
    if not current_user.is_authenticated:
        return

    sender_username = data.get('sender_username')
    sender = User.query.filter_by(username=sender_username).first()

    if sender:
        # Encontra todas as mensagens não lidas que o usuário atual recebeu do remetente
        messages_to_update = PrivateMessage.query.filter(
            PrivateMessage.recipient_id == current_user.id,
            PrivateMessage.sender_id == sender.id,
            PrivateMessage.read == False
        ).all()
        
        for msg in messages_to_update:
            msg.read = True
            
        db.session.commit()
        print(f'{len(messages_to_update)} mensagens de {sender_username} marcadas como lidas para {current_user.username}')


@socketio.on('typing_start')
def handle_typing_start(data):
    """Avisa ao outro usuário na sala privada que o usuário atual começou a digitar."""
    if not current_user.is_authenticated:
        return

    room = data.get('room')
    if room:
        payload = {'username': current_user.username}
        emit('user_typing_start', payload, to=room, include_self=False)


@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Avisa ao outro usuário na sala privada que o usuário atual parou de digitar."""
    if not current_user.is_authenticated:
        return

    room = data.get('room')
    if room:
        payload = {'username': current_user.username}
        emit('user_typing_stop', payload, to=room, include_self=False)
