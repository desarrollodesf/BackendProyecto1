import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    