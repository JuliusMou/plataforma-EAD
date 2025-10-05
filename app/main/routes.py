# app/main/routes.py

import markdown
from datetime import datetime
from . import main
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request
from app.models import User, Course, Lesson, Question, Answer, Quiz, Friendship
from app import db
from .forms import EditProfileForm
from sqlalchemy import or_


@main.before_app_request
def before_request():
    """ Executa antes de CADA requisição na aplicação. """
    if current_user.is_authenticated:
        # Atualiza o 'last_seen' do usuário
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

        # LÓGICA CRÍTICA para redirecionar usuários não confirmados
        if not current_user.confirmed \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            flash('Por favor, confirme sua conta para acessar esta página.', 'warning')
            return redirect(url_for('auth.resend_confirmation'))


@main.app_template_filter('markdown_to_html')
def markdown_to_html(text):
    """Converte uma string de texto em Markdown para HTML."""
    return markdown.markdown(text)


@main.app_context_processor
def inject_friends():
    """ Injeta a lista de amigos do usuário atual em todos os templates. """
    if current_user.is_authenticated:
        friends = current_user.get_friends()
        return dict(friends_list=friends)
    return dict(friends_list=[])


@main.route('/usuarios')
@login_required
def pagina_usuarios():
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
    friendship_status = 'not_friends'

    if user != current_user:
        friendship = Friendship.query.filter(
            or_(
                (Friendship.requester_id == current_user.id) & (Friendship.addressee_id == user.id),
                (Friendship.requester_id == user.id) & (Friendship.addressee_id == current_user.id)
            )
        ).first()

        if friendship:
            if friendship.status == 'accepted':
                friendship_status = 'friends'
            elif friendship.status == 'pending':
                if friendship.requester_id == current_user.id:
                    friendship_status = 'request_sent'
                else:
                    friendship_status = 'request_received'

    pending_requests = Friendship.query.filter_by(addressee_id=user.id, status='pending').all()

    return render_template('main/profile.html', user=user, friendship_status=friendship_status,
                           pending_requests=pending_requests)


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


@main.route('/amizade/adicionar/<username>', methods=['POST'])
@login_required
def adicionar_amigo(username):
    user_to_add = User.query.filter_by(username=username).first_or_404()
    if user_to_add == current_user:
        flash('Você não pode adicionar a si mesmo como amigo.', 'warning')
        return redirect(url_for('main.pagina_perfil', username=username))

    existing_friendship = Friendship.query.filter(
        or_(
            (Friendship.requester_id == current_user.id) & (Friendship.addressee_id == user_to_add.id),
            (Friendship.requester_id == user_to_add.id) & (Friendship.addressee_id == current_user.id)
        )
    ).first()

    if existing_friendship:
        flash('Um pedido de amizade já existe com este usuário.', 'info')
        return redirect(url_for('main.pagina_perfil', username=username))

    new_friendship = Friendship(requester_id=current_user.id, addressee_id=user_to_add.id, status='pending')
    db.session.add(new_friendship)
    db.session.commit()
    flash(f'Pedido de amizade enviado para {username}.', 'success')
    return redirect(url_for('main.pagina_perfil', username=username))


@main.route('/amizade/aceitar/<int:request_id>', methods=['POST'])
@login_required
def aceitar_amizade(request_id):
    friend_request = Friendship.query.get_or_404(request_id)
    if friend_request.addressee_id != current_user.id:
        flash('Ação não autorizada.', 'danger')
        return redirect(url_for('main.pagina_principal'))

    friend_request.status = 'accepted'
    db.session.commit()
    flash(f'Você e {friend_request.requester.username} agora são amigos!', 'success')
    return redirect(url_for('main.pagina_perfil', username=current_user.username))


@main.route('/amizade/recusar/<int:request_id>', methods=['POST'])
@login_required
def recusar_amizade(request_id):
    friend_request = Friendship.query.get_or_404(request_id)
    if friend_request.addressee_id != current_user.id:
        flash('Ação não autorizada.', 'danger')
        return redirect(url_for('main.pagina_principal'))

    db.session.delete(friend_request)
    db.session.commit()
    flash('Pedido de amizade recusado.', 'info')
    return redirect(url_for('main.pagina_perfil', username=current_user.username))


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
    curso = Course.query.get_or_404(course_id)

    lessons_list = curso.lessons
    current_lesson_index = None
    for i, lesson in enumerate(lessons_list):
        if lesson.id == lesson_id:
            current_lesson_index = i
            break

    prev_lesson = lessons_list[
        current_lesson_index - 1] if current_lesson_index is not None and current_lesson_index > 0 else None
    next_lesson = lessons_list[
        current_lesson_index + 1] if current_lesson_index is not None and current_lesson_index < len(
        lessons_list) - 1 else None

    is_completed = current_user.has_completed_lesson(aula)

    return render_template('main/lesson_detail.html',
                           aula=aula,
                           curso=curso,
                           prev_lesson=prev_lesson,
                           next_lesson=next_lesson,
                           is_completed=is_completed)


@main.route('/aula/concluir/<int:lesson_id>', methods=['POST'])
@login_required
def concluir_aula(lesson_id):
    aula = Lesson.query.get_or_404(lesson_id)

    if not current_user.has_completed_lesson(aula):
        current_user.completed_lessons.append(aula)
        current_user.score += 10
        db.session.commit()
        flash(f'Parabéns! Você concluiu a aula "{aula.title}" e ganhou 10 pontos!', 'success')
    else:
        flash(f'Você já havia concluído a aula "{aula.title}".', 'info')

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

    flash(f'Você acertou {respostas_corretas} de {total_perguntas} perguntas e ganhou {pontos_ganhos} pontos!',
          'success')
    return redirect(url_for('main.pagina_aula', course_id=quiz.lesson.course.id, lesson_id=quiz.lesson.id))