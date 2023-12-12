from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from geoalchemy2 import types
from flask_migrate import Migrate
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:tsatsatsa9@localhost:5432/actualdatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
class species_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(100), unique=True, nullable=False)
    common_name = db.Column(db.String(100), unique=True, nullable=False)
    family = db.Column(db.String(80), unique=True, nullable=False)
    maximum_height = db.Column(db.Integer)
    beginning_of_flowering=db.Column(db.DateTime)
    end_of_flowering=db.Column(db.DateTime)
    
    def __repr__(self) -> str:
        return f'{self.id} - {self.username} {self.common_name}'

class trees_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(types.Geometry(geometry_type='POINT', srid=4326))
    planting_date = db.Column(db.DateTime)
    state_of_conservation = db.Column(db.String(80), unique=True, nullable=False)
    height=db.Column(db.Integer)
    diameter=db.Column(db.Integer)
    last_pruning=db.Column(db.DateTime)
    
    def __repr__(self) -> str:
        return f'{self.id} - {self.username}'
    
    
    
class gardeners_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    surname = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f'{self.id} - {self.username}'


@app.route('/')
def hello_world():
    return render_template('index.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
