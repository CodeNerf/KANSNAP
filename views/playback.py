from app import app
from flask import render_template, request
from models import vehicles, phone_list, signals_table, completed_signals, rationalized_list
import json
import pathlib
import os


@app.route('/playback')
def playback():
    all_vehicles = vehicles.Vehicles.query.all()
    return render_template('playback.html', all_vehicles=all_vehicles)


@app.route('/playback/get_completed/<vehicle_id>', methods=['GET'])
def get_data(vehicle_id):
    output = {}
    completed_sigs = completed_signals.CompletedSignals.query.filter_by(vehicle_id=vehicle_id).all()
    needed_signals = []
    for signal in completed_sigs:
        for sig in signal.completed_signals_list.split(','):
            sig_info = {}
            sig_find = signals_table.SignalsTable.query.filter_by(signal_id=sig).first().signal_description
            sig_info[sig] = sig_find
            needed_signals.append(sig_info)
    output['signal_list'] = needed_signals
    json.dumps(output)
    return output


@app.route('/playback/get_assets/<vehicle_id>/<signal_id>', methods=["GET"])
def get_assets(vehicle_id, signal_id):
    data = {}
    selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    log_path = f"{path}/static/captures/{selected_vehicle.VIN}/{signal_id}/"
    data['log_path'] = log_path
    json.dumps(data)
    return data
