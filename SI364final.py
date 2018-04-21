import os
import requests
import json
from unsplash_client_id import client_id
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'hardtoguessstring'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/SI364projectplanhaelee"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# App addition setups
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

########################
######## Models ########
########################
tags = db.Table('tags', db.Column('photo_id', db.Integer, db.ForeignKey('photos.id')), db.Column('search_id', db.Integer, db.ForeignKey('searchterm.id')))

user_collection = db.Table('user_collection', db.Column('photo_id', db.Integer, db.ForeignKey('photos.id')), db.Column('collections_id', db.Integer, db.ForeignKey('unsplashCollection.id')))




## From HW4
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    collections = db.relationship('UnsplashCollection',backref='User')


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Photo(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key = True)
    likes = db.Column(db.String(10))
    url = db.Column(db.String(256))
    download = db.Column(db.String(256))
    color = db.Column(db.String(10))
    def __repr__(self):
        return "Title: {} | URL: {}".format(self.title, self.embedURL)

class UnsplashCollection(db.Model):
    __tablename__ = "unsplashCollection"
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    photos = db.relationship('Photo', secondary=user_collection, backref=db.backref('UnsplashCollection', lazy='dynamic'),lazy='dynamic')

class SearchTerm(db.Model):
    __tablename__ ="searchterm"
    id = db.Column(db.Integer, primary_key = True)
    term = db.Column(db.String(32), unique=True)
    photos = db.relationship('Photo',secondary=tags,backref=db.backref('searchterm',lazy='dynamic'),lazy='dynamic')
    def __repr__(self):
        return "Term Searched: {}".format(self.term)

class Background(db.Model):
    __tablename__="backgrounds"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    preference = db.Column(db.String(250))

    def __repr__(self):
        return "Name: {} | preference: {}".format(self.name, self.preference)

########################
######## Forms #########
########################

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class PhotoSearchForm(FlaskForm):
    search = StringField("Enter a term to search photos on Unsplash", validators=[Required()])
    submit = SubmitField('Submit')

class CollectionCreateForm(FlaskForm):
    name = StringField('Collection Name',validators=[Required()])
    photo_picks = SelectMultipleField('Select photos based on the number of likes to give you a unique collection!')
    submit = SubmitField("Create Collection")

class BackgroundForm(FlaskForm):
    name = StringField("What is your name?", validators=[Required()])
    preference = StringField("What is your wallpaper preference for your phone or laptop? (e.g. abstract, animals, family/friends)", validators=[Required()])
    submit = SubmitField("Submit")

    def validate_name(self, field):
        if len(field.data.split()) > 1:
            raise ValidationError("You may only enter one word name")

    def validate_preference(self, field):
        if field.data in ["$","#","*"]:
            raise ValidationError("You man NOT enter the speical characters: $, #, *")

class UpdateButtonForm(FlaskForm):
    submit = SubmitField("Update")

class UpdateInfoForm(FlaskForm):
    newPreference = StringField("Update information about your preference", validators=[Required()])
    submit = SubmitField("Update")

class DeleteButtonForm(FlaskForm):
    submit = SubmitField("Delete")

########################
### Helper functions ###
########################


def get_photos_from_unsplash(term):
    baseurl = "https://api.unsplash.com/search/photos"
    param = {'client_id':client_id,'query':str(term)}
    response = requests.get(baseurl, params = param)
    response_dict = json.loads(response.text)
    return response_dict['results']


# Provided
def get_photo_by_id(id):
    p = Photo.query.filter_by(id=id).first()
    return p

def get_or_create_photo(db_session, likes, url, download, color):
    p = db_session.query(Photo).filter_by(likes=likes).first()
    if p:
        return p
    else:
        p = Photo(likes=likes, url=url, download=download, color=color)
        db_session.add(p)
        db_session.commit()
    return p


def get_or_create_search_term(db_session, term):
    s = db_session.query(SearchTerm).filter_by(term=term).first()
    if s:
        return s
    else:
        s = SearchTerm(term = term)
        photo_list = get_photos_from_unsplash(term)
        for photo in photo_list:
            photo = get_or_create_photo(db_session, str(photo['likes']), photo['urls']['small'], photo['links']['download'],  photo['color'])
            s.photos.append(photo)
        db_session.add(s)
        db_session.commit()
    return s


def get_or_create_collection(db_session, name, current_user, photo_list=[]):
    collection = db_session.query(UnsplashCollection).filter_by(name=name,id=current_user.id).first()
    if collection:
        return collection
    else:
        collection = UnsplashCollection(name=name, user_id=current_user.id, photos=photo_list)
        for g in photo_list:
            collection.photos.append(g)
        db_session.add(collection)
        db_session.commit()
        return collection

def get_preference(name, preference):
    b = Background.query.filter_by(name=name).first()
    if b:
        return b
    else:
        b = Background(name=name, preference=preference)
        db.session.add(b)
        db.session.commit()
        return b

########################
#### View functions ####
########################

## Error handling routes - from HW4
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

## Login-related routes - from HW4
@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
    return "Only authenticated users can do this! Try to log in or contact the site admin."

@app.route('/', methods=['GET', 'POST'])
def index():
    form = PhotoSearchForm()
    if form.validate_on_submit():
        get_or_create_search_term(db.session, form.search.data)
        return redirect(url_for('search_results',search_term = form.search.data))
    return render_template('base.html',form=form)


@app.route('/photo_searched/<search_term>')
def search_results(search_term):
    form = PhotoSearchForm()
    term = SearchTerm.query.filter_by(term=search_term).first()
    relevant_photos = term.photos.all()
    return render_template('searched_photos.html',photos=relevant_photos,term=term)


@app.route('/search_terms')
def search_terms():
    all_terms = SearchTerm.query.all()
    return render_template('search_terms.html', all_terms = all_terms )

@app.route('/all_photos')
def all_photos():
    photos = Photo.query.all()
    return render_template('all_photos.html',all_photos=photos)



@app.route('/create_collection',methods=["GET","POST"])
@login_required
def create_collection():
    form = CollectionCreateForm()
    photos = Photo.query.all()
    choices = [(p.id, p.likes) for p in photos]
    form.photo_picks.choices = choices

    if request.method == 'POST':
        photos_selected = form.photo_picks.data
        photo_objects = [get_photo_by_id(int(id)) for id in photos_selected]
        get_or_create_collection(db.session,current_user=current_user, name=form.name.data, photo_list=photo_objects)
        return redirect(url_for('collections'))
    return render_template('create_collection.html',form=form)



## Renders collections.html after login, shows user's photo collection
@app.route('/collections',methods=["GET","POST"])
@login_required
def collections():
    collections = UnsplashCollection.query.all()
    return render_template('collections.html', collections=collections)


## Shows a single collection when clicked on. Shows all photos and renders collection.html.
@app.route('/collection/<id_num>')
def single_collection(id_num):
    id_num = int(id_num)
    collection = UnsplashCollection.query.filter_by(id=id_num).first()
    photos = collection.photos.all()
    return render_template('collection.html',collection=collection, photos=photos)



@app.route('/background', methods=["GET","POST"])
@login_required
def backgrounds():
    form = BackgroundForm()
    if form.validate_on_submit():
        name = form.name.data
        preference = form.preference.data
        new_answer = get_preference(name,preference)
        return redirect(url_for('b_info'))

    #CODE DIRECTLY FROM HW3 (210-212)
    errors = [v for v in form.errors.values()]
    if len(errors) >0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))

    return render_template('create_background.html',form=form)



@app.route('/b_info')
@login_required
def b_info():
    form = DeleteButtonForm()
    bgs = Background.query.all()
    return render_template('backgrounds.html', form=form, bgs=bgs)


@app.route('/one_bg/<ident>',methods=["GET","POST"]) #update
def one_bg(ident):
    form = UpdateButtonForm()
    b = Background.query.filter_by(name=ident).first()
    return render_template('background.html', form=form, b=b)

@app.route('/update/<pref>',methods=["GET","POST"])
def update(pref):
    form = UpdateInfoForm()
    if form.validate_on_submit():
        bgs = Background.query.filter_by(name=pref).first()
        print(bgs)
        bgs.preference = form.newPreference.data
        print(bgs.preference)
        db.session.commit()
        flash("Updated preference of {}".format(pref))
        return redirect(url_for("one_bg",ident=pref))
    return render_template("update_info.html", form=form, name=pref)


@app.route('/delete/<name>',methods=["GET","POST"])
def delete(name):
    b = Background.query.filter_by(name=name).first()
    print(b)
    db.session.delete(b)
    db.session.commit()
    flash("Deleted info {}".format(name))
    return redirect(url_for("b_info"))


if __name__ == '__main__':
    db.create_all()
    manager.run()
