# plataforma_ead/app/admin.py (VERSÃO FINAL COM TODAS AS CORREÇÕES)

from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for
from werkzeug.security import generate_password_hash

from wtforms_sqlalchemy.fields import QuerySelectField
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, BooleanField, PasswordField

from .models import User, Course, Lesson, Quiz, Question, Answer
from . import db


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('main.pagina_principal'))
        return super(MyAdminIndexView, self).index()


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.pagina_principal'))


class UserAdminForm(FlaskForm):
    username = StringField('Username')
    email = StringField('Email')
    full_name = StringField('Nome Completo')
    score = IntegerField('Pontuação', render_kw={'readonly': True})
    bio = TextAreaField('Biografia')
    is_admin = BooleanField('É Admin?')
    password = PasswordField('Nova Senha [deixe em branco para não alterar]')


class UserAdminView(SecureModelView):
    form = UserAdminForm
    column_list = ['username', 'email', 'full_name', 'score', 'is_admin']
    def on_model_change(self, form, model, is_created):
        if form.password.data and form.password.data.strip():
            model.password_hash = generate_password_hash(form.password.data, method='pbkdf2:sha256')


# --- CLASSE MODIFICADA ABAIXO ---
class AnswerAdminView(SecureModelView):
    column_list = ['text', 'is_correct', 'question']
    form_columns = ['question', 'text', 'is_correct']

    # Adiciona a configuração explícita para o campo de seleção 'question'
    form_overrides = {
        'question': QuerySelectField
    }

    form_args = {
        'question': {
            'query_factory': lambda: Question.query.all(),
            'allow_blank': False,
            # Usamos o __str__ do model Question, que já formata o texto
            'get_label': str
        }
    }


class LessonAdminView(SecureModelView):
    column_list = ['title', 'course']
    form_columns = ['course', 'title', 'content']

    form_overrides = {
        'course': QuerySelectField
    }

    form_args = {
        'course': {
            'query_factory': lambda: Course.query.all(),
            'allow_blank': False,
            'get_label': 'title'
        }
    }


class QuizAdminView(SecureModelView):
    column_list = ['title', 'lesson']
    form_columns = ['lesson', 'title']

    form_overrides = {
        'lesson': QuerySelectField
    }

    form_args = {
        'lesson': {
            'query_factory': lambda: Lesson.query.all(),
            'allow_blank': False,
            'get_label': 'title'
        }
    }


class QuestionAdminView(SecureModelView):
    column_list = ['text', 'quiz']
    form_columns = ['quiz', 'text']

    form_overrides = {
        'quiz': QuerySelectField
    }

    form_args = {
        'quiz': {
            'query_factory': lambda: Quiz.query.all(),
            'allow_blank': False,
            'get_label': 'title'
        }
    }


admin = Admin(name='Plataforma EAD Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())


admin.add_view(UserAdminView(User, db.session, name='Usuários'))
admin.add_view(SecureModelView(Course, db.session, name='Cursos'))
admin.add_view(LessonAdminView(Lesson, db.session, name='Aulas'))
admin.add_view(QuizAdminView(Quiz, db.session, name='Simulados'))
admin.add_view(QuestionAdminView(Question, db.session, name='Perguntas'))
admin.add_view(AnswerAdminView(Answer, db.session, name='Respostas'))