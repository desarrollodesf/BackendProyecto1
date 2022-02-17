import os.path
from queue import Empty
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from sqlalchemy import null
from config import Config
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from datetime import datetime
from flask_cors import CORS
import pytz
from tzlocal import get_localzone


app = Flask(__name__)
CORS(app)
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
        fields = ("id", "name", "banner", "url", "startDate", "endDate", "payment", "script", "address", "notes", "user_id")

contest_schema = Contest_Schema()
contests_schema = Contest_Schema(many = True)

class ContestResource(Resource):

    def get(self, contest_id):
        contest = Contest.query.get_or_404(contest_id)
        return contest_schema.dump(contest)

    def put(self, contest_id):

        contest = Contest.query.get_or_404(contest_id)

        fecha_inicio = contest.startDate
        fecha_fin = contest.endDate
        user = Contest.query.filter_by(url=request.json['url']).first()
        
        if user is not None:
            return 'La URL del concurso ya está siendo utilizado por otro administrador para su URL personalizada. Por favor use otra personalización de URL', 400

        if 'startDate' in request.json:
            contest.startDate = datetime.strptime(request.json['startDate'],'%Y-%m-%dT%H:%M:%S')

        if 'endDate' in request.json:
            contest.endDate = datetime.strptime(request.json['endDate'],'%Y-%m-%dT%H:%M:%S')

        if fecha_inicio > fecha_fin:
            return 'Fecha de inicio debe ser menor o igual a la fecha de fin', 400
            
        if 'name' in request.json:
            contest.name = request.json['name']

        if 'banner' in request.json:
            contest.banner = request.json['banner']

        if 'url' in request.json:
            contest.url = request.json['url']

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

        test_list = User.query.all()
        if next((x for x in test_list if str(x.id) == contest.user_id), None) is None:
            return 'El ID del usuario utilizado para crear el concurso no existe', 400 

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

            if not request.json['startDate']:
                return 'Fecha de inicio no puede estar vacía', 400

            if not request.json['endDate']:
                return 'Fecha de fin no puede estar vacía', 400

            if not request.json['name']:
                return 'No se puede dejar el nombre del concurso vacío', 400

            new_contest = Contest(
                name = request.json['name'],
                banner = request.json['banner'],
                url = request.json['name'],
                startDate = datetime.strptime(request.json['startDate'],'%Y-%m-%dT%H:%M:%S'),
                endDate = datetime.strptime(request.json['endDate'],'%Y-%m-%dT%H:%M:%S'),
                payment = request.json['payment'],
                script = request.json['script'],
                address = request.json['address'],
                notes = request.json['notes'],
                user_id = request.json['user_id']     
            )

            if new_contest.startDate > new_contest.endDate:
                return 'Fecha de inicio debe ser menor o igual a la fecha de fin', 400

            test_list = User.query.all()
            if next((x for x in test_list if str(x.id) == str(new_contest.user_id)), None) is None:
                return 'El ID del usuario utilizado para crear el concurso no existe', 400

            test_list = Contest.query.all()
            if not next((x for x in test_list if str(x.url) == str(new_contest.url)), None) is None:
                return 'El nombre del concurso ya está siendo utilizado por otro administrador para su URL personalizada. Por favor use otro nombre para crear su concurso.', 400

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

        form = Form.query.get_or_404(form_id)

        if 'state' in request.json:
            form.state = request.json['state']

        if 'formatted' in request.json:
            form.formatted = request.json['formatted']

        db.session.commit()
        return form_schema.dump(form)


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
                uploadDate = datetime.strptime(datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/New_York")).strftime('%Y-%m-%dT%H:%M:%S'),'%Y-%m-%dT%H:%M:%S'),
                state = "En proceso",
                original = request.json['original'],
                formatted = "",
                notes = request.json['notes'],
                contest_id = request.json['contest_id']     
            )
                    
            test_list = Contest.query.all()
            if next((x for x in test_list if str(x.id) == str(new_form.contest_id)), None) is None:
                return 'El ID del concurso utilizado para enviar un formulario no existe', 400

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
    
    def get(self, URL):
        contest = Contest.query.filter_by(url = URL).first()
        if contest is None:
            return 'URL no encontrado', 400
        forms = Form.query.filter_by(contest_id=contest.id)
        return forms_schema.dump(forms)

class PendingToConvertResource(Resource):
    def get(self):
        forms = Form.query.filter_by(state = "En proceso")
        return forms_schema.dump(forms)


api.add_resource(UserResource,'/api/administrador/')   
api.add_resource(FormsResource,'/api/forms/')
api.add_resource(FormResource,'/api/form/<int:form_id>')
api.add_resource(ContestsResource,'/api/contests/')
api.add_resource(ContestResource,'/api/contest/<int:contest_id>')
api.add_resource(ContestsByUserResource,'/api/administrador/<int:user_id>/contests')
api.add_resource(FormsByContestResource,'/api/contests/<string:URL>/forms')
api.add_resource(PendingToConvertResource,'/api/forms/pendingToConvert')