# -*- coding: utf-8 -*-
from app import app, db
from flask import render_template, flash, redirect, url_for, request, jsonify
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, \
    CompanyRegistrationForm, EventRegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Event, Company, Points
from werkzeug.urls import url_parse
from app.email import send_password_reset_email


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    events = Event.query.all()
    return render_template('index.html', title="Домашняя страница", f_events=events)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, last_name=form.last_name.data,
                    first_name=form.first_name.data, date=form.date.data, sum_b=0)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        company = Company(id=user.id, agent_id=user.id)
        db.session.add(company)
        db.session.commit()
        flash('Поздравляем, теперь вы зарегистрированы!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/company_register', methods=['GET', 'POST'])
def company_register():
    form = CompanyRegistrationForm()
    if form.validate_on_submit():
        company = Company.query.filter_by(agent_id=current_user.id).first()
        company.name = form.name.data
        company.address = form.address.data
        db.session.add(company)
        db.session.commit()
        flash('Предприятие зарегистрировано, теперь вы можете добавлять мероприятия!')
        return redirect(url_for('user', username=current_user.username))
    return render_template('company_register.html', title='Регистрация предприятия', form=form)


@app.route('/event_register', methods=['GET', 'POST'])
def event_register():
    form = EventRegistrationForm()
    if form.validate_on_submit():
        company = Company.query.filter_by(agent_id=current_user.id).first()
        event = Event(name=form.name.data, place=form.place.data, date_event=form.date_event.data,
                      description=form.description.data, b_count=form.b_count.data, company_id=company.id)
        db.session.add(event)
        db.session.commit()
        flash('Мероприятие добавлено!')
        return redirect(url_for('company', id=company.id))
    return render_template('event_register.html', title='Добавление мероприятия', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    events = current_user.followed_events
    company = Company.query.filter_by(agent_id=current_user.id).first()
    return render_template('user.html', title='Мой профиль', user=user, events=events, company=company)


@app.route('/company/<id>')
@login_required
def company(id):
    company = Company.query.filter_by(id=id).first_or_404()
    events = Event.query.filter_by(company_id=company.id).all()
    return render_template('company.html', title='Профиль предприятия', company=company, events=events)


@app.route('/event/<id>')
@login_required
def event(id):
    event = Event.query.filter_by(id=id).first_or_404()
    users = []
    other_events = []
    for u in event.followers:
        users.append(u)
    for e in event.sponsor.events:
        if e.id != event.id:
            other_events.append(e)
    print(users)
    points_available = event.points.count() == 0
    return render_template('event.html', title='Мероприятие', event=event, users=users, other_events=other_events,
                           len=len(other_events), points_available=points_available)


@app.route('/subs/<event>')
@login_required
def subs(event):
    current_user.follow(event)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/unsubs/<event>')
@login_required
def unsubs(event):
    current_user.unfollow(event)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.last_name = form.last_name.data
        current_user.first_name = form.first_name.data
        current_user.date = form.date.data
        db.session.commit()
        flash('Изменения сохранены.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.last_name.data = current_user.last_name
        form.first_name.data = current_user.first_name
        form.date.data = current_user.date
    return render_template('edit_profile.html', title='Редактирование профиля',
                           form=form)

@app.route('/event/<id>/score_points',  methods=['GET', 'POST'])
@login_required
def score_points(id):
    event = Event.query.filter_by(id=id).first_or_404()
    users = []
    other_events = []
    for u in event.followers:
        users.append(u)

    for e in event.sponsor.events:
        if e.id != event.id:
            other_events.append(e)
    return render_template('score_points.html', title='Начисление баллов участникам', event=event, users=users,
                           other_events=other_events, len=len(other_events))
# 1. Извлечь из базы данных всех участников, и разместить их в виде чекбоксов
# с подписями и id чекбокосов равными id пользователя и каким-то классом
# 2. Создать функцию на js которая находит все чекбоксы, относящиеся к нашему классу getElementsByClass
# создает объект result = {}
# наполняет его значениями из чекбоксов result[id] = значение из чекбокса
# отправляет полученный объект на сервер post('/points', result)
# после получения ответа от сервера делает чекбоксы недоступным и отображает текст о том, что баллы начислены
# 3. На сервере в routes добавляем /points в котором нужно извлечь объект (список id пользователей
# со значениями True или  False) из запроса, Для тех пользователей у которых True - начислить баллы в базе данных и
# отправить 'Ок' в ответ.

@app.route('/event/<id>/points', methods=['POST'])
@login_required
def points(id):
    event = Event.query.filter_by(id=id).first_or_404()
    users = []
    for u in event.followers:
        users.append(u)
    result = dict(request.form)
    keys = []
    for key, value in result.items():
        if value == 'True':
            keys.append(int(key))
    for u in users:
        if u.id in keys:
            point = Points(user_id=u.id, event_id=id, points=event.b_count)
            db.session.add(point)
            u.sum_b += event.b_count
    db.session.commit()
    return jsonify()


@app.route('/event/<id>/points_awarded',  methods=['GET', 'POST'])
@login_required
def points_awarded(id):
    event = Event.query.filter_by(id=id).first_or_404()
    users = []
    for p in Points.query.filter_by(event_id=id).all():
        users.append(User.query.filter_by(id=p.user_id).first())
    print(users)
    return render_template('points_awarded.html', title='Начисленные баллы', event=event, users=users)


@app.route('/oops/')
def oops():
    return render_template('404.html')

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Проверьте ваш электронный ящик')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Ваш пароль был изменен')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)