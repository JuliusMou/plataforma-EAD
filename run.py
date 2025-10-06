# run.py

# --- IMPORTAÇÃO MODIFICADA ---
# Importamos 'socketio' junto com 'create_app' e 'db'
from app import create_app, db, socketio
from app.models import User, Course, Lesson, Quiz
from werkzeug.security import generate_password_hash
import click

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
    }


@app.cli.command('create-users')
def create_users_command():
    """Cria 10 usuários de teste para a plataforma."""

    novos_usuarios = [
        {'username': 'ana.silva', 'email': 'ana.silva@example.com', 'password': 'password123', 'full_name': 'Ana Silva',
         'bio': 'Engenheira eletricista apaixonada por automação residencial.', 'profile_picture': 'u1.jpg'},
        {'username': 'bruno.costa', 'email': 'bruno.costa@example.com', 'password': 'password123',
         'full_name': 'Bruno Costa', 'bio': 'Técnico em eletrotécnica com foco em energias renováveis.',
         'profile_picture': 'u2.jpg'},
        {'username': 'carla.souza', 'email': 'carla.souza@example.com', 'password': 'password123',
         'full_name': 'Carla Souza', 'bio': 'Estudante de engenharia de controle e automação.',
         'profile_picture': 'u3.jpg'},
        {'username': 'diego.santos', 'email': 'diego.santos@example.com', 'password': 'password123',
         'full_name': 'Diego Santos', 'bio': 'Projetista de painéis elétricos industriais.',
         'profile_picture': 'u4.jpg'},
        {'username': 'eduardo.lima', 'email': 'eduardo.lima@example.com', 'password': 'password123',
         'full_name': 'Eduardo Lima', 'bio': 'Especialista em CLP e IHM, transformando indústrias.',
         'profile_picture': 'u5.jpg'},
        {'username': 'fabiana.gomes', 'email': 'fabiana.gomes@example.com', 'password': 'password123',
         'full_name': 'Fabiana Gomes', 'bio': 'Automação de processos industriais é a minha paixão.',
         'profile_picture': 'u6.jpg'},
        {'username': 'gustavo.alves', 'email': 'gustavo.alves@example.com', 'password': 'password123',
         'full_name': 'Gustavo Alves', 'bio': 'Fascinado por robótica colaborativa e sistemas embarcados.',
         'profile_picture': 'u7.jpg'},
        {'username': 'helena.rocha', 'email': 'helena.rocha@example.com', 'password': 'password123',
         'full_name': 'Helena Rocha', 'bio': 'Consultora em eficiência energética e smart grids.',
         'profile_picture': 'u8.jpg'},
        {'username': 'igor.martins', 'email': 'igor.martins@example.com', 'password': 'password123',
         'full_name': 'Igor Martins', 'bio': 'Técnico de manutenção preditiva em campo, sempre pronto para um desafio.',
         'profile_picture': 'u9.jpg'},
        {'username': 'julia.pereira', 'email': 'julia.pereira@example.com', 'password': 'password123',
         'full_name': 'Julia Pereira', 'bio': 'Apaixonada por instalações elétricas prediais e domótica.',
         'profile_picture': 'u10.jpg'}
    ]

    click.echo('Iniciando a criação de usuários de teste...')
    for user_data in novos_usuarios:
        existing_user = User.query.filter(
            (User.username == user_data['username']) | (User.email == user_data['email'])).first()
        if existing_user:
            click.echo(f"Usuário '{user_data['username']}' já existe. Pulando.")
            continue

        password_hash = generate_password_hash(user_data['password'], method='pbkdf2:sha256')
        novo_usuario = User(
            username=user_data['username'],
            email=user_data['email'],
            password_hash=password_hash,
            full_name=user_data['full_name'],
            bio=user_data['bio'],
            profile_picture=user_data['profile_picture'],
            score=0,
            confirmed=True # Confirmando usuários de teste automaticamente
        )
        db.session.add(novo_usuario)
        click.echo(f"Usuário '{user_data['username']}' preparado para ser adicionado.")

    try:
        db.session.commit()
        click.secho('\\n*** SUCESSO! ***', fg='green', bold=True)
        click.echo('Novos usuários foram salvos no banco de dados.')
    except Exception as e:
        db.session.rollback()
        click.secho(f'\\nOcorreu um erro ao salvar: {e}', fg='red')


@app.cli.command('create-courses')
def create_courses_command():
    """Cria 10 cursos de teste para a plataforma."""
    # (O conteúdo deste comando permanece o mesmo, foi omitido para brevidade)
    pass # Remova este pass se for colar o conteúdo do comando


if __name__ == '__main__':
    # --- MODO DE EXECUÇÃO ALTERADO ---
    # Agora usamos socketio.run() para iniciar o servidor correto
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
