from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Regexp

from app.models import User


class LoginForm(FlaskForm):
    username = StringField('手机号', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    username = StringField('手机号', validators=[DataRequired(), Regexp(r'1[34578]\d{9}', message='请输入正确的手机号')])
    # email = StringField('邮箱地址', validators=[DataRequired(), Email()])

    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField('重复密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    @staticmethod
    def validate_username(username):
        user = User.query.filter_by(name=username.data).first()
        if user is not None:
            raise ValidationError('手机号已注册')

    # def validate_email(self, email):
    #     user = User.query.filter_by(email=email.data).first()
    #     if user is not None:
    #         raise ValidationError('请输入一个不同的邮箱')


# class ResetPasswordRequestForm(FlaskForm):
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     submit = SubmitField('Request Password Reset')
#
#
# class ResetPasswordForm(FlaskForm):
#     password = PasswordField('password', validators=[DataRequired()])
#     password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
#     submit = SubmitField('Request Password Reset')


class SearchForm(FlaskForm):
    search = StringField('搜索', validators=[DataRequired()])
    submit = SubmitField('搜索')


class JumpForm(FlaskForm):
    page = IntegerField('页码', validators=[DataRequired()])
    submit = SubmitField('跳转')
