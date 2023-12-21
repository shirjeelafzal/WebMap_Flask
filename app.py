import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, FloatField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.types import Geometry
from flask_migrate import Migrate
from sqlalchemy import ForeignKey
from flask import flash,Blueprint
from sqlalchemy.orm import relationship
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from geoalchemy2 import WKTElement
from flask_bootstrap import Bootstrap
from wtforms import StringField, IntegerField, DateField, SelectField
from wtforms.validators import DataRequired, Length
from sqlalchemy.exc import SQLAlchemyError
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from sqlalchemy import func
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from geoalchemy2.shape import to_shape

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tsatsatsa9@localhost:5432/actualdatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Only set this in a production environment with HTTPS

db = SQLAlchemy(app)
migrate = Migrate(app, db)
Bootstrap(app)
admin = Admin(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Example using Blueprints


species_blueprint = Blueprint('species', __name__)

@login_manager.user_loader
def load_user(user_id):
    return user_model.query.get(int(user_id))


class user_model(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


class species_model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(100), nullable=False)
    common_name = db.Column(db.String(100), nullable=False)
    family = db.Column(db.String(80),  nullable=False)
    maximum_height = db.Column(db.Integer)
    beginning_of_flowering = db.Column(db.Date)
    end_of_flowering = db.Column(db.Date)
    trees = relationship('trees_model', back_populates='species')

    def __repr__(self) -> str:
        return f'{self.id} - {self.common_name}'


class trees_model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(Geometry(geometry_type='POINT', srid=4326))
    planting_date = db.Column(db.Date)
    state_of_conservation = db.Column(db.String(80))
    height = db.Column(db.Integer)
    diameter = db.Column(db.Integer)
    last_pruning = db.Column(db.Date)
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

# def TreesView(BaseModelView):

#     column_list =["location","planting_date","state_of_conservation","height","diameter","last_pruning","gardener","species"]
#################### Registering models in admin##############
admin.add_view(ModelView(user_model, db.session, name='User'))
admin.add_view(ModelView(trees_model, db.session, name='Trees'))
admin.add_view(ModelView(species_model, db.session, name='Species'))
admin.add_view(ModelView(gardeners_model, db.session, name='Gardeners'))
################# forms####################

class SignupForm(FlaskForm):
    class Meta:
        model = user_model
    first_name = StringField('First Name', validators=[
                             DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[
                            DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(max=100)])

    submit=SubmitField("Submit")

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(max=100)])
    submit=SubmitField("Login")

class SpeciesForm(FlaskForm):
    class Meta:
        model = species_model

    scientific_name = StringField('Scientific Name', validators=[Length(max=100), DataRequired()])
    common_name = StringField('Common Name', validators=[Length(max=100), DataRequired()])
    family = StringField('Family', validators=[Length(max=80), DataRequired()])
    maximum_height = IntegerField(
        'Maximum Height', validators=[DataRequired()])
    beginning_of_flowering = DateField(
        'Beginning of Flowering', validators=[DataRequired()])
    end_of_flowering = DateField(
        'End of Flowering', validators=[DataRequired()])
    submit=SubmitField("Submit")

class GardenersForm(FlaskForm):
    class Meta:
        model = gardeners_model
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    surname = StringField('Surname', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Submit")

class TreesForm(FlaskForm):
    class Meta:
        model = trees_model
    location_x = FloatField('Location X', validators=[DataRequired()])
    location_y = FloatField('Location Y', validators=[DataRequired()])
    planting_date = DateField('Planting Date', validators=[DataRequired()])
    state_of_conservation = StringField('State of Conservation', validators=[DataRequired()])
    height = IntegerField('Height', validators=[DataRequired()])
    diameter = IntegerField('Diameter', validators=[DataRequired()])
    last_pruning = DateField('Last Pruning', validators=[DataRequired()])
    gardener_id = SelectField('Gardener', coerce=int,validators=[DataRequired()],choices=[])
    species_id = SelectField('Species', coerce=int,validators=[DataRequired()],choices=[])
    submit=SubmitField("Submit")
################################# adding routes######################

@app.route('/')
def dashboard():
    try:
        trees = trees_model.query.all()
        points = [(to_shape(tree.location).x, to_shape(tree.location).y) for tree in trees]
        print('Points:', points)
        trees_data = [
            {
                'id': tree.id,
                'location': (to_shape(tree.location).x, to_shape(tree.location).y),
                'planting_date': tree.planting_date.strftime('%Y-%m-%d'),
                'state_of_conservation': tree.state_of_conservation,
                'height': tree.height,
                'diameter': tree.diameter,
                'last_pruning': tree.last_pruning.strftime('%Y-%m-%d'),
                'gardener_id': tree.gardener_id,
                'species_id': tree.species_id,
                'species_name':species_model.query.get(tree.species_id).common_name,
            }
            for tree in trees
        ]
        return render_template('index.html', trees_data=trees_data,points=points)
    except SQLAlchemyError as e:
        print(f"Error: {e}")
        return 'Error fetching tree data.'

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = user_model.query.filter_by(email=form.email.data).first()
        if user:
            # check the password
            if user.password == form.password.data:
                login_user(user)
                flash('Login Successful')
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong  Password - Try again")
                redirect(url_for('login'))
        else:
            flash("Email is incorrect")
            redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Logout Successful')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    try:
        if form.validate_on_submit():
            # Create a new species instance and add it to the database
            model_data = {
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'email': form.email.data,
                'password': form.password.data,
            }
            new_species = user_model(**model_data)
            db.session.add(new_species)
            db.session.commit()
            return 'User created successfully!'
    except SQLAlchemyError as e:
        db.session.rollback()  # Roll back the changes made in the current session
        print(f"Error: {e}")
        return 'Error creating user. Please try again.'
    return render_template('signup.html', form=form)


@app.route('/species', methods=['GET', 'POST'])
@login_required
def species():
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
            flash('Form Submitted Successfully')
            form.process()
            form.errors.clear()
            return redirect(url_for("species"))
    except SQLAlchemyError as e:
        db.session.rollback()  # Roll back the changes made in the current session
        print(f"Error: {e}")
        return 'Error creating species. Please try again.'
    species = species_model.query.all()
    return render_template('species.html', form=form, species=species)


@app.route('/species/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_species(id):
    try:
        specie_to_delete=species_model.query.get_or_404(id)
        if specie_to_delete:
            db.session.delete(specie_to_delete)
            db.session.commit()
            flash("Specie has been deleted")
            return redirect(url_for("species"))
    except:
        flash("Error deleting the specie. Try again")
        return redirect(url_for('species'))
@app.route('/species/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_species(id):
    form=SpeciesForm()
    specie_to_update=species_model.query.get_or_404(id)
    if form.validate_on_submit():
        specie_to_update.scientific_name=form.scientific_name.data
        specie_to_update.common_name=form.common_name.data
        specie_to_update.family=form.family.data
        specie_to_update.maximum_height=form.maximum_height.data
        specie_to_update.beginning_of_flowering=form.beginning_of_flowering.data
        specie_to_update.end_of_flowering=form.end_of_flowering.data
        db.session.commit()
        flash("Specie has been updated.")
        return redirect(url_for('species'))
    return render_template('update_species',form=form,specie_to_update=specie_to_update)

@app.route('/gardeners', methods=['GET', 'POST'])
@login_required
def gardeners():
    form = GardenersForm()
    if request.method == 'POST':
        try:
            if form.validate_on_submit():
                model_data = {
                    'name': form.name.data,
                    'surname': form.surname.data,
                    'email': form.email.data,
                }
                new_gardener = gardeners_model(**model_data)
                db.session.add(new_gardener)
                db.session.commit()
                flash('Form Submitted Successfully.')
                form.process()
                form.errors.clear()
                return redirect(url_for('gardeners'))
        except SQLAlchemyError as e:
            db.session.rollback()  # Roll back the changes made in the current session
            print(f"Error: {e}")
            flash('Error creating gardener. Please try again.')
            return redirect(url_for('gardeners'))

    gardeners = gardeners_model.query.all()
    return render_template('gardeners.html', form=form, gardeners=gardeners)

@app.route('/gardeners/delete/<int:id>')
@login_required
def delete_gardeners(id):
    try:
        gardener_to_delete=gardeners_model.query.get_or_404(id)
        if gardener_to_delete:
            db.session.delete(gardener_to_delete)
            db.session.commit()
            flash("Gardener has been deleted")
            return redirect(url_for("gardeners"))
    except:
        flash("Error deleting the gardener. Try again")
        return redirect(url_for('gardeners'))

@app.route('/gardeners/update/<int:id>',methods=['GET','POST'])
@login_required
def update_gardeners(id):
    form=GardenersForm()
    gardener_to_update=gardeners_model.query.get_or_404(id)
    if form.validate_on_submit():
        gardener_to_update.name=form.name.data
        gardener_to_update.surname=form.surname.data
        gardener_to_update.email=form.email.data
        db.session.commit()
        flash("Gardener has been updated.")
        return redirect(url_for("gardeners"))
    return render_template('update_gardeners.html',form=form,gardener_to_update=gardener_to_update)

@app.route('/trees', methods=['GET', 'POST'])
@login_required
def trees():
    form = TreesForm()
    lon = request.args.get('lon')
    lat = request.args.get('lat')

    species = species_model.query.all()
    gardeners = gardeners_model.query.all()

    species_choices = [(specie.id, specie.common_name) for specie in species]
    gardener_choices = [(gardener.id, gardener.name) for gardener in gardeners]

    form.species_id.choices = species_choices
    form.gardener_id.choices = gardener_choices

    try:
        if form.validate_on_submit():
            # Process form submission
            location_x = float(form['location_x'].data)
            location_y = float(form['location_y'].data)

            model_data = {
                'planting_date': datetime.strptime(str(form['planting_date'].data), '%Y-%m-%d'),
                'state_of_conservation': form['state_of_conservation'].data,
                'height': int(form['height'].data),
                'diameter': int(form['diameter'].data),
                'last_pruning': datetime.strptime(str(form['last_pruning'].data), '%Y-%m-%d'),
                'gardener_id': int(form['gardener_id'].data),
                'species_id': int(form['species_id'].data),
                'location': WKTElement(f'POINT({location_x} {location_y})', srid=4326),
            }

            new_tree = trees_model(**model_data)
            db.session.add(new_tree)
            db.session.commit()
            
            flash('Form Submitted Successfully')
            return redirect(url_for('trees'))
        else:
            print(f'errors: {form.errors}')
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error: {e}")

    trees = trees_model.query.all()

    if lon is not None and lat is not None:
        return render_template('trees.html', form=form, trees=trees, lon=lon, lat=lat)

    return render_template('trees.html', form=form, trees=trees)

@app.route('/trees/delete/<int:id>')
@login_required
def delete_trees(id):
    try:
        tree_to_delete=trees_model.query.get_or_404(id)
        if tree_to_delete:
            db.session.delete(tree_to_delete)
            db.session.commit()
            flash("Tree has been deleted")
            return redirect(url_for("trees"))
    except:
        flash("Error deleting the tree. Try again")
        return redirect(url_for('trees'))

@app.route('/trees/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_trees(id):
    tree_to_update = trees_model.query.get_or_404(id)
    species = species_model.query.all()
    gardeners = gardeners_model.query.all()

    species_choices = [(specie.id, specie.common_name) for specie in species]
    gardener_choices = [(gardener.id, gardener.name) for gardener in gardeners]

    form = TreesForm(obj=tree_to_update) 
    form.species_id.choices = species_choices
    form.gardener_id.choices = gardener_choices

    if form.validate_on_submit():
        try:
            location_x = float(form.location_x.data)
            location_y = float(form.location_y.data)
            location = WKTElement(f'POINT({location_x} {location_y})', srid=4326)
            tree_to_update.location = location
            tree_to_update.height=form.height.data
            tree_to_update.planting_date=form.planting_date.data
            tree_to_update.species_id=form.species_id.data
            tree_to_update.state_of_conservation=form.state_of_conservation.data
            tree_to_update.diameter=form.diameter.data
            tree_to_update.last_pruning=form.last_pruning.data
            tree_to_update.gardener_id=form.gardener_id.data
            db.session.commit()
            flash("Tree has been updated.")
            return redirect(url_for("trees"))
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error: {e}")
            flash("Error updating tree.")
    if tree_to_update:
        location = tree_to_update.location
        query = db.session.query(
            func.ST_X(location).label('location_x'),
            func.ST_Y(location).label('location_y')
        )
        result = query.first()
        location_x = result.location_x
        location_y = result.location_y
    print("about to render the update.html")
    return render_template('update_trees.html', form=form, tree_to_update=tree_to_update, location_x=location_x, location_y=location_y)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
