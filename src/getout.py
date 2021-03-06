from sqlalchemy import create_engine
from flask import Flask, Response, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, BooleanField, StringField, PasswordField, validators

import sys


testdb = 'sqlite:///../test.db'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = testdb
db = SQLAlchemy(app)

# Model Objects
class User(db.Model):
	#session attributes
	is_authenticated = False
	is_active = True
	is_anonymous = False


	#database attributes
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True)
	email = db.Column(db.String(120), unique=True)
	is_owner = db.Column(db.Boolean)
	zipcode = db.Column(db.String(5))


	#Constructor
	def __init__(self, username, email, password):
		self.username = username
		self.email = email
		self.set_password(password)
		self.pw_hash = None
		self.zipcode = None

	def set_password(self, password):
		self.pw_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.pw_hash, password)

	# session methods
	def get_id(self):
		return self.username

	#toString and the like
	def __repr__(self):
		return 'User %r' % self.username


class Venue(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True)
	physical_addr = db.Column(db.String(255), unique=True)
	webaddr = db.Column(db.String(120), unique=False)
	claimed = db.Column(db.Boolean, unique=False, default=False)
	place_id = db.Column(db.String(120), unique=True)

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return 'Name: %r' % self.name


class Event(db.Model):
	id=db.Column(db.Integer, primary_key=True)
	venue_id = db.Column(db.Integer)
	eventtype = db.Column(db.String(64))
	description = db.Column(db.String(1024))
	sunday = db.Column(db.Boolean, default=False)
	monday = db.Column(db.Boolean, default=False)
	tuesday = db.Column(db.Boolean, default=False)
	wednesday = db.Column(db.Boolean, default=False)
	thursday = db.Column(db.Boolean, default=False)
	friday = db.Column(db.Boolean, default=False)
	saturday = db.Column(db.Boolean, default=False)


db.create_all()

#Forms
class LoginForm(Form):
	username = StringField("Username", [validators.Length(min=3, max=64)])
	email = StringField("Email Address", [validators.Length(min=6, max=64)])
	password = PasswordField("Password", [validators.DataRequired()])

@app.route('/do_login', methods=['GET', 'POST'])
def do_login():
	user = User.query.filter_by(username=request.form['userinput']).first()
	return render_template('home.html', user=user)

#URL Handlers

@app.route('/newuser')
def new_user():
	return render_template('newuser.html')

@app.route('/editusers', methods=['POST'])
def edit_user():
	print("edit_user")
	
	users = User.query.all();
	for user in users:
		user_id = str(user.id)
		checked =  False if request.form.get(user_id) is None else True
		if checked: 
			db.session.delete(user)

	db.session.commit()

	return list_users()

@app.route('/adduser', methods=['POST'])
def add_user():
	user = User(request.form['userinput'], request.form['emailinput'], request.form['passwordinput'],)
	db.session.add(user)
	db.session.commit()
	return list_users()

@app.route('/listusers', methods=['GET'])
def list_users():
	users = User.query.all()
	return render_template('listusers.html', users=users)

@app.route('/listvenues', methods=['GET'])
def list_venues():
	venues = Venue.query.all()
	return render_template('listvenues.html', venues=venues)

@app.route('/getplaceids', methods=['GET', 'POST'])
def get_place_ids():
	ids = [venue.place_id for venue in Venue.query.all()]
	return jsonify(place_ids = ids)


@app.route('/newvenue')
def new_venue(place_id):
	return render_template('newvenue.html')

@app.route('/addvenue', methods=['POST'])
def add_venue():
	venue = Venue(request.form['venueinput'])
	venue.webaddr = request.form['venuewebsite']
	db.session.add(venue)
	db.session.commit()
	return list_venues()


@app.route('/editvenues', methods=['POST'])
def edit_venues():
	
	venues = Venue.query.all();
	for venue in venues:
		venue_id = str(venue.id)
		checked =  False if request.form.get(venue_id) is None else True
		if checked: 
			db.session.delete(venue)

	db.session.commit()

	return list_venues()

@app.route('/newevent/<place_id>/<venue_name>')
def new_event(place_id, venue_name):
	return render_template('newevent.html', 
			place_id=place_id, venue_name=venue_name)

@app.route('/addevent', methods=['POST'])
def add_event():
	event = Event()
	event.description = request.form['eventdescription']

	event.eventtype = request.form.get('eventtype')
	print(request.form.get('eventtype'), file=sys.stderr)

	event.sunday = False if request.form.get('checkbox_sunday') is None else True
	event.monday = False if request.form.get('checkbox_monday') is None else True
	event.tuesday = False if request.form.get('checkbox_tuesday') is None else True
	event.wednesday = False if request.form.get('checkbox_wednesday') is None else True
	event.thursday = False if request.form.get('checkbox_thursday') is None else True
	event.friday = False if request.form.get('checkbox_friday') is None else True
	event.saturday = False if request.form.get('checkbox_saturday') is None else True

	venue = Venue.query.filter_by(place_id=request.form['place_id']).first()
	if(venue == None):
		newvenue=Venue(request.form['venueinput'])
		newvenue.place_id = request.form['place_id']
		db.session.add(newvenue)
		db.session.commit()
		venue = Venue.query.filter_by(place_id=request.form['place_id']).first()

	event.venue_id = venue.id


	db.session.add(event)
	db.session.commit()
	return render_template('index.html', venues=Venue.query.all())	

@app.route('/listevents', methods=['GET'])
def list_events():
	events = Event.query.all()
	return render_template('listevents.html', events=events)

@app.route('/editevents', methods=['POST'])
def edit_events():
	events = Event.query.all();
	for event in events:
		id = str(event.id)
		checked =  False if request.form.get(id) is None else True
		if checked: 
			db.session.delete(event)

	db.session.commit()

	return list_events()

@app.route('/login')
def login():
	return render_template('login.html')

@app.route('/')
def welcome():
	return render_template('index.html', venues=Venue.query.all())


@app.route('/about')
def about():
	return "SQLAlchemy Version: " + sqlalchemy.__version__
