from app import db
from app.models import ActivityLog

def log_user_activity(user, event_type, details=None):
    """
    Registra uma atividade do usuário no banco de dados.

    :param user: Objeto User (geralmente current_user)
    :param event_type: String identificando o tipo de evento (ex: 'lesson_completed', 'forum_post')
    :param details: String opcional com detalhes (ex: 'Título da Aula', 'Nome do Amigo')
    """
    try:
        activity = ActivityLog(
            user=user,
            event_type=event_type,
            details=details
        )
        db.session.add(activity)
        # O commit é deixado para o chamador ou hook de request para evitar múltiplos commits,
        # mas em casos isolados pode ser útil commitar aqui.
        # Por segurança, vamos apenas adicionar à sessão.
    except Exception as e:
        print(f"Erro ao registrar atividade: {e}")
