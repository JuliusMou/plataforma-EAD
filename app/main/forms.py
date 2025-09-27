# app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
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

# A classe SearchForm foi removida.