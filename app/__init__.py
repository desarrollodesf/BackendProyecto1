import os.path
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from config import Config
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)
api = Api(app)
ma = Marshmallow(app)
bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'

from app.models import Contest, Form, User

def setup_database(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

if not os.path.isfile(app.config['SQLALCHEMY_DATABASE_URI']):
    setup_database(app)


class Contest_Schema(ma.Schema):
    class Meta:
        fields = ("id", "name", "banner", "url", "startDate", "endDate", "payment", "script", "address", "notes" "user_id")

contest_schema = Contest_Schema()
contests_schema = Contest_Schema(many = True)

class ContestResource(Resource):

    def get(self, contest_id):
        contest = Contest.query.get_or_404(contest_id)
        return contest_schema.dump(contest)

    def put(self, contest_id):

        contest = Contest.query.get_or_404(contest_id)

        if 'name' in request.json:
            contest.name = request.json['name']

        if 'banner' in request.json:
            contest.banner = request.json['banner']

        if 'url' in request.json:
            contest.url = request.json['url']

        #if 'startDate' in request.json:
        #    contest.fechaInicio = request.json['startDate']

        #if 'endDate' in request.json:
        #    contest.fechaFin = request.json['endDate']

        if 'payment' in request.json:
            contest.payment = request.json['payment']

        if 'script' in request.json:
            contest.script = request.json['script']
        
        if 'address' in request.json:
            contest.address = request.json['address']

        if 'notes' in request.json:
            contest.notes = request.json['notes']

        if 'user_id' in request.json:
            contest.user_id = request.json['user_id']
        
        db.session.commit()
        return contest_schema.dump(contest)


    def delete(self, contest_id):

        contest = Contest.query.get_or_404(contest_id)
        db.session.delete(contest)
        db.session.commit()
        return 'Contest deleted', 204

class ContestsResource(Resource):

    def get(self):
        contests = Contest.query.all()
        return contests_schema.dump(contests)

    def post(self):
            new_contest = Contest(
                name = request.json['name'],
                banner = request.json['banner'],
                url = request.json['url'],
                #startDate = request.form['startDate'],
                #endDate = request.form['endDate'],
                payment = request.json['payment'],
                script = request.json['script'],
                address = request.json['address'],
                notes = request.json['notes'],
                user_id = request.json['user_id']     
            )

            db.session.add(new_contest)
            db.session.commit()
            return contest_schema.dump(new_contest)

class Form_Schema(ma.Schema):
    class Meta:
        fields = ("id","email", "name", "lastname", "uploadDate", "state", "original", "formatted", "notes", "contest_id")

form_schema = Form_Schema()
forms_schema = Form_Schema(many = True)

class FormResource(Resource):

    def get(self, form_id):
        form = Form.query.get_or_404(form_id)
        return form_schema.dump(form)

    def put(self, form_id):

        contest = Form.query.get_or_404(form_id)

        if 'email' in request.json:
            contest.email = request.json['email']

        if 'name' in request.json:
            contest.name = request.json['name']

        if 'lastname' in request.json:
            contest.lastname = request.json['lastname']

        #if 'uploadDate' in request.json:
        #    contest.fechaInicio = request.json['uploadDate']

        if 'state' in request.json:
            contest.state = request.json['state']

        if 'original' in request.json:
            contest.original = request.json['original']
        
        if 'formatted' in request.json:
            contest.formatted = request.json['formatted']

        if 'notes' in request.json:
            contest.notes = request.json['notes']

        if 'contest_id' in request.json:
            contest.contest_id = request.json['contest_id']
        
        db.session.commit()
        return form_schema.dump(contest)


    def delete(self, form_id):

        contest = Form.query.get_or_404(form_id)
        db.session.delete(contest)
        db.session.commit()
        return 'Form deleted', 204

class FormsResource(Resource):

    def get(self):
        forms = Form.query.all()
        return forms_schema.dump(forms)

    def post(self):
            new_form = Form(
                email = request.json['email'],
                name = request.json['name'],
                lastname = request.json['lastname'],
                #uploadDate = request.form['uploadDate'],
                state = request.json['state'],
                original = request.json['original'],
                formatted = request.json['formatted'],
                notes = request.json['notes'],
                contest_id = request.json['contest_id']     
            )

            db.session.add(new_form)
            db.session.commit()
            return form_schema.dump(new_form)

class UserResource(Resource):
    def post(self):
        name = request.json['name']
        lastname = request.json['lastname']
        email = request.json['email']
        password = request.json['password']

        user = User.query.filter_by(email=email).first()
        if user is not None:
            return 'Usuario ya existe', 400

        user_data = User(name=name, lastname=lastname,email=email )
        user_data.set_password(password)
        db.session.add(user_data)
        db.session.commit()
        return 'Usuario creado', 204

class ContestsByUserResource(Resource):
    
    def get(self, user_id):
        contests = Contest.query.filter_by(user_id=user_id)
        return contests_schema.dump(contests)

class FormsByContestResource(Resource):
    
    def get(self, contest_id):
        forms = Form.query.filter_by(contest_id=contest_id)
        return forms_schema.dump(forms)

api.add_resource(UserResource,'/api/administrador/')   
api.add_resource(FormsResource,'/api/forms/')
api.add_resource(FormResource,'/api/form/<int:form_id>')
api.add_resource(ContestsResource,'/api/contests/')
api.add_resource(ContestResource,'/api/contest/<int:contest_id>')
api.add_resource(ContestsByUserResource,'/api/administrador/<int:user_id>/contests')
api.add_resource(FormsByContestResource,'/api/contests/<int:contest_id>/forms')