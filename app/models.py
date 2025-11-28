# app/models.py

from . import db
from datetime import datetime, timedelta
from flask_login import UserMixin
from app import login_manager
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous.exc import SignatureExpired, BadTimeSignature
from sqlalchemy import func, or_


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


lesson_completions = db.Table('lesson_completions',
                              db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                              db.Column('lesson_id', db.Integer, db.ForeignKey('lessons.id'), primary_key=True)
                              )


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    score = db.Column(db.Integer, default=0)

    user = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')


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
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

    completed_lessons = db.relationship('Lesson', secondary=lesson_completions,
                                        lazy='subquery',
                                        backref=db.backref('completed_by_users', lazy=True))
    ratings = db.relationship('CourseRating', backref='user', lazy='dynamic')
    enrollments = db.relationship('Enrollment', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

    def is_enrolled(self, course):
        return self.enrollments.filter_by(course_id=course.id).count() > 0

    def enroll(self, course):
        if not self.is_enrolled(course):
            enrollment = Enrollment(user=self, course=course)
            db.session.add(enrollment)

    def unenroll(self, course):
        enrollment = self.enrollments.filter_by(course_id=course.id).first()
        if enrollment:
            db.session.delete(enrollment)

    def get_enrollment_for(self, course):
        return self.enrollments.filter_by(course_id=course.id).first()

    def get_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.id)

    @staticmethod
    def verify_confirmation_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=3600)
        except (SignatureExpired, BadTimeSignature):
            return None
        return User.query.get(user_id)

    def get_reset_password_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.id)

    @staticmethod
    def verify_reset_password_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)
        except (SignatureExpired, BadTimeSignature):
            return None
        return User.query.get(user_id)

    def has_completed_lesson(self, lesson):
        return lesson in self.completed_lessons

    def get_friends(self):
        friends = []
        sent_requests = Friendship.query.filter_by(requester_id=self.id, status='accepted').all()
        for req in sent_requests:
            friends.append(req.addressee)
        received_requests = Friendship.query.filter_by(addressee_id=self.id, status='accepted').all()
        for req in received_requests:
            friends.append(req.requester)
        return friends

    def is_online(self):
        if self.last_seen:
            time_difference = datetime.utcnow() - self.last_seen
            return time_difference < timedelta(minutes=5)
        return False

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
    ratings = db.relationship('CourseRating', backref='course', lazy='dynamic')
    enrollments = db.relationship('Enrollment', back_populates='course', lazy='dynamic', cascade="all, delete-orphan")

    def average_rating(self):
        avg = db.session.query(func.avg(CourseRating.stars)).filter(CourseRating.course_id == self.id).scalar()
        return round(avg, 1) if avg else 0

    def user_rating(self, user):
        if not user.is_authenticated:
            return None
        rating = self.ratings.filter_by(user_id=user.id).first()
        return rating.stars if rating else None

    def __repr__(self):
        return f'<Course {self.title}>'

    def __str__(self):
        return self.title


class CourseRating(db.Model):
    __tablename__ = 'course_ratings'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    stars = db.Column(db.Integer, nullable=False)


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
        return self.text if len(self.text) <= 80 else self.text[:80] + '...'


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
        return self.text if len(self.text) <= 80 else self.text[:80] + '...'


class Friendship(db.Model):
    __tablename__ = 'friendships'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # status: pending, accepted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- NOVO CAMPO ADICIONADO ---
    message = db.Column(db.Text, nullable=True)  # Mensagem opcional no pedido de amizade

    requester = db.relationship('User', foreign_keys=[requester_id], backref='sent_friend_requests')
    addressee = db.relationship('User', foreign_keys=[addressee_id], backref='received_friend_requests')

    def __repr__(self):
        return f'<Friendship from {self.requester.username} to {self.addressee.username} - Status: {self.status}>'


# --- NOVO MODELO PARA MENSAGENS PRIVADAS ---
class PrivateMessage(db.Model):
    __tablename__ = 'private_messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    # Relacionamentos para acessar os objetos User
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    def __repr__(self):
        return f'<PrivateMessage from {self.sender.username} to {self.recipient.username}>'


class ContentSuggestion(db.Model):
    __tablename__ = 'content_suggestions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # podcast, artigo, video, curso, outro
    status = db.Column(db.String(20), default='pendente', nullable=False)  # pendente, aprovado, rejeitado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('suggestions', lazy=True))

    def __repr__(self):
        return f'<ContentSuggestion {self.title}>'


class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    topics = db.relationship('ForumTopic', backref='category', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ForumCategory {self.name}>'


class ForumTopic(db.Model):
    __tablename__ = 'forum_topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('topics', lazy=True))
    posts = db.relationship('ForumPost', backref='topic', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ForumTopic {self.title}>'


class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('posts', lazy=True))

    def __repr__(self):
        return f'<ForumPost by {self.user.username} on topic {self.topic_id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('activities', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<ActivityLog {self.event_type} by {self.user.username}>'


class CourseLike(db.Model):
    __tablename__ = 'course_likes'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    is_like = db.Column(db.Boolean, nullable=False) # True = Like, False = Dislike

    user = db.relationship('User', backref=db.backref('course_likes', lazy='dynamic', cascade="all, delete-orphan"))
    course = db.relationship('Course', backref=db.backref('likes', lazy='dynamic', cascade="all, delete-orphan"))