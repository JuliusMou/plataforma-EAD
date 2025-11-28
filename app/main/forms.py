# app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

class EditProfileForm(FlaskForm):
    """
    Formulário para editar o perfil do usuário.
    """
    # Campo para o nome completo, com validador de tamanho.
    full_name = StringField('Nome Completo', validators=[Length(0, 120)])

    # Campo para a biografia, com validador de tamanho.
    bio = TextAreaField('Biografia', validators=[Length(0, 500)])

    # Botão de envio do formulário.
    submit = SubmitField('Salvar Alterações')

class ContentSuggestionForm(FlaskForm):
    """
    Formulário para sugestão de novos conteúdos.
    """
    title = StringField('Título', validators=[DataRequired(), Length(min=5, max=150)])
    description = TextAreaField('Descrição Detalhada', validators=[DataRequired(), Length(min=20, max=1000)])
    content_type = SelectField('Tipo de Conteúdo', choices=[
        ('podcast', 'Podcast'),
        ('artigo', 'Artigo'),
        ('video', 'Vídeo'),
        ('curso', 'Curso Completo'),
        ('outro', 'Outro')
    ], validators=[DataRequired()])
    submit = SubmitField('Enviar Sugestão')

class TopicForm(FlaskForm):
    """
    Formulário para criar um novo tópico no fórum.
    """
    title = StringField('Título do Tópico', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('Conteúdo', validators=[DataRequired(), Length(min=10, max=5000)])
    category = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Criar Tópico')

class PostForm(FlaskForm):
    """
    Formulário para responder a um tópico.
    """
    content = TextAreaField('Sua Resposta', validators=[DataRequired(), Length(min=2, max=2000)])
    submit = SubmitField('Responder')