# app/main/routes.py

import markdown
from datetime import datetime, timedelta
from . import main
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request, jsonify
from app.models import User, Course, Lesson, Question, Answer, Quiz, Friendship, CourseRating, Enrollment, PrivateMessage
from app import db
from .forms import EditProfileForm
from sqlalchemy import or_, func


@main.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        if not current_user.confirmed \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            flash('Por favor, confirme sua conta para acessar esta página.', 'warning')
            return redirect(url_for('auth.resend_confirmation'))


# --- NOVO CONTEXT PROCESSOR PARA NOTIFICAÇÕES ---
@main.app_context_processor
def inject_unread_counts():
    """Injeta a contagem de mensagens não lidas em todos os templates."""
    if current_user.is_authenticated:
        # Conta mensagens não lidas por remetente
        unread_counts = db.session.query(
            User.username, func.count(PrivateMessage.id)
        ).join(
            PrivateMessage, User.id == PrivateMessage.sender_id
        ).filter(
            PrivateMessage.recipient_id == current_user.id,
            PrivateMessage.read == False
        ).group_by(User.username).all()
        
        # Converte a lista de tuplas em um dicionário para fácil acesso no JS/Jinja
        unread_dict = {username: count for username, count in unread_counts}
        return dict(unread_counts=unread_dict)
    return dict(unread_counts={})


@main.route('/')
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    total_users = User.query.count()
    online_users = User.query.filter(User.last_seen > datetime.utcnow() - timedelta(minutes=5)).count()

    return render_template('main/landing_page.html', total_users=total_users, online_users=online_users)


@main.route('/dashboard')
@login_required
def dashboard():
    total_users = User.query.count()
    online_users = User.query.filter(User.last_seen > datetime.utcnow() - timedelta(minutes=5)).count()

    return render_template('main/dashboard.html', total_users=total_users, online_users=online_users)


@main.app_template_filter('markdown_to_html')
def markdown_to_html(text):
    return markdown.markdown(text)


@main.app_context_processor
def inject_friends():
    if current_user.is_authenticated:
        friends = current_user.get_friends()
        return dict(friends_list=friends)
    return dict(friends_list=[])


@main.route('/usuarios')
@login_required
def pagina_usuarios():
    all_users = User.query.filter(User.id != current_user.id).order_by(User.username.asc()).all()
    return render_template('main/users.html', users=all_users)


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

    message = request.form.get('message', '').strip()
    new_friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=user_to_add.id,
        status='pending',
        message=message if message else None
    )
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
        return redirect(url_for('main.dashboard'))

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
        return redirect(url_for('main.dashboard'))

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
    course = aula.course

    if not current_user.has_completed_lesson(aula):
        current_user.completed_lessons.append(aula)
        enrollment = current_user.get_enrollment_for(course)
        if enrollment:
            enrollment.score += 10
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
    course = quiz.lesson.course

    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if not enrollment:
        flash('Você precisa estar inscrito no curso para responder ao simulado.', 'warning')
        return redirect(url_for('main.pagina_aula', course_id=course.id, lesson_id=quiz.lesson.id))

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
        enrollment.score += pontos_ganhos
        current_user.score += pontos_ganhos
        db.session.commit()

    flash(
        f'Você acertou {respostas_corretas} de {total_perguntas} perguntas e ganhou {pontos_ganhos} pontos neste curso!',
        'success')
        
    return redirect(url_for('main.pagina_aula', course_id=quiz.lesson.course.id, lesson_id=quiz.lesson.id))


@main.route('/curso/<int:course_id>/inscrever', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    current_user.enroll(course)
    db.session.commit()
    flash(f'Você se inscreveu no curso "{course.title}" com sucesso!', 'success')
    return redirect(url_for('main.pagina_cursos'))


@main.route('/curso/<int:course_id>/cancelar', methods=['POST'])
@login_required
def unenroll(course_id):
    course = Course.query.get_or_404(course_id)
    current_user.unenroll(course)
    db.session.commit()
    flash(f'Sua inscrição no curso "{course.title}" foi cancelada.', 'info')
    return redirect(url_for('main.pagina_cursos'))


@main.route('/curso/<int:course_id>/avaliar', methods=['POST'])
@login_required
def rate_course(course_id):
    course = Course.query.get_or_404(course_id)
    stars = request.form.get('stars', 0, type=int)

    if stars < 1 or stars > 5:
        flash('Avaliação inválida.', 'danger')
        return redirect(url_for('main.pagina_cursos'))

    rating = CourseRating.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if rating:
        rating.stars = stars
        flash('Sua avaliação foi atualizada!', 'success')
    else:
        rating = CourseRating(user_id=current_user.id, course_id=course.id, stars=stars)
        db.session.add(rating)
        flash('Obrigado por avaliar o curso!', 'success')

    db.session.commit()
    return redirect(url_for('main.pagina_cursos'))
