import flask
from db import db
from app import app
from flask import request, render_template, redirect, url_for
from models import vehicles
from static.configurations.config import config_dictionary
import logger
import can

@app.route('/vehicle_setup', methods=['POST', 'GET'])
def vehicle_setup():
    # read_bus()
    db.create_all()
    form_data = request.form
    if(request.method == 'GET'):
        return render_template('vehicle_setup.html', config_dictionary=config_dictionary, form_data=form_data)
    if(request.method == 'POST'):
        new_vehicle = vehicles.Vehicles(
            model_year = request.form['vehicle_year'],
            vehicle_make = request.form['vehicle_make'],
            model = request.form['vehicle_model'],
            VIN = request.form['vehicle_vin'],
            transmission_type = request.form['vehicle_transmission'],
            trim_notes = request.form['vehicle_options'],
            networks_list = request.form['networks_list']
        )
        db.session.add(new_vehicle)
        db.session.commit()
        logger.CaptureActivityLogs.capture_status_to_log(request.form['vehicle_vin'], None, "Added Vehicle")
        flask.flash(f"Successfully Added "
                    f"{request.form['vehicle_year']} "
                    f"{request.form['vehicle_make']} "
                    f"{request.form['vehicle_model']} to database!")
        return flask.redirect(url_for('main'))


#
# def read_bus():
#     bus = can.Bus(interface='socketcan', channel='can0')
#     for msg in bus:
#         try:
#             print(bytes.fromhex(msg.data.hex()).decode('utf-8'))
#         except:
#             pass
#         # raw_string = str(msg.data).replace("bytearray(b'", "").replace("')", "")
#         # print(raw_string)
#         # ascii_text = bytes.fromhex(raw_string).decode('ASCII')
#         # print(ascii_text)


