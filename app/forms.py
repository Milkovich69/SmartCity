from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, PasswordField, BooleanField, SubmitField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Вход')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    last_name = StringField('Фамилия')
    first_name = StringField('Имя')
    date = DateField('Дата рождения', format='%d.%m.%Y')
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Регистрация')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пожалуйста, выберите другой логин.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Такой e-mail уже зарегистрирован, используйте другой.')


class CompanyRegistrationForm(FlaskForm):
    name = StringField('Название')
    address = StringField('Адрес')
    submit = SubmitField('Регистрация')


class EventRegistrationForm(FlaskForm):
    name = StringField('Название')
    place = StringField('Место проведения')
    date_event = DateField('Дата проведения', format='%d.%m.%Y')
    b_count = IntegerField('Количество баллов за участие')
    submit = SubmitField('Добавить')


class EditProfileForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    last_name = StringField('Фамилия')
    first_name = StringField('Имя')
    date = DateField('Дата рождения', format='%d.%m.%Y')
    submit = SubmitField('Сохранить')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Этот логин уже занят.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Отправить письмо на почту')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Восстановить пароль')