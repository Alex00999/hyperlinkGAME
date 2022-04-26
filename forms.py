from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired(), Length(min=4, max=64), Email()])
    psw = PasswordField("Пароль", validators=[DataRequired(), Length(min=4, max=64)])
    remember = BooleanField("Запомнить", default=False)
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    name = StringField("Имя", validators=[Length(min=4, max=64)])
    email = StringField("Почта", validators=[Email()])
    psw = PasswordField("Пароль", validators=[DataRequired(), Length(min=4, max=64)])
    psw2 = PasswordField("Повторите пароль", validators=[DataRequired(), EqualTo('psw')])
    submit = SubmitField("Зарегистрироваться")
