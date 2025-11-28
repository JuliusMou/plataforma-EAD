from app import create_app, db
from app.models import User, Course, Lesson, Quiz, Question, Answer, Friendship, Enrollment, ContentSuggestion, ForumCategory, ForumTopic, ForumPost, ActivityLog
from werkzeug.security import generate_password_hash
from datetime import datetime

def populate():
    app = create_app()
    with app.app_context():
        print("Apagando tabelas...")
        db.drop_all()
        print("Criando tabelas...")
        db.create_all()

        # --- USUÁRIOS ---
        print("Criando usuários...")
        users_data = [
            {'username': 'admin', 'email': 'admin@ead.com', 'password': 'admin', 'full_name': 'Admin da Plataforma', 'bio': 'Eu sou o administrador.', 'profile_picture': 'default.jpg', 'is_admin': True},
            {'username': 'ana.silva', 'email': 'ana.silva@example.com', 'password': 'password123', 'full_name': 'Ana Silva', 'bio': 'Engenheira eletricista apaixonada por automação residencial.', 'profile_picture': 'u1.jpg'},
            {'username': 'bruno.costa', 'email': 'bruno.costa@example.com', 'password': 'password123', 'full_name': 'Bruno Costa', 'bio': 'Técnico em eletrotécnica com foco em energias renováveis.', 'profile_picture': 'u2.jpg'},
            {'username': 'carla.souza', 'email': 'carla.souza@example.com', 'password': 'password123', 'full_name': 'Carla Souza', 'bio': 'Estudante de engenharia de controle e automação.', 'profile_picture': 'u3.jpg'},
            {'username': 'diego.santos', 'email': 'diego.santos@example.com', 'password': 'password123', 'full_name': 'Diego Santos', 'bio': 'Projetista de painéis elétricos industriais.', 'profile_picture': 'u4.jpg'},
            {'username': 'eduardo.lima', 'email': 'eduardo.lima@example.com', 'password': 'password123', 'full_name': 'Eduardo Lima', 'bio': 'Entusiasta de IoT e automação.', 'profile_picture': 'default.jpg'},
            {'username': 'fernanda.oliveira', 'email': 'fernanda.oliveira@example.com', 'password': 'password123', 'full_name': 'Fernanda Oliveira', 'bio': 'Engenheira de Sistemas.', 'profile_picture': 'default.jpg'},
            {'username': 'gabriel.almeida', 'email': 'gabriel.almeida@example.com', 'password': 'password123', 'full_name': 'Gabriel Almeida', 'bio': 'Técnico em Eletrônica.', 'profile_picture': 'default.jpg'},
        ]

        created_users = {}
        for user_data in users_data:
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
            created_users[user_data['username']] = new_user

        db.session.commit() # Commit para obter os IDs

        # --- CURSOS E AULAS ---
        print("Criando cursos e aulas...")
        # Curso 1
        course1 = Course(
            title='Fundamentos de Comandos Elétricos',
            description='Aprenda a lógica por trás de partidas de motores, contatores e relés. Essencial para qualquer eletricista industrial.',
            category='Eletrotécnica'
        )
        db.session.add(course1)
        l1_1 = Lesson(title='Introdução a Contatores', content='Nesta aula, veremos o princípio de funcionamento de um contator...', course=course1)
        l1_2 = Lesson(title='Partida Direta de Motores', content='A partida direta é o método mais simples de acionamento de motores trifásicos...', course=course1)
        l1_3 = Lesson(title='Simulado Final de Comandos', content='Teste seus conhecimentos sobre comandos elétricos.', course=course1)
        db.session.add_all([l1_1, l1_2, l1_3])

        quiz1 = Quiz(title='Avaliação de Comandos Elétricos', lesson=l1_3)
        db.session.add(quiz1)
        q1 = Question(text='Qual o principal componente para uma partida direta?', quiz=quiz1)
        db.session.add(q1)
        db.session.add_all([
            Answer(text='Um disjuntor', is_correct=False, question=q1),
            Answer(text='Um contator', is_correct=True, question=q1),
            Answer(text='Um relé térmico', is_correct=False, question=q1),
        ])

        # Curso 2
        course2 = Course(
            title='CLP Básico: Lógica Ladder',
            description='Introdução à programação de Controladores Lógicos Programáveis (CLP) utilizando a linguagem Ladder.',
            category='Automação Industrial'
        )
        db.session.add(course2)
        l2_1 = Lesson(title='O que é um CLP?', content='CLPs são computadores industriais robustos que controlam processos...', course=course2)
        l2_2 = Lesson(title='Contatos NA e NF', content='A base da lógica Ladder são os contatos Normalmente Abertos (NA) e Normalmente Fechados (NF)...', course=course2)
        db.session.add_all([l2_1, l2_2])

        # Curso 3
        course3 = Course(
            title='Segurança em Instalações NR-10',
            description='Curso obrigatório para profissionais que interagem com instalações elétricas e serviços com eletricidade.',
            category='Segurança do Trabalho'
        )
        db.session.add(course3)
        l3_1 = Lesson(title='Introdução à NR-10', content='A Norma Regulamentadora 10 estabelece os requisitos e condições mínimas...', course=course3)
        l3_2 = Lesson(title='Riscos Elétricos', content='Choque elétrico, arco elétrico, campos eletromagnéticos...', course=course3)
        db.session.add_all([l3_1, l3_2])

        # Curso 4
        course4 = Course(
            title='Inversores de Frequência',
            description='Domine o controle de velocidade de motores elétricos trifásicos.',
            category='Automação Industrial'
        )
        db.session.add(course4)
        l4_1 = Lesson(title='Princípio de Funcionamento', content='Como o inversor converte CA em CC e depois em CA novamente com frequência variável.', course=course4)
        db.session.add(l4_1)

        db.session.commit()

        # --- INTERAÇÕES ---
        print("Criando inscrições, amizades e sugestões...")

        user_ana = User.query.filter_by(username='ana.silva').first()
        user_bruno = User.query.filter_by(username='bruno.costa').first()
        user_carla = User.query.filter_by(username='carla.souza').first()
        user_eduardo = User.query.filter_by(username='eduardo.lima').first()

        # Inscrições
        if user_ana:
            user_ana.enroll(course1)
            user_ana.enroll(course2)
        if user_bruno: user_bruno.enroll(course1)
        if user_eduardo: user_eduardo.enroll(course3)

        # Amizades
        if user_ana and user_bruno:
             db.session.add(Friendship(requester=user_ana, addressee=user_bruno, status='accepted'))

        if user_carla and user_ana:
            db.session.add(Friendship(requester=user_carla, addressee=user_ana, status='pending', message='Oi Ana, vi que você também curte automação! Vamos nos conectar?'))

        # Sugestões
        if user_ana:
            s1 = ContentSuggestion(
                user=user_ana,
                title='Podcast sobre Indústria 4.0',
                description='Seria muito legal ter um episódio discutindo os impactos da indústria 4.0 no mercado de trabalho.',
                content_type='podcast',
                status='pendente'
            )
            db.session.add(s1)

        if user_bruno:
            s2 = ContentSuggestion(
                user=user_bruno,
                title='Curso avançado de Altium Designer',
                description='Falta conteúdo sobre criação de PCBs profissionais.',
                content_type='curso',
                status='aprovado'
            )
            db.session.add(s2)

        # --- FÓRUM ---
        print("Criando categorias e tópicos do fórum...")

        cat1 = ForumCategory(name='Dúvidas Gerais', description='Espaço para dúvidas sobre a plataforma e cursos.', slug='duvidas-gerais')
        cat2 = ForumCategory(name='Eletrotécnica', description='Discussões técnicas sobre elétrica.', slug='eletrotecnica')
        cat3 = ForumCategory(name='Automação Industrial', description='Tudo sobre CLPs, IHM e SCADA.', slug='automacao')
        cat4 = ForumCategory(name='Carreira', description='Dicas de emprego e mercado de trabalho.', slug='carreira')

        db.session.add_all([cat1, cat2, cat3, cat4])
        db.session.commit()

        if user_ana:
            t1 = ForumTopic(
                title='Qual o melhor CLP para iniciantes?',
                content='Estou querendo comprar um CLP para treinar em casa. Qual vocês recomendam que tenha um bom custo-benefício e software gratuito?',
                user=user_ana,
                category=cat3,
                views=15
            )
            db.session.add(t1)
            db.session.commit() # Precisa do ID do tópico

            if user_bruno:
                p1 = ForumPost(
                    content='Recomendo o Logo! da Siemens ou o Click da AutomationDirect. São ótimos para começar.',
                    user=user_bruno,
                    topic=t1
                )
                db.session.add(p1)

            if user_eduardo:
                p2 = ForumPost(
                    content='Também tem os da WEG, linha Clic02. Software em português e bem intuitivo.',
                    user=user_eduardo,
                    topic=t1
                )
                db.session.add(p2)

        # --- ATIVIDADES (Timeline) ---
        print("Criando logs de atividades...")
        if user_ana:
            db.session.add(ActivityLog(user=user_ana, event_type='lesson_completed', details='Concluiu a aula: Introdução a Contatores'))
            db.session.add(ActivityLog(user=user_ana, event_type='forum_topic', details='Criou o tópico: Qual o melhor CLP para iniciantes?'))
        if user_bruno:
            db.session.add(ActivityLog(user=user_bruno, event_type='forum_post', details='Respondeu ao tópico: Qual o melhor CLP para iniciantes?'))
            db.session.add(ActivityLog(user=user_bruno, event_type='new_friend', details='Agora é amigo de ana.silva'))

        db.session.commit()
        print("*** SUCESSO! Banco de dados recriado e povoado. ***")

if __name__ == '__main__':
    populate()
