# app/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

class PasswordResetRequestForm(FlaskForm):
    """
    Formulário para solicitar a redefinição de senha.
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Link de Redefinição')


class ResetPasswordForm(FlaskForm):
    """
    Formulário para redefinir a senha.
    """
    password = PasswordField('Nova Senha', validators=[DataRequired()])
    password2 = PasswordField(
        'Confirme a Nova Senha', validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais.')])
    submit = SubmitField('Redefinir Senha')