import flask
from app import app
from db import db
from flask import request, render_template
from models import vehicles
import can
from static.configurations.config import config_dictionary

@app.route('/vehicles/select', methods=["GET", "POST"])
def select_vehicle(vehicle_id=0):

    args = request.args.to_dict()
    if check_key(args, 'vehicle_id'):
        vehicle_id = args['vehicle_id']
    form_data = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
    initiate_can_busses(vehicle_id)
    if request.method == "POST":
        form_data.VIN = request.form['vehicle_vin']
        form_data.model_year = request.form['vehicle_year']
        form_data.model = request.form['vehicle_model']
        form_data.vehicle_make = request.form['vehicle_make']
        form_data.transmission_type = request.form['vehicle_transmission']
        form_data.trim_notes = request.form['vehicle_options']
        form_data.networks_list = request.form['networks_list']
        db.session.commit()
        return flask.redirect(flask.url_for('select_vehicle', vehicle_id=vehicle_id))
    return render_template('select_vehicle_options.html', vehicle_id=vehicle_id, can_busses=can_busses,
                           config_dictionary=config_dictionary, form_data=form_data)


def initiate_can_busses(vehicle_id):
    global busses
    global can_busses

    busses = []

    v = vehicles.Vehicles.query.get(vehicle_id)
    can_busses = v.networks_list.strip().split(',')
    for can_bus in can_busses:
        try:
            busses.append(can.interface.Bus(channel=can_bus.strip(), interface='socketcan'))
        except OSError as e:
            print(f"INITITIATE CAN BUS ERROR:On appending {can_bus} received error: {e}")
            return False, f"{can_bus} received error: {e}"

    return True, f"Success"

def check_key(dictionary, key):
    if key in dictionary.keys():
        return True
    return False