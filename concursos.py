from app import app, db, ma, api
from app.models import User, Contest, Form

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Contest': Contest, 'Form': Form, 'ma' : ma, "api" : api}
