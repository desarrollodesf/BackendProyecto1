import os.path

from sqlalchemy.ext.declarative import DeclarativeMeta
from flask import Flask, request, abort, jsonify, send_from_directory, flash,send_file,after_this_request
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
import uuid
import boto3
import io
import mimetypes
import json
import redis
import urllib.request
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
migrate.init_app(app, db)
login = LoginManager(app)
api = Api(app)
ma = Marshmallow(app)
bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'


global PATH_GUARDAR_GLOBAL
#PATH_GUARDAR_GLOBAL = '/var/locally-mounted/'
#PATH_GUARDAR_GLOBAL = '/home/ubuntu/BackendProyecto1/'
PATH_GUARDAR_GLOBAL = '/app/'
#PATH_GUARDAR_GLOBAL = 'D:/Nirobe/202120-Grupo07/BackendProyecto1/'

global local_environment #bd de datos
local_environment = False

global File_System #Si es Local = 'local' desarrolador, si es local linux = 'linux' si es S3 = 's3', si es  nfs = 'nfs' 
File_System = 's3'

global UPLOAD_FOLDER 
UPLOAD_FOLDER = "uploads"

global PHOTO_FOLDER 
PHOTO_FOLDER = "photos"

global CONVERTED_FOLDER 
CONVERTED_FOLDER = "converted"

global S3_BUCKET 
S3_BUCKET = "grupo13s3"


from app.models import Contest, Form, User


def setup_database(app):
    db.drop_all()
    db.init_app(app)
    with app.app_context():
        db.create_all()


path="uploads"
isExist = os.path.exists(path)
if not isExist:
    os.makedirs(path)

path="converted"
isExist = os.path.exists(path)
if not isExist:
    os.makedirs(path)

path="photos"
isExist = os.path.exists(path)
if not isExist:
    os.makedirs(path)

if local_environment is True:
    if not os.path.isfile(app.config['SQLALCHEMY_DATABASE_URI']):
        setup_database(app)
else:
    r = redis.StrictRedis(host='redis://redistogo:3db655910a128facdf555b3ab7a052cf@barb.redistogo.com:10299/', port=6379, db=0, socket_timeout=1)
    session = boto3.Session(     
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ['AWS_SESSION_TOKEN'],
    region_name = 'us-east-1')

    dynamo_client = session.resource('dynamodb')

class Contest_Schema(ma.Schema):
    class Meta:
        fields = ("id", "name", "banner", "url", "startDate", "endDate", "payment", "script", "address", "notes", "user_id")

contest_schema = Contest_Schema()
contests_schema = Contest_Schema(many = True)

class ContestResource(Resource):

    def get(self, contest_id):
        contest = ""
        try:
            plain = r.get(contest_id)  
            print(plain)
            s = json.loads(plain)
            print(s)
            contest = Contest(
                name = s['name'],
                banner = s['banner'],
                url = s['url'],
                startDate = datetime.strptime(s['startDate'],'%Y-%m-%d %H:%M:%S').isoformat(),
                endDate = datetime.strptime(s['endDate'],'%Y-%m-%d %H:%M:%S').isoformat(),
                payment = s['payment'],
                script = s['script'],
                address = s['address'],
                notes = s['notes'],
                user_id = s['user_id']
            )
        except Exception as e:
            return str(e), 400
        return contest_schema.dump(contest)


    def put(self, contest_id):

        data = request.form
        contest = Contest.query.get_or_404(contest_id)
        
        fecha_inicio = contest.startDate
        fecha_fin = contest.endDate

        if 'startDate' in data:
            if local_environment is True:
                contest.startDate = datetime.strptime(data['startDate'],'%Y-%m-%dT%H:%M:%S')
            else:
                contest.startDate = datetime.strptime(data['startDate'],'%Y-%m-%dT%H:%M:%S').isoformat()

        if 'endDate' in data:
            if local_environment is True:
                contest.endDate = datetime.strptime(data['endDate'],'%Y-%m-%dT%H:%M:%S')
            else:
                contest.endDate = datetime.strptime(data['endDate'],'%Y-%m-%dT%H:%M:%S').isoformat()

        if fecha_inicio > fecha_fin:
            return 'Fecha de inicio debe ser menor o igual a la fecha de fin', 400
            
        if 'name' in data:
            contest.name = data['name']

        if 'url' in data:
            if contest.url != data['url']:
                user = Contest.query.filter_by(url=data['url']).first()
                if user is not None:
                    return 'La URL del concurso ya está siendo utilizado por otro administrador para su URL personalizada. Por favor use otra personalización de URL', 400
                contest.url = data['url']

        if 'payment' in data:
            contest.payment = data['payment']

        if 'script' in data:
            contest.script = data['script']
        
        if 'address' in data:
            contest.address = data['address']

        if 'notes' in data:
            contest.notes = data['notes']

        if 'user_id' in data:
            contest.user_id = data['user_id']

        #test_list = User.query.all()
        #if next((x for x in test_list if str(x.id) == str(contest.user_id)), None) is None:
        #    return 'El ID del usuario utilizado para crear el concurso no existe', 400 

        if 'file' in request.files:
            f = request.files['file']
            
            if f.filename != "":
   
                PATH_GUARDAR = PATH_GUARDAR_GLOBAL  +  f.filename
                if File_System == 's3':
                    PATH_GUARDAR = PATH_GUARDAR_GLOBAL  +  f"photos/{f.filename}"
                contest.nombreBanner = f.filename
                contest.banner = PATH_GUARDAR
                f.save(PATH_GUARDAR)

                
                if File_System == 's3':
                    contest.nombreBanner = f"photos/{f.filename}"
                    response = upload_file(f"photos/{f.filename}", S3_BUCKET)
                    os.remove(os.path.join(PHOTO_FOLDER, f.filename))


        db.session.commit()
        return contest_schema.dump(contest)


    def delete(self, contest_id):
        
        try:
            contest = Contest.query.get_or_404(contest_id)

            forms = Form.query.filter_by(contest_id=contest_id)

            for form in forms:    
                formToDelete = Form.query.get_or_404(form.id)
                
                db.session.delete(formToDelete)
                db.session.commit()
                    
            db.session.delete(contest)
            db.session.commit()
        except Exception as e:
            return str(e), 400
        return 'Contest deleted', 204

class ContestsResource(Resource):

    def get(self):
        contests = Contest.query.all()
        return contests_schema.dump(contests)
    def post(self):
            try:
                data = request.form
                if not data['startDate']:
                    return 'Fecha de inicio no puede estar vacía', 400

                if not data['endDate']:
                    return 'Fecha de fin no puede estar vacía', 400

                if not data['name']:
                    return 'No se puede dejar el nombre del concurso vacío', 400

                if File_System == 's3':
                    PATH_GUARDAR = PATH_GUARDAR_GLOBAL + "photos/" +  data['nombreBanner']
                else:
                    PATH_GUARDAR = PATH_GUARDAR_GLOBAL  +  data['nombreBanner']

                new_contest = Contest(
                    name = data['name'],
                    banner = PATH_GUARDAR,
                    url = data['name'],
                    startDate = datetime.strptime(data['startDate'],'%Y-%m-%dT%H:%M:%S').isoformat(),
                    endDate = datetime.strptime(data['endDate'],'%Y-%m-%dT%H:%M:%S').isoformat(),
                    payment = data['payment'],
                    script = data['script'],
                    address = data['address'],
                    notes = data['notes'],
                    user_id = data['user_id']

                )

                if local_environment is True:
                    new_contest.startDate = datetime.strptime(data['startDate'],'%Y-%m-%dT%H:%M:%S')
                    new_contest.endDate = datetime.strptime(data['endDate'],'%Y-%m-%dT%H:%M:%S')


                if new_contest.startDate > new_contest.endDate:
                    return 'Fecha de inicio debe ser menor o igual a la fecha de fin', 400

                #test_list = User.query.all()
                #if next((x for x in test_list if str(x.id) == str(new_contest.user_id)), None) is None:
                 #   return 'El ID del usuario utilizado para crear el concurso no existe', 400

                test_list = Contest.query.all()
                if not next((x for x in test_list if str(x.url) == str(new_contest.url)), None) is None:
                    return 'El nombre del concurso ya está siendo utilizado por otro administrador para su URL personalizada. Por favor use otro nombre para crear su concurso.', 400

                db.session.add(new_contest)
                
                f = request.files['file']
                f.save(PATH_GUARDAR)
                new_contest.nombreBanner = f.filename

                if File_System == 's3':
                    new_contest.nombreBanner = f"photos/{f.filename}"
                    response = upload_file(f"photos/{f.filename}", S3_BUCKET)
                    os.remove(PATH_GUARDAR)
                db.session.commit()
                dictionary = new_contest.as_dict()
                s = json.dumps(dictionary, default=str)
                r.set(new_contest.id,s)
            except Exception as e:
                return str(e), 400

            return contest_schema.dump(new_contest)

class Form_Schema(ma.Schema):
    class Meta:
        fields = ("id","email", "name", "lastname", "uploadDate", "state", "original", "formatted", "notes", "contest_id", "startConversion", "finishConversion")

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

        if 'startConversion' in request.json:

            if local_environment is True:
                form.startConversion = datetime.strptime(request.json['startConversion'],'%Y-%m-%d %H:%M:%S')
            else:
                form.startConversion = datetime.strptime(request.json['startConversion'],'%Y-%m-%d %H:%M:%S').isoformat()

        if 'finishConversion' in request.json:
            if local_environment is True:
                form.finishConversion = datetime.strptime(request.json['finishConversion'],'%Y-%m-%d %H:%M:%S')
            else:
                form.finishConversion = datetime.strptime(request.json['finishConversion'],'%Y-%m-%d %H:%M:%S').isoformat()     

        db.session.commit()
        return form_schema.dump(form)


    def delete(self, form_id):

        form = Form.query.get_or_404(form_id)
        db.session.delete(form)
        db.session.commit()
        return 'Form deleted', 204

class FormsResource(Resource):

    def get(self):
        forms = Form.query.all()
        return forms_schema.dump(forms)

    def post(self):
        
        numberFile=Form.query.count()
        if numberFile == 0:
            numberFile = 1
        else: 
            numberFile = numberFile+1
        f = request.files['file']

        if File_System == 's3':
            PATH_GUARDAR = PATH_GUARDAR_GLOBAL + "uploads/" +  str(numberFile) +  f.filename
        else:
            PATH_GUARDAR = PATH_GUARDAR_GLOBAL +  str(numberFile)   +  f.filename

        forms = Form.query.filter_by(original=PATH_GUARDAR).first()
        if forms is not None:
            return "El archivo ya existe", 400

        data = request.form
        new_form = Form(
            email = data['email'],
            name = data['name'],
            lastname = data['lastname'],    
            uploadDate = datetime.strptime(datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/New_York")).strftime('%Y-%m-%dT%H:%M:%S'),'%Y-%m-%dT%H:%M:%S').isoformat(),
            state = "En proceso",
            original = PATH_GUARDAR,
            formatted = "",
            notes = data['notes'],
            contest_id = data['contest_id'],     
            guid = uuid.uuid4().hex,
        )

        if local_environment is True:
            new_form.uploadDate = datetime.strptime(datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/New_York")).strftime('%Y-%m-%dT%H:%M:%S'),'%Y-%m-%dT%H:%M:%S')


        test_list = Contest.query.all()
        if next((x for x in test_list if str(x.id) == str(new_form.contest_id)), None) is None:
            return 'El ID del concurso utilizado para enviar un formulario no existe', 400

        f.save(PATH_GUARDAR)

        if File_System == 's3':
            nombreArchivo = f"uploads/{str(numberFile)+f.filename}"
            response = upload_file(nombreArchivo, S3_BUCKET)
            os.remove(PATH_GUARDAR)
            

        db.session.add(new_form)
        db.session.commit()

        if File_System == 's3':
            sendMessageQueue(nombreArchivo, new_form.id, new_form.email, new_form.name)
        return form_schema.dump(new_form)

    def delete(self):
        Form.query.delete()
        db.session.commit()
        return 'Forms deleted', 204

class UserResource(Resource):
    def post(self):
        name = request.json['name']
        lastname = request.json['lastname']
        email = request.json['email']
        password = request.json['password']

        #user = User.query.filter_by(email=email).first()
        #if user is not None:
        #    return 'Usuario ya existe', 400

        #user_data = User(name=name, lastname=lastname,email=email )
        #user_data.set_password(password)
        #db.session.add(user_data)
        #db.session.commit()


        dynamoUser = dynamo_client.Table('usuarios')
        try:
            response = dynamoUser.get_item(
                Key={'correo': request.json["email"]})
        except Exception as e:
            return str(e), 400

        else:   
            if len(response) == 1:
                scan = dynamoUser.scan()
                contador = 0
                if len(scan['Items']) == 0:
                    contador = contador + 1
                else:
                    contador = len(scan['Items']) + 1

                response = dynamoUser.put_item(
                    # Data to be inserted
                    Item={
                        'correo': email,
                        'name': name,
                        'lastname': lastname,
                        'password': password,
                        'id' : contador
                    }
                )
                return 'Usuario creado', 204 
            else:
                return 'Usuario ya existe', 400 

class ContestsByUserResource(Resource):
    
    def get(self, user_id):
        contests = Contest.query.filter_by(user_id=user_id)
        return contests_schema.dump(contests)

class ContestByUrlResource(Resource):
    
    def get(self, URL):
        contest = Contest.query.filter_by(url = URL).first()
        if contest is None:
            return 'URL no encontrado', 400
        else:
            return contest_schema.dump(contest)

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
        form = next(iter(forms), None)
        if form is not None:
            form.state = "Asignada"
            db.session.commit()
        return form_schema.dump(form)

class Admin_Schema(ma.Schema):
    class Meta:
        fields = ("id", "name", "lastname")

admin_schema = Admin_Schema()

class LoginResource(Resource):
    def post(self):
        #user = User.query.filter_by(email=request.json["email"]).first()
        #if user is None or not user.check_password(request.json["password"]):
        #    return 'Invalid username or password', 400


        dynamoUser = dynamo_client.Table('usuarios')
        try:
            response = dynamoUser.get_item(
                Key={'correo': request.json["email"]})
        except Exception as e:
            return 'Invalid username or password', 400
        else:
            if len(response) == 1:
                return 'Invalid username or password', 400

            else:
                item = response['Item']
                name = item['name']
                lastname = item['lastname']
                email = item['correo']
                id = int(item['id'])
                user_data = User(name=name, lastname=lastname,email=email, id = id)
                return admin_schema.dump(user_data)


class GetContestImageResource(Resource):
    def get(self, contest_id):     
        contest = Contest.query.filter_by(id=contest_id).first()
        try:
            if File_System == 's3':
                #file_path = download_file(contest.nombreBanner, S3_BUCKET)
                filePath = PATH_GUARDAR_GLOBAL + "/" + contest.nombreBanner
                upload_file_cloudfront(contest.nombreBanner)
                return send_file(filePath, as_attachment=True)
                
            else :
                return send_from_directory(PATH_GUARDAR_GLOBAL, contest.nombreBanner, as_attachment=True)

        except FileNotFoundError:
            return(404)

class GetOriginalAudioResource(Resource):
    def get(self, form_id):
        audio = Form.query.filter_by(id=form_id).first()

        try:
            if File_System == 's3':
                name = "uploads/" + os.path.basename(audio.original)
                upload_file_cloudfront(name)
                #output = download_file(name, S3_BUCKET)
                
                return send_from_directory(PATH_GUARDAR_GLOBAL, name, as_attachment=True)
            else :
                return send_from_directory(PATH_GUARDAR_GLOBAL, os.path.basename(audio.original), as_attachment=True)

        except FileNotFoundError:
            return(400)

class GetConvertedAudioResource(Resource):
    def get(self, form_id):
        audio = Form.query.filter_by(id=form_id).first()

        try:
            if File_System == 's3':
                name = "converted/" + os.path.basename(audio.formatted)
                upload_file_cloudfront(name)
                #output = download_file(name, S3_BUCKET)
                return send_from_directory(PATH_GUARDAR_GLOBAL, name, as_attachment=True)
            else :
                send_from_directory(PATH_GUARDAR_GLOBAL, os.path.basename(audio.formatted), as_attachment=True)

        except FileNotFoundError:
            return(400)


def upload_file_cloudfront(file_name):

    urllib.request.urlretrieve("https://d3ruftgzgpixxi.cloudfront.net/"+file_name, file_name)


def upload_file(file_name, bucket):
    """
    Function to upload a file to an S3 bucket
    """
    object_name = file_name
    s3_client = boto3.client('s3',     
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ['AWS_SESSION_TOKEN'])
    response = s3_client.upload_file(file_name, bucket, object_name)

    return response

def download_file(file_name, bucket):
    """
    Function to download a given file from an S3 bucket
    """
    pathdownload = os.path.join(PATH_GUARDAR_GLOBAL, file_name)

    s3 = boto3.client('s3',     
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ['AWS_SESSION_TOKEN'])
    s3.download_file(bucket, file_name, pathdownload)

    return pathdownload


def sendMessageQueue(nombreArchivo, idForm, email, name ):
    # Create SQS client
    sqs = boto3.client('sqs', region_name = 'us-east-1',     
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    aws_session_token=os.environ['AWS_SESSION_TOKEN'])

    message = {"key": nombreArchivo, "id": idForm, "email": email , "name": name}
    response = sqs.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/146202439559/MyQueue",
        MessageBody=json.dumps(message)
    )
    print(response)

api.add_resource(UserResource,'/api/administrador/')   
api.add_resource(FormsResource,'/api/forms/')
api.add_resource(FormResource,'/api/form/<int:form_id>')
api.add_resource(ContestsResource,'/api/contests/')
api.add_resource(ContestResource,'/api/contest/<int:contest_id>')
api.add_resource(ContestsByUserResource,'/api/administrador/<int:user_id>/contests')
api.add_resource(FormsByContestResource,'/api/contests/<string:URL>/forms')
api.add_resource(ContestByUrlResource,'/api/contests/<string:URL>/contests')
api.add_resource(PendingToConvertResource,'/api/forms/pendingToConvert')
api.add_resource(LoginResource,'/api/login/')
api.add_resource(GetContestImageResource,'/api/contest/<int:contest_id>/image')
api.add_resource(GetOriginalAudioResource,'/api/form/<int:form_id>/original')
api.add_resource(GetConvertedAudioResource,'/api/form/<int:form_id>/convertido')

