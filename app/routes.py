# -*- coding: utf-8 -*-
from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, \
    CompanyRegistrationForm, EventRegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Event, Company
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
                    first_name=form.first_name.data, date=form.date.data)
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
        print(company)
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
                      b_count=form.b_count.data, company_id=company.id)
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