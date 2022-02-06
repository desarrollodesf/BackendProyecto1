from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, DateTimeField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms.fields import DateTimeLocalField
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
    
    def __repr__(self):
        return '<Post {}>'.format(self.body)

class CreateEventForm(FlaskForm):
    name = StringField('EventName', validators=[DataRequired()])
    category = RadioField('Category',  choices = ['Conferencia', 'Seminario', 'Congreso', 'Curso'], validators=[DataRequired()])
    place = StringField('Place', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    timestamp = DateTimeLocalField('Start Date/Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    timestamp_end = DateTimeLocalField('End Date/Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    method = RadioField('Type',  choices = ['Presencial', 'Virtual'], validators=[DataRequired()])
    submit = SubmitField('Create')

    

