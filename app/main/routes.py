import markdown
from . import main
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request
from app.models import User, Course, Lesson, Question, Answer, Quiz
from app import db
from .forms import EditProfileForm

@main.app_template_filter('markdown_to_html')
def markdown_to_html(text):
    """Converte uma string de texto em Markdown para HTML."""
    return markdown.markdown(text)

# --- NOVA ROTA ADICIONADA ---
@main.route('/usuarios')
@login_required
def pagina_usuarios():
    """ Exibe uma lista de todos os usuários da plataforma. """
    # A consulta agora busca todos os usuários, exceto o que está logado.
    all_users = User.query.filter(User.id != current_user.id).order_by(User.username.asc()).all()
    return render_template('main/users.html', users=all_users)


@main.route('/')
@login_required
def pagina_principal():
    return render_template('main/index.html')

@main.route('/perfil/<username>')
@login_required
def pagina_perfil(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('main/profile.html', user=user)

@main.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        db.session.add(current_user)
        db.session.commit()
        flash('Seu perfil foi atualizado com sucesso!')
        return redirect(url_for('main.pagina_perfil', username=current_user.username))
    form.full_name.data = current_user.full_name
    form.bio.data = current_user.bio
    return render_template('main/edit_profile.html', form=form)

@main.route('/cursos')
@login_required
def pagina_cursos():
    cursos = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('main/courses.html', cursos=cursos)

@main.route('/cursos/<int:course_id>')
@login_required
def pagina_curso(course_id):
    curso = Course.query.get_or_404(course_id)
    return render_template('main/course_detail.html', curso=curso)

@main.route('/cursos/<int:course_id>/aula/<int:lesson_id>')
@login_required
def pagina_aula(course_id, lesson_id):
    aula = Lesson.query.get_or_404(lesson_id)
    return render_template('main/lesson_detail.html', aula=aula)

@main.route('/aula/concluir/<int:lesson_id>', methods=['POST'])
@login_required
def concluir_aula(lesson_id):
    aula = Lesson.query.get_or_404(lesson_id)
    # Lógica de pontuação simplificada por enquanto
    current_user.score += 10
    db.session.commit()
    flash(f'Parabéns! Você concluiu a aula "{aula.title}" e ganhou 10 pontos!', 'success')
    return redirect(url_for('main.pagina_aula', course_id=aula.course.id, lesson_id=aula.id))

@main.app_context_processor
def inject_ranking():
    top_users = User.query.order_by(User.score.desc()).limit(10).all()
    return dict(ranking_users=top_users)

@main.route('/quiz/submit/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    pontos_ganhos = 0
    total_perguntas = len(quiz.questions)
    respostas_corretas = 0

    for pergunta in quiz.questions:
        id_resposta_selecionada = request.form.get(f'pergunta_{pergunta.id}')
        if id_resposta_selecionada:
            resposta = Answer.query.get(id_resposta_selecionada)
            if resposta and resposta.is_correct:
                respostas_corretas += 1
                pontos_ganhos += 10

    if pontos_ganhos > 0:
        current_user.score += pontos_ganhos
        db.session.commit()

    flash(f'Você acertou {respostas_corretas} de {total_perguntas} perguntas e ganhou {pontos_ganhos} pontos!', 'success')
    return redirect(url_for('main.pagina_aula', course_id=quiz.lesson.course.id, lesson_id=quiz.lesson.id))