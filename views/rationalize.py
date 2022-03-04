import flask
from app import app
from db import db
from flask import render_template, request
from models import vehicles, signals_table, systems, capture_modes, rationalized_list, completed_signals
import json

@app.route('/rationalize/<vehicle_id>', methods=["GET", "POST"])
def rationalize_parameter_list(vehicle_id):
    needExisting = False
    signals = signals_table.SignalsTable.query.all()
    if request.method == "GET":
        existing_info = rationalized_list.RationalizedList.query.filter_by(vehicle_id=vehicle_id).first()
        completed_signals_list = completed_signals.CompletedSignals.query.filter_by(vehicle_id=vehicle_id).first()
        if completed_signals_list is not None:
            cslist = completed_signals_list.completed_signals_list.split(',')
            needExisting = True
        if existing_info is None:
            existing_info = ""
        else:
            existing_info = str(existing_info.available_signals)
    if request.method == "POST":
        params = {}
        rationalized_information = rationalized_list.RationalizedList.query.filter_by(vehicle_id=vehicle_id).first()
        for item in request.form:
            if "toggleParam" in item:
                paramNum = item.split("toggleParam")[1]
                params[paramNum] = 'Park'
        if rationalized_information is None:
            new_rationale = rationalized_list.RationalizedList(
                vehicle_id=vehicle_id,
                available_signals=json.dumps(params)
            )
            db.session.add(new_rationale)
            db.session.commit()
        else:
            rationalized_information.available_signals = json.dumps(params)
            db.session.commit()
        return flask.redirect(flask.url_for('select_vehicle', vehicle_id=vehicle_id))
    if needExisting:
        return render_template('parameters.html', signals=signals, vehicle_id=vehicle_id, existing_info=existing_info, cslist=cslist)
    return render_template('parameters.html', signals=signals, vehicle_id=vehicle_id, existing_info=existing_info)