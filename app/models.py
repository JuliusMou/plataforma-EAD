# plataforma_ead/app/models.py (VERSÃO ESTÁVEL)

from . import db
from datetime import datetime
from flask_login import UserMixin
from app import login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
    # O relacionamento 'completed_lessons' e o método 'has_completed_lesson' foram removidos.

    def __repr__(self):
        return f'<User {self.username}>'

    def __str__(self):
        return self.username


class Course(db.Model):
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

# A tabela 'lesson_completions' e o model 'Friendship' foram removidos.