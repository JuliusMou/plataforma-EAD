from app import create_app, db
# Removido werkzeug e click, pois não são mais usados aqui
from app.models import User, Course, Lesson, Quiz

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Torna variáveis acessíveis no 'flask shell'.
    """
    return {
        'db': db,
        'User': User,
        'Course': Course,
        'Lesson': Lesson,
        'Quiz': Quiz
        # Removido Friendship
    }

# O comando de terminal 'create-users' foi removido.

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)