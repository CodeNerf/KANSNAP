import flask
from app import app
from db import db
from flask import render_template, request
from models import signals_table
import logger

@app.route('/edit_parameters', methods=["GET", "POST"])
def edit_parameters():
    signals = signals_table.SignalsTable.query.all()
    if flask.request.method == "POST":
        if 'new_signal_btn' in flask.request.form:
            add_signal(flask.request.form['signalDescription'])
            logger.CaptureActivityLogs.capture_status_to_log(None, flask.request.form['signalDescription'], "Added Signal")
        if 'delete_signal_btn' in flask.request.form:
            delete_signal(flask.request.form['signalDescription'])
            logger.CaptureActivityLogs.capture_status_to_log(None, flask.request.form['signalDescription'], "Deleted Signal")
        if 'edit_signal_btn' in flask.request.form:
            edit_signal(flask.request.form['storedSignalDesc'], flask.request.form['signalDescription'])
            logger.CaptureActivityLogs.capture_status_to_log(None, flask.request.form['signalDescription'], f"Changed Signal from {flask.request.form['storedSignalDesc']}")
        signals = signals_table.SignalsTable.query.all()
        return render_template('edit_parameters.html', signals=signals)
    return render_template('edit_parameters.html', signals=signals)

def add_signal(signal_desc):
    new_signal = signals_table.SignalsTable(
        signal_description=signal_desc,
        system = None,
        units = None,
        capture_mode = "Park",
        vehicle_id= 0
    )
    db.session.add(new_signal)
    db.session.commit()

def delete_signal(signal_desc):
    signal = signals_table.SignalsTable.query.filter_by(signal_description=signal_desc).first()
    db.session.delete(signal)
    db.session.commit()

def edit_signal(stored, signal_desc):
    signal = signals_table.SignalsTable.query.filter_by(signal_description=stored).first()
    signal.signal_description = signal_desc
    db.session.commit()