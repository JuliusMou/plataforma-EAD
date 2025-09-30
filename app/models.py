from . import db
from datetime import datetime, timedelta  # Adicione timedelta
from flask_login import UserMixin
from app import login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


lesson_completions = db.Table('lesson_completions',
                              db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                              db.Column('lesson_id', db.Integer, db.ForeignKey('lessons.id'), primary_key=True)
                              )


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    full_name = db.Column(db.String(120), nullable=True)
    score = db.Column(db.Integer, server_default='0', nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=False, server_default='default.jpg')
    is_admin = db.Column(db.Boolean, server_default='f', nullable=False)

    # --- NOVO CAMPO ADICIONADO ---
    # Armazena a última vez que o usuário fez uma requisição.
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    completed_lessons = db.relationship('Lesson', secondary=lesson_completions,
                                        lazy='subquery',
                                        backref=db.backref('completed_by_users', lazy=True))

    def has_completed_lesson(self, lesson):
        """Verifica se o usuário já completou uma aula específica."""
        return lesson in self.completed_lessons

    def get_friends(self):
        """ Retorna uma lista de usuários que são amigos. """
        friends = []
        sent_requests = Friendship.query.filter_by(requester_id=self.id, status='accepted').all()
        for req in sent_requests:
            friends.append(req.addressee)

        received_requests = Friendship.query.filter_by(addressee_id=self.id, status='accepted').all()
        for req in received_requests:
            friends.append(req.requester)

        return friends

    # --- NOVO MÉTODO ADICIONADO ---
    def is_online(self):
        """
        Verifica se o usuário esteve ativo nos últimos 5 minutos.
        Retorna True se estiver online, False caso contrário.
        """
        if self.last_seen:
            # Calcula a diferença entre o tempo atual e a última vez que o usuário foi visto
            time_difference = datetime.utcnow() - self.last_seen
            # Retorna True se a diferença for menor que 5 minutos
            return time_difference < timedelta(minutes=5)
        return False

    def __repr__(self):
        return f'<User {self.username}>'

    def __str__(self):
        return self.username


# ... O restante do arquivo (Course, Lesson, Quiz, etc.) permanece o mesmo ...
class Course(db.Model):
    # ... (sem alterações)
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lessons = db.relationship('Lesson', back_populates='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.title}>'

    def __str__(self):
        return self.title


class Lesson(db.Model):
    # ... (sem alterações)
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    quiz = db.relationship('Quiz', back_populates='lesson', lazy=True, uselist=False, cascade="all, delete-orphan")
    course = db.relationship('Course', back_populates='lessons')

    def __repr__(self):
        return f'<Lesson {self.title}>'

    def __str__(self):
        return self.title


class Quiz(db.Model):
    # ... (sem alterações)
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False, unique=True)
    questions = db.relationship('Question', back_populates='quiz', lazy=True, cascade="all, delete-orphan")
    lesson = db.relationship('Lesson', back_populates='quiz')

    def __repr__(self):
        return f'<Quiz {self.title}>'

    def __str__(self):
        return self.title


class Question(db.Model):
    # ... (sem alterações)
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    answers = db.relationship('Answer', back_populates='question', lazy=True, cascade="all, delete-orphan")
    quiz = db.relationship('Quiz', back_populates='questions')

    def __repr__(self):
        return f'<Question {self.text[:30]}>'

    def __str__(self):
        if len(self.text) > 80:
            return self.text[:80] + '...'
        return self.text


class Answer(db.Model):
    # ... (sem alterações)
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    question = db.relationship('Question', back_populates='answers')

    def __repr__(self):
        return f'<Answer {self.text[:30]}>'

    def __str__(self):
        if len(self.text) > 80:
            return self.text[:80] + '...'
        return self.text


class Friendship(db.Model):
    # ... (sem alterações)
    __tablename__ = 'friendships'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requester = db.relationship('User', foreign_keys=[requester_id], backref='sent_friend_requests')
    addressee = db.relationship('User', foreign_keys=[addressee_id], backref='received_friend_requests')

    def __repr__(self):
        return f'<Friendship from {self.requester.username} to {self.addressee.username} - Status: {self.status}>'