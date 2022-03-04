import flask
from app import app
from db import db
from flask import render_template, request, redirect
from models import vehicles, signals_table, systems, capture_modes, rationalized_list, completed_signals
import json

@app.route('/parameters/<vehicle_id>', methods=['GET', 'POST'])
def show_parameter_list(vehicle_id):
    needExisting = False
    signals_list = []
    pull = rationalized_list.RationalizedList.query.filter_by(vehicle_id=vehicle_id).first()
    completed_signals_list = completed_signals.CompletedSignals.query.filter_by(vehicle_id=vehicle_id).first()
    if completed_signals_list is not None:
        needExisting = True
        cslist = completed_signals_list.completed_signals_list.split(',')
    if pull is None or pull.available_signals == "{}":
        flask.flash("No Parameters Rationalized")
        return redirect(f'/vehicles/select?vehicle_id={vehicle_id}')
    existing_info = str(pull.available_signals)
    for item in json.loads(pull.available_signals):
        signals_list.append(item)
    signals = signals_table.SignalsTable.query.filter(signals_table.SignalsTable.signal_id.in_(signals_list)).all()
    if request.method == "POST":
        return redirect(flask.url_for('capture_page', vehicle_id=vehicle_id, param=request.form['signal_id']))
    if needExisting:
        return render_template('choose_parameter.html', existing_info=existing_info, signals=signals, cslist=cslist)
    return render_template('choose_parameter.html', existing_info=existing_info, signals=signals)
