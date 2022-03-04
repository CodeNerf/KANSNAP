import shutil

import flask
from app import app
from flask import render_template, request
from models import vehicles, phone_list, signals_table, completed_signals, rationalized_list
import json
import pathlib
import os
from static.configurations.upload_information import upload_creds
import pysftp
import time
import threading

all_paths = []
all_required = []
items_to_upload = {}
item_count = 0
root_path = ""

@app.route('/upload')
def upload():
    global item_count

    item_count = 0
    need_vehicles = []
    all_vehicles = vehicles.Vehicles.query.all()
    for vehicle in all_vehicles:
        completed =  completed_signals.CompletedSignals.query.filter_by(vehicle_id=vehicle.vehicle_id).all()
        if completed != []:
            need_vehicles.append(vehicle)
    return render_template('upload.html', all_vehicles=need_vehicles)


@app.route('/upload/get_completed/<vehicle_id>', methods=['GET'])
def upload_get_data(vehicle_id):
    global all_paths
    global all_required
    global root_path

    all_required =[]
    needed_signals = []
    all_paths = []
    uploaded_signals = []
    all_files = {}
    selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent

    completed_sigs = completed_signals.CompletedSignals.query.filter_by(vehicle_id=vehicle_id).all()
    root_path = f"{path}/static/captures/{selected_vehicle.VIN}"
    for signal in completed_sigs:
        for sig in signal.completed_signals_list.split(','):
            needed_signals.append(sig)

    with sftp_connection() as sftp:
        for sig in needed_signals:
            if sftp.exists(f"{upload_creds['server_path']}/{selected_vehicle.VIN}/{sig}"):
                if sig not in uploaded_signals:
                    uploaded_signals.append(sig)
                    print(uploaded_signals)
                needed_signals.remove(sig)
    print(uploaded_signals)
    for signal in needed_signals:
        log_path = f"{path}/static/captures/{selected_vehicle.VIN}/{signal}/"
        video_path = log_path + 'videos/'
        all_paths.append(log_path)
        all_paths.append(video_path)

    try:
        for path in all_paths:
            if not (os.path.exists(path)):
                continue
            param_id = path.split('captures/')[1].split("/")[1].split("/")[0]

            for item in os.listdir(path):
                if 'videos' not in item:
                    all_files[item] = param_id
    except Exception as e:
        all_files['error'] = str(e)


    for path in all_paths:
        if(os.path.exists(path)):
            for file in os.listdir(path):
                if '.' in file:
                    all_required.append(path + file)
    all_files['uploaded'] = uploaded_signals
    json.dumps(all_files)
    return all_files


@app.route('/upload/upload_files/<vehicle_id>', methods=["POST"])
def upload_push_assets(vehicle_id):
    global items_to_upload
    global all_required
    global item_count

    selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
    item_count = len(all_required)
    for file in all_required:
        if 'videos' in file:
            file_name = file.split(selected_vehicle.VIN)[1].split("/")[3]
        else:
            file_name = file.split(selected_vehicle.VIN)[1].split("/")[2]
        items_to_upload[file_name] = False

    # cnopts = pysftp.CnOpts()
    # cnopts.hostkeys = None

    pi_path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    new_path= f"{upload_creds['server_path']}/{selected_vehicle.VIN}/"

    with sftp_connection() as sftp:
        if selected_vehicle.VIN not in sftp.listdir(f"{upload_creds['server_path']}"):
            sftp.mkdir(new_path)
        sftp.chdir(new_path)
        for file in all_required:
            param_num = str(file).split(selected_vehicle.VIN)[1].split("/")[1]
            param_path = new_path + param_num
            if param_num not in sftp.listdir(new_path):
                sftp.mkdir(param_path)
            sftp.chdir(param_path)
            if 'videos' in file:
                if 'videos' not in sftp.listdir(param_path):
                    sftp.mkdir(f"{param_path}/videos")
                sftp.chdir(f"{param_path}/videos")
                sftp.put(file)
                items_to_upload[file.split(selected_vehicle.VIN)[1].split("/")[3]] = True
            else:
                sftp.chdir(param_path)
                sftp.put(file)
                items_to_upload[file.split(selected_vehicle.VIN)[1].split("/")[2]] = True
            sftp.chdir(new_path)
            item_count -= 1
    return 'test'

@app.route('/upload/status', methods=["GET"])
def upload_status():
    global items_to_upload
    global item_count
    print(item_count)
    items_to_upload['complete'] = False
    if item_count == 0:
        items_to_upload['complete'] = True
        shutil.rmtree(root_path)
        flask.flash("Finished Uploading")
        # time.sleep(1)
        # return flask.redirect(flask.url_for('upload'))
    flask.json.dumps(items_to_upload)
    return items_to_upload

def sftp_connection():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    sftp = pysftp.Connection(upload_creds['server'],
                      username=upload_creds['username'],
                      password=upload_creds['password'],
                      cnopts=cnopts)
    return sftp



