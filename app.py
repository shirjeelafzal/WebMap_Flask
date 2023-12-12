import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,EmailField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.types import Geometry
from flask_migrate import Migrate
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from geoalchemy2 import WKTElement
from flask_bootstrap import Bootstrap
from wtforms import StringField, IntegerField, DateTimeField,DateField
from wtforms.validators import DataRequired, Length, Optional
from sqlalchemy.exc import SQLAlchemyError
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tsatsatsa9@localhost:5432/actualdatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
Bootstrap(app)



class species_model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(100), nullable=False)
    common_name = db.Column(db.String(100), nullable=False)
    family = db.Column(db.String(80),  nullable=False)
    maximum_height = db.Column(db.Integer)
    beginning_of_flowering=db.Column(db.Date)
    end_of_flowering=db.Column(db.Date)
    trees = relationship('trees_model', back_populates='species')
    def __repr__(self) -> str:
        return f'{self.id} - {self.common_name}'

class trees_model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(Geometry(geometry_type='POINT', srid=4326))
    planting_date = db.Column(db.Date)
    state_of_conservation = db.Column(db.String(80), unique=True, nullable=False)
    height=db.Column(db.Integer)
    diameter=db.Column(db.Integer)
    last_pruning=db.Column(db.Date)
    gardener_id = db.Column(db.Integer, ForeignKey('gardeners_model.id'))
    species_id = db.Column(db.Integer, ForeignKey('species_model.id'))

    gardener = relationship('gardeners_model', back_populates='trees')
    species = relationship('species_model', back_populates='trees')
    def __repr__(self):
        return f'{self.id} - {self.state_of_conservation}'
    
    
    
class gardeners_model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80),  nullable=False)
    trees = relationship('trees_model', back_populates='gardener')
    def __repr__(self):
        return f'{self.id} - {self.name}'
#################forms####################
class SpeciesForm(FlaskForm):
    class Meta:
        model = species_model

    scientific_name = StringField('Scientific Name', validators=[DataRequired(), Length(max=100)])
    common_name = StringField('Common Name', validators=[DataRequired(), Length(max=100)])
    family = StringField('Family', validators=[DataRequired(), Length(max=80)])
    maximum_height = IntegerField('Maximum Height', validators=[DataRequired()])
    beginning_of_flowering = DateField('Beginning of Flowering', validators=[DataRequired()])
    end_of_flowering = DateField('End of Flowering', validators=[DataRequired()])
    
class GardenersForm(FlaskForm):
    class Meta:
        model=gardeners_model
    name = StringField('name', validators=[DataRequired(), Length(max=100)])
    surname = StringField('surname', validators=[DataRequired(), Length(max=100)])
    email = EmailField('email', validators=[DataRequired(), Length(max=100)])
#################################adding routes######################
@app.route('/')
def hello_world():
    return render_template('index.html')
@app.route('/species', methods=['GET', 'POST'])
def create_species():
    form = SpeciesForm()
    try:
        if form.validate_on_submit():
            # Create a new species instance and add it to the database
            model_data = {
                'scientific_name': form.scientific_name.data,
                'common_name': form.common_name.data,
                'family': form.family.data,
                'maximum_height': form.maximum_height.data,
                'beginning_of_flowering': form.beginning_of_flowering.data,
                'end_of_flowering': form.end_of_flowering.data,
            }
            new_species = species_model(**model_data)
            db.session.add(new_species)
            db.session.commit()
            return 'Species created successfully!'
    except SQLAlchemyError as e:
        db.session.rollback()  # Roll back the changes made in the current session
        print(f"Error: {e}")
        return 'Error creating species. Please try again.'
    return render_template('species.html', form=form)

@app.route('/gardeners', methods=['GET', 'POST'])
def create_gardeners():
    form = GardenersForm()
    try:
        if form.validate_on_submit():
            model_data = {
                'name': form.name.data,
                'surname': form.surname.data,
                'email': form.email.data,
            }
            new_species = gardeners_model(**model_data)
            db.session.add(new_species)
            db.session.commit()
            return 'Gardeners created successfully!'
    except SQLAlchemyError as e:
        db.session.rollback()  # Roll back the changes made in the current session
        print(f"Error: {e}")
        return 'Error creating gardener. Please try again.'
    return render_template('gardeners.html', form=form)































@app.route('/add_tree', methods=['POST'])
def add_tree():
    if request.method == 'POST':
        location_x = float(request.form['location_x'])
        location_y = float(request.form['location_y'])
        planting_date = datetime.strptime(request.form['planting_date'], '%Y-%m-%d')
        state_of_conservation = request.form['state_of_conservation']
        height = int(request.form['height'])
        diameter = int(request.form['diameter'])
        last_pruning = datetime.strptime(request.form['last_pruning'], '%Y-%m-%d')

        # Create a WKT(well known text) point from the coordinates
        location = WKTElement(f'POINT({location_x} {location_y})', srid=4326)

        new_tree = trees_model(
            location=location,
            planting_date=planting_date,
            state_of_conservation=state_of_conservation,
            height=height,
            diameter=diameter,
            last_pruning=last_pruning
        )

        db.session.add(new_tree)
        db.session.commit()

        return redirect(url_for('some_success_page'))  # Redirect to a success page or another route
    else:
        return render_template('add_tree_form.html')  # Render a form to add trees









if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
