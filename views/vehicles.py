from app import app
from flask import render_template
from models import vehicles
from static.configurations.config import config_dictionary

@app.route('/vehicles/<vehicle_id>')
@app.route('/vehicles/')
def list_vehicles(vehicle_id=None):
    all_vehicles = vehicles.Vehicles.query.all()
    return render_template('list_vehicles.html', all_vehicles=all_vehicles, config_dictionary=config_dictionary)
