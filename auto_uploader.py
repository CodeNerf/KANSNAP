import pathlib
import subprocess
import os
import pysftp
import time
import shutil
import cv2
import tarfile
import random
import requests, json
from models import vehicles, completed_signals
from static.configurations.upload_information import upload_creds
from datetime import datetime

server_found = False
upload_completed = False
all_paths = []
all_required = []
items_to_upload = {}
item_count = 0
all_roots = []
vehicle_ids = []

def network_monitor():
    global server_found
    global upload_completed
    global upload_completed
    global all_roots

    all_roots = []
    test_ip = "192.168.7.207"


    while True:
        # req = requests.get('http://192.168.2.171:5006/param_capture_readout') #TODO: Detect if capture currently happening and wait
        resp = subprocess.Popen(['ping', test_ip, '-c', '1', '-W', '2'])
        resp.wait()
        if resp.poll():
            time.sleep(30)
            pass
        else:
            print('initializing')
            initialize_upload()
            break


def initialize_upload():
    global all_paths
    global all_required
    global all_roots
    global vehicle_ids

    vehicle_ids = []
    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    path = str(path) + '/canSNARE'
    all_required = []
    needed_signals = []
    all_paths = []
    uploaded_signals = []
    all_files = {}
    vins = []
    dirs = os.listdir(f"{path}/static/captures")

    print(dirs)
    for dir in dirs:
        print(dir)
        vins.append(str(dir))

    for vin in vins:
        selected_vehicle = vehicles.Vehicles.query.filter_by(VIN=vin).first()
        vehicle_id = selected_vehicle.vehicle_id
        vehicle_ids.append(vehicle_id)
        completed_sigs = completed_signals.CompletedSignals.query.filter_by(vehicle_id=vehicle_id).all()

        for signal in completed_sigs:
            for sig in signal.completed_signals_list.split(','):
                needed_signals.append(sig)

        with sftp_connection() as sftp:
            for sig in needed_signals:
                if sftp.exists(f"{upload_creds['server_path']}/{selected_vehicle.VIN}/{sig}"):
                    if sig not in uploaded_signals:
                        uploaded_signals.append(sig)
                    needed_signals.remove(sig)

        print(needed_signals)
        for signal in needed_signals:
            log_path = f"{path}/static/captures/{selected_vehicle.VIN}/{signal}/"
            if os.path.exists(log_path):
                all_roots.append(log_path[:-1])
            video_path = log_path + 'videos/'
            all_paths.append(log_path)
            all_paths.append(video_path)

        for path in all_paths:
            if not (os.path.exists(path)):
                continue
            param_id = path.split('captures/')[1].split("/")[1].split("/")[0]
            for item in os.listdir(path):
                if 'videos' not in item:
                    all_files[item] = param_id

        for path in all_paths:
            if (os.path.exists(path)):
                for file in os.listdir(path):
                    if '.' in file:
                        all_required.append(path + file)

        print(all_required)
        all_files['uploaded'] = uploaded_signals
    if len(all_required) == 0:
        time.sleep(30)
        network_monitor()
    upload_files()

def upload_files():
    global items_to_upload
    global all_required
    global item_count
    global upload_completed

    for vehicle_id in vehicle_ids:
        selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
        item_count = len(all_required)
        for file in all_required:
            if 'videos' in file:
                file_name = file.split(selected_vehicle.VIN)[1].split("/")[3]
                print(file_name)
            else:
                file_name = file.split(selected_vehicle.VIN)[1].split("/")[2]
            items_to_upload[file_name] = False

        new_path= f"{upload_creds['server_path']}/{selected_vehicle.VIN}/"

        for file in all_required:
            if 'videos' in file and ".mp4" in file:
                print("converting " + file)
                convert_to_tar(file)


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
                if 'videos' in file and '.mp4' not in file:
                    if 'videos' not in sftp.listdir(param_path):
                        sftp.mkdir(f"{param_path}/videos")
                    sftp.chdir(f"{param_path}/videos")
                    sftp.put(file)
                    items_to_upload[file.split(selected_vehicle.VIN)[1].split("/")[3]] = True
                elif '.log' in file:
                    sftp.chdir(param_path)
                    sftp.put(file)
                    items_to_upload[file.split(selected_vehicle.VIN)[1].split("/")[2]] = True
                sftp.chdir(new_path)
                item_count -= 1
    upload_completed = True
    print("upload complete")
    for root in all_roots:
        shutil.rmtree(root)
    network_monitor()


def convert_to_tar(video):
    global all_required

    print('opening ' + video)
    rand = random.randrange(1, 100000000)
    to_remove = []
    vid = cv2.VideoCapture(video)
    count = 0
    new_path = video.split('videos/')[0]+str(rand)
    os.mkdir(new_path)
    while vid.isOpened():
        # print("reading frame " + str(count))
        ret, image = vid.read()
        if ret:
            # print('reading file')
            cv2.imwrite(os.path.join(new_path, "%s.jpg") % str(count).rjust(8, "0"), image)
            to_remove.append(new_path + "/%s.jpg" % str(count).rjust(8, "0"))
            count += 1
        else:
            break
    vid.release()
    file_name = datetime.now().strftime(f'%m-%d-%y-%H%M%S-640x480-Capture.tar')
    tar = tarfile.open(f"{new_path}/{file_name}", "w")
    print(f"tar file name {file_name}")
    print('creating tar')
    for file in os.listdir(new_path):
        full_file = new_path + '/' + file
        if '.jpg' in file:
            # print('adding file ' + file)
            tar.add(full_file, arcname=file)
    tar.close()
    all_required.append(str(new_path + "videos/" + file_name).replace(str(rand), ""))
    print('closing')
    for file in to_remove:
        # print('destroy file ' + file)
        os.remove(file)
    orig_path = video.split("videos/")[0]
    shutil.move(new_path + "/" + file_name, orig_path + 'videos/' + file_name)
    os.remove(video)
    os.rmdir(new_path)
    time.sleep(1)

def sftp_connection():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    sftp = pysftp.Connection(upload_creds['server'],
                      username=upload_creds['username'],
                      password=upload_creds['password'],
                      cnopts=cnopts)
    return sftp




network_monitor()