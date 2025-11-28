# app/main/routes.py

import markdown
from datetime import datetime, timedelta
from . import main
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request, jsonify
# lesson_completions foi importado para a nova query
from app.models import User, Course, Lesson, Question, Answer, Quiz, Friendship, CourseRating, Enrollment, \
    PrivateMessage, ContentSuggestion, ForumCategory, ForumTopic, ForumPost, CourseLike, lesson_completions
from app import db
from .forms import EditProfileForm, ContentSuggestionForm, TopicForm, PostForm
from app.utils import log_user_activity
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


@main.app_context_processor
def inject_unread_counts():
    """Injeta a contagem de mensagens não lidas em todos os templates."""
    if current_user.is_authenticated:
        unread_counts = db.session.query(
            User.username, func.count(PrivateMessage.id)
        ).join(
            PrivateMessage, User.id == PrivateMessage.sender_id
        ).filter(
            PrivateMessage.recipient_id == current_user.id,
            PrivateMessage.read == False
        ).group_by(User.username).all()

        unread_dict = {username: count for username, count in unread_counts}
        return dict(unread_counts=unread_dict)
    return dict(unread_counts={})


@main.route('/')
def landing_page():
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

    log_user_activity(current_user, 'new_friend', f'Agora é amigo de {friend_request.requester.username}')
    log_user_activity(friend_request.requester, 'new_friend', f'Agora é amigo de {current_user.username}')

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
    search_query = request.args.get('q')
    if search_query:
        cursos = Course.query.filter(
            or_(
                Course.title.ilike(f'%{search_query}%'),
                Course.description.ilike(f'%{search_query}%')
            )
        ).order_by(Course.created_at.desc()).all()
    else:
        cursos = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('main/courses.html', cursos=cursos, search_query=search_query)


# LÓGICA DESTA ROTA FOI ATUALIZADA
@main.route('/cursos/<int:course_id>')
@login_required
def pagina_curso(course_id):
    curso = Course.query.get_or_404(course_id)
    progress = 0

    if current_user.is_authenticated:
        total_lessons = len(curso.lessons)
        if total_lessons > 0:
            # Conta quantas aulas deste curso o usuário completou
            completed_lessons_count = db.session.query(lesson_completions).join(Lesson).filter(
                Lesson.course_id == curso.id,
                lesson_completions.c.user_id == current_user.id
            ).count()
            progress = round((completed_lessons_count / total_lessons) * 100)

    return render_template('main/course_detail.html', curso=curso, progress=progress)


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

        log_user_activity(current_user, 'lesson_completed', f'Concluiu a aula: {aula.title}')

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


@main.route('/curso/<int:course_id>/interagir', methods=['POST'])
@login_required
def interact_course(course_id):
    course = Course.query.get_or_404(course_id)
    action = request.form.get('action')

    if action not in ['like', 'dislike']:
        return jsonify({'error': 'Invalid action'}), 400

    existing_interaction = CourseLike.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    is_like = (action == 'like')

    if existing_interaction:
        if existing_interaction.is_like == is_like:
            # Toggle off if clicking the same action
            db.session.delete(existing_interaction)
            message = 'Interação removida.'
        else:
            # Switch interaction
            existing_interaction.is_like = is_like
            message = f'Você deu {action} neste curso.'
    else:
        interaction = CourseLike(user_id=current_user.id, course_id=course.id, is_like=is_like)
        db.session.add(interaction)
        message = f'Você deu {action} neste curso.'

    db.session.commit()

    # Calculate new counts
    likes = CourseLike.query.filter_by(course_id=course.id, is_like=True).count()
    dislikes = CourseLike.query.filter_by(course_id=course.id, is_like=False).count()

    return jsonify({'success': True, 'message': message, 'likes': likes, 'dislikes': dislikes})


@main.route('/curso/<int:course_id>/compartilhar', methods=['POST'])
@login_required
def share_course(course_id):
    course = Course.query.get_or_404(course_id)
    recipient_username = request.form.get('friend_username')

    if not recipient_username:
        flash('Selecione um amigo para compartilhar.', 'warning')
        return redirect(url_for('main.pagina_cursos'))

    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('main.pagina_cursos'))

    # Check if they are friends
    if recipient not in current_user.get_friends():
        flash('Você só pode compartilhar com amigos.', 'danger')
        return redirect(url_for('main.pagina_cursos'))

    message_content = f"Olá! Recomendo este curso: **{course.title}**. Confira aqui: {url_for('main.pagina_curso', course_id=course.id, _external=True)}"

    msg = PrivateMessage(sender=current_user, recipient=recipient, content=message_content)
    db.session.add(msg)
    db.session.commit()

    flash(f'Curso compartilhado com {recipient.username}!', 'success')
    return redirect(url_for('main.pagina_cursos'))


@main.route('/sugerir-conteudo', methods=['GET', 'POST'])
@login_required
def sugerir_conteudo():
    form = ContentSuggestionForm()
    if form.validate_on_submit():
        sugestao = ContentSuggestion(
            user=current_user,
            title=form.title.data,
            description=form.description.data,
            content_type=form.content_type.data
        )
        db.session.add(sugestao)
        db.session.commit()
        flash('Sua sugestão foi enviada com sucesso! Agradecemos sua contribuição.', 'success')
        return redirect(url_for('main.minhas_sugestoes'))
    return render_template('main/suggest_content.html', form=form)


@main.route('/minhas-sugestoes')
@login_required
def minhas_sugestoes():
    sugestoes = ContentSuggestion.query.filter_by(user_id=current_user.id).order_by(ContentSuggestion.created_at.desc()).all()
    return render_template('main/my_suggestions.html', sugestoes=sugestoes)


# --- ROTA DO CHATBOT ---

@main.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    data = request.get_json()
    message = data.get('message', '').lower()

    if 'senha' in message or 'password' in message:
        response = "Para redefinir sua senha, vá para a página de login e clique em 'Esqueceu a senha?'. Ou acesse suas configurações de perfil."
    elif 'curso' in message or 'aula' in message:
        response = "Você pode acessar seus cursos na aba 'Cursos' do menu principal. Lá você encontra todo o conteúdo disponível."
    elif 'contato' in message or 'suporte' in message:
        response = "Você pode entrar em contato com o suporte através do email suporte@ead.com ou usar nosso fórum para dúvidas técnicas."
    elif 'fórum' in message or 'forum' in message:
        response = "O fórum é um ótimo lugar para tirar dúvidas! Acesse pelo menu 'Comunidade' > 'Fórum'."
    elif 'olá' in message or 'oi' in message:
        response = f"Olá, {current_user.username}! Como posso te ajudar hoje?"
    else:
        response = "Desculpe, não entendi. Tente perguntar sobre cursos, senha, fórum ou contato."

    return jsonify({'response': response})


# --- ROTAS DO FÓRUM ---

@main.route('/forum/busca')
@login_required
def forum_search():
    search_query = request.args.get('q', '')
    if search_query:
        topics = ForumTopic.query.filter(
            or_(
                ForumTopic.title.ilike(f'%{search_query}%'),
                ForumTopic.content.ilike(f'%{search_query}%')
            )
        ).order_by(ForumTopic.created_at.desc()).all()
    else:
        topics = []

    return render_template('forum/search_results.html', topics=topics, search_query=search_query)


@main.route('/forum')
@login_required
def forum_index():
    categories = ForumCategory.query.order_by(ForumCategory.name.asc()).all()
    return render_template('forum/index.html', categories=categories)


@main.route('/forum/categoria/<int:category_id>')
@login_required
def forum_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    topics = ForumTopic.query.filter_by(category_id=category.id).order_by(ForumTopic.created_at.desc()).all()
    return render_template('forum/category.html', category=category, topics=topics)


@main.route('/forum/topico/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def forum_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)

    # Incrementa visualizações
    topic.views += 1
    db.session.commit()

    form = PostForm()
    if form.validate_on_submit():
        post = ForumPost(
            content=form.content.data,
            user=current_user,
            topic=topic
        )
        db.session.add(post)

        log_user_activity(current_user, 'forum_post', f'Respondeu ao tópico: {topic.title}')

        db.session.commit()
        flash('Sua resposta foi publicada.', 'success')
        return redirect(url_for('main.forum_topic', topic_id=topic.id))

    return render_template('forum/topic.html', topic=topic, form=form)


@main.route('/forum/novo-topico', methods=['GET', 'POST'])
@login_required
def create_topic():
    form = TopicForm()
    # Popula as categorias no SelectField
    form.category.choices = [(c.id, c.name) for c in ForumCategory.query.order_by('name').all()]

    if form.validate_on_submit():
        topic = ForumTopic(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category.data,
            user=current_user
        )
        db.session.add(topic)

        log_user_activity(current_user, 'forum_topic', f'Criou o tópico: {topic.title}')

        db.session.commit()
        flash('Tópico criado com sucesso!', 'success')
        return redirect(url_for('main.forum_topic', topic_id=topic.id))

    return render_template('forum/create_topic.html', form=form)