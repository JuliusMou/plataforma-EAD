# run.py

import eventlet
eventlet.monkey_patch()

from app import create_app, db, socketio
from app.models import User, Course, Lesson, Quiz, Question, Answer, Friendship, Enrollment
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
        'Quiz': Quiz,
        'Question': Question,
        'Answer': Answer,
        'Friendship': Friendship,
        'Enrollment': Enrollment
    }

# --- COMANDOS DE POVOAMENTO (SEED) ---

def _create_users():
    """Função auxiliar para criar usuários."""
    users_data = [
        {'username': 'admin', 'email': 'admin@ead.com', 'password': 'admin', 'full_name': 'Admin da Plataforma', 'bio': 'Eu sou o administrador.', 'profile_picture': 'default.jpg', 'is_admin': True},
        {'username': 'ana.silva', 'email': 'ana.silva@example.com', 'password': 'password123', 'full_name': 'Ana Silva', 'bio': 'Engenheira eletricista apaixonada por automação residencial.', 'profile_picture': 'u1.jpg'},
        {'username': 'bruno.costa', 'email': 'bruno.costa@example.com', 'password': 'password123', 'full_name': 'Bruno Costa', 'bio': 'Técnico em eletrotécnica com foco em energias renováveis.', 'profile_picture': 'u2.jpg'},
        {'username': 'carla.souza', 'email': 'carla.souza@example.com', 'password': 'password123', 'full_name': 'Carla Souza', 'bio': 'Estudante de engenharia de controle e automação.', 'profile_picture': 'u3.jpg'},
        {'username': 'diego.santos', 'email': 'diego.santos@example.com', 'password': 'password123', 'full_name': 'Diego Santos', 'bio': 'Projetista de painéis elétricos industriais.', 'profile_picture': 'u4.jpg'},
    ]
    
    for user_data in users_data:
        user = User.query.filter_by(email=user_data['email']).first()
        if not user:
            password_hash = generate_password_hash(user_data['password'], method='pbkdf2:sha256')
            new_user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=password_hash,
                full_name=user_data.get('full_name'),
                bio=user_data.get('bio'),
                profile_picture=user_data.get('profile_picture', 'default.jpg'),
                is_admin=user_data.get('is_admin', False),
                score=0,
                confirmed=True 
            )
            db.session.add(new_user)
    db.session.commit()
    click.echo('Usuários de teste criados com sucesso.')

def _create_courses_and_lessons():
    """Função auxiliar para criar cursos, aulas e simulados."""
    # Curso 1: Comandos Elétricos
    course1 = Course.query.filter_by(title='Fundamentos de Comandos Elétricos').first()
    if not course1:
        course1 = Course(
            title='Fundamentos de Comandos Elétricos',
            description='Aprenda a lógica por trás de partidas de motores, contatores e relés. Essencial para qualquer eletricista industrial.',
            category='Eletrotécnica'
        )
        db.session.add(course1)
        
        # Aulas para o Curso 1
        l1_1 = Lesson(title='Introdução a Contatores', content='Nesta aula, veremos o princípio de funcionamento de um contator...', course=course1)
        l1_2 = Lesson(title='Partida Direta de Motores', content='A partida direta é o método mais simples de acionamento de motores trifásicos...', course=course1)
        l1_3 = Lesson(title='Simulado Final de Comandos', content='Teste seus conhecimentos sobre comandos elétricos.', course=course1)
        db.session.add_all([l1_1, l1_2, l1_3])

        # Simulado para a Aula 3 do Curso 1
        quiz1 = Quiz(title='Avaliação de Comandos Elétricos', lesson=l1_3)
        db.session.add(quiz1)
        q1 = Question(text='Qual o principal componente para uma partida direta?', quiz=quiz1)
        db.session.add(q1)
        db.session.add_all([
            Answer(text='Um disjuntor', is_correct=False, question=q1),
            Answer(text='Um contator', is_correct=True, question=q1),
            Answer(text='Um relé térmico', is_correct=False, question=q1),
        ])

    # Curso 2: CLP Básico
    course2 = Course.query.filter_by(title='CLP Básico: Lógica Ladder').first()
    if not course2:
        course2 = Course(
            title='CLP Básico: Lógica Ladder',
            description='Introdução à programação de Controladores Lógicos Programáveis (CLP) utilizando a linguagem Ladder.',
            category='Automação Industrial'
        )
        db.session.add(course2)
        
        # Aulas para o Curso 2
        l2_1 = Lesson(title='O que é um CLP?', content='CLPs são computadores industriais robustos que controlam processos...', course=course2)
        l2_2 = Lesson(title='Contatos NA e NF', content='A base da lógica Ladder são os contatos Normalmente Abertos (NA) e Normalmente Fechados (NF)...', course=course2)
        db.session.add_all([l2_1, l2_2])

    db.session.commit()
    click.echo('Cursos, aulas e simulados de teste criados com sucesso.')

def _create_social_features():
    """Função auxiliar para criar amizades e inscrições."""
    user_ana = User.query.filter_by(username='ana.silva').first()
    user_bruno = User.query.filter_by(username='bruno.costa').first()
    user_carla = User.query.filter_by(username='carla.souza').first()
    
    course_clp = Course.query.filter_by(title='CLP Básico: Lógica Ladder').first()
    course_comandos = Course.query.filter_by(title='Fundamentos de Comandos Elétricos').first()

    # Inscrições
    if user_ana and course_comandos and not user_ana.is_enrolled(course_comandos):
        user_ana.enroll(course_comandos)
    if user_bruno and course_comandos and not user_bruno.is_enrolled(course_comandos):
        user_bruno.enroll(course_comandos)
    if user_ana and course_clp and not user_ana.is_enrolled(course_clp):
        user_ana.enroll(course_clp)

    # Amizades
    # Ana e Bruno já são amigos
    f1 = Friendship.query.filter_by(requester_id=user_ana.id, addressee_id=user_bruno.id).first()
    if not f1:
        db.session.add(Friendship(requester=user_ana, addressee=user_bruno, status='accepted'))

    # Carla enviou um pedido para Ana
    f2 = Friendship.query.filter_by(requester_id=user_carla.id, addressee_id=user_ana.id).first()
    if not f2:
        db.session.add(Friendship(requester=user_carla, addressee=user_ana, status='pending', message='Oi Ana, vi que você também curte automação! Vamos nos conectar?'))
    
    db.session.commit()
    click.echo('Inscrições e amizades de teste criadas com sucesso.')


# --- COMANDO PRINCIPAL: seed-all ---
@app.cli.command('seed-all')
def seed_all_command():
    """
    Apaga o banco de dados e o repovoa com dados de teste (usuários, cursos, etc).
    Ideal para o ambiente de desenvolvimento não persistente.
    """
    click.confirm('Isso irá apagar todos os dados do banco de dados. Deseja continuar?', abort=True)
    
    click.echo('Apagando tabelas...')
    db.drop_all()
    
    click.echo('Criando tabelas...')
    db.create_all()

    click.echo('Iniciando povoamento...')
    _create_users()
    _create_courses_and_lessons()
    _create_social_features()
    
    click.secho('*** BANCO DE DADOS POVOADO COM SUCESSO! ***', fg='green')


if __name__ == '__main__':
    # Agora usamos socketio.run() para iniciar o servidor correto
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
