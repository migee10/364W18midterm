##Michele Gee
## SI 364 - Winter 2018
##Midterm

####################
## Import statements
####################

from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell

import requests
import json

############################
# Application configurations
############################
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hard to tguess string from si364'
## TODO 364: Create a database in postgresql in the code line below, and fill in your app's database URI. It should be of the format: postgresql://localhost/YOUR_DATABASE_NAME

## Your final Postgres database should be your uniqname, plus HW3, e.g. "jczettaHW3" or "maupandeHW3"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/midterm"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################

db = SQLAlchemy(app) # For database use

url = "https://pokeapi.co/api/v2/pokemon/"

#########################
#########################
######### Everything above this line is important/useful setup,
## not problem-solving.##
#########################
#########################

#########################
##### Set up Models #####
#########################

## TODO 364: Set up the following Model classes, as described, with the respective fields (data types).

class Pokemon(db.Model):
    __tablename__:'pokemon'
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String(280))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return "({%r}) (ID:%r)" % (self.text, self.id)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), unique = True)
    team_name = db.Column(db.String(124))
    pokemon = db.relationship('Pokemon',backref='User')

    def __repr__(self):
        return "({%r}) (ID:%r)" % (self.username, self.id)


########################
##### Set up Forms #####
########################


class pokemonentryform(FlaskForm):
    text= StringField("Choose your Pokemon:", validators=[Required(),Length(1,280)])
    username = StringField("Enter your Name:",validators=[Required(),Length(1,64)])
    team_name = StringField("Enter your Team Name:",validators=[Required(),Length(1,64)])
    submit = SubmitField()

    def validate_team_name(self, field):
        if len(field.data.split()) < 1:
            raise ValidationError("team name must be at least 1 word long")


class PokemonForm(FlaskForm):
    pokemonName = StringField("Enter a pokemon:", validators=[Required()])
    submit = SubmitField('Submit')


###################################
##### Routes & view functions #####
###################################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():

    form = pokemonentryform()

    num_pokemon = db.session.query(Pokemon).count()

    if form.validate_on_submit():

    	username = form.username.data
    	team_name = form.team_name.data
    	user = User.query.filter_by(username=username).first()

    	if not user:
    		user = User(username=username,team_name=team_name)
    		db.session.add(user)
    		db.session.commit()

    	text= form.text.data
    	pokemon = Pokemon.query.filter_by(text=text,user_id=user.id).first()
    	if pokemon:
    		flash('Pokemon not added, pokemon already exists!')

    		return redirect(url_for('see_all_pokemon'))

    	pokemons = Pokemon(text=text,user_id=user.id)
    	db.session.add(pokemons)
    	db.session.commit()


    	flash('Pokemon has been successfully added to the database #GottaCatchEmAll')


    	return redirect(url_for('index'))

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
    	errstr = "!!!! ERRORS IN FORM SUBMISSION - "
    	errstr+=' --- '.join([error[0] for error in errors])
    	flash(errstr)
    return render_template('indexx.html', form=form, num_pokemon=num_pokemon)


@app.route('/see_all_pokemon')
def see_all_pokemon():
    #tweetlist = Tweet.query.all()
    pokemonlist = Pokemon.query.all()

    all_pokemon = []
    for pokemon in pokemonlist:
        user = User.query.filter_by(id=pokemon.user_id).first()
        holder = (pokemon.text, user.username)
        all_pokemon.append(holder)
    return render_template('all_pokemon.html', all_pokemon = all_pokemon)


@app.route('/all_users')
def go_to_users():
    users = User.query.all()
    return render_template('all_players.html', users=users)


@app.route('/pokemon')
def pokemon_form():
    pokemonForm = PokemonForm()
    return render_template('pokemon.html',form=pokemonForm)

@app.route('/pokemondata', methods = ['GET', 'POST'])
def pokemon_result():
    form = PokemonForm()
    if form.validate_on_submit():
        pokemonName = form.pokemonName.data
        response = form.pokemonName.data

        base_url = "https://pokeapi.co/api/v2/pokemon/" + pokemonName
        spond = requests.get(base_url)
        spond_text = spond.text
        spond_json = json.loads(spond_text)
        nameof = (spond_json['forms'][0]['name'])
        baseexp = (spond_json['base_experience'])
        firstmove = (spond_json['moves'][0]['move']['name'])
        height = (spond_json['types'][0]['type']['name'])

        if spond.status_code != 200:
            flash('Something went wrong, try entering again!')
            return redirect(url_for('pokemon_form'))

        pokemonresults = json.loads(spond.text)
        return render_template('psokemondata.html', data = pokemonresults)
    flash('All frields are required!')
    return redirect(url_for('pokemon_form'))

    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('pokemon.html', form=form)


if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
