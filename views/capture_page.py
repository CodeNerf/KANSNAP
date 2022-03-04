import random

import flask
import requests

from app import app
from flask import render_template, request
from models import vehicles, phone_list, signals_table, completed_signals, rationalized_list
from static.configurations.config import config_dictionary
from static.configurations.upload_information import logging_info
import can
import os
import threading
from datetime import datetime
import pathlib
import cv2
import shutil
from db import db
import time
import json
from views import edit_parameters
from can_overrides import MyCanutilsLogReader
import sys
import re
import logger

droid_x_hosts = config_dictionary['droid_x_list']
capture = ""
capturing = False
capture_initialized = False
VIN = ""
param_num = ""
video_ips = []
current_timestamp = ""
thread_count = 0
all_threads = []
can_channels = []
log_directory = ""
param_name = ""
logged_lines = 0
video_directory = ""
global_vehicle_id = ""
stored_marks = []
all_log_files = []
screen_cap_ip = None
screen_cap_only = False
finished = True
finish_error = ""
sorting = False
can_errors = ""
fatal_can_error = ""


@app.route('/parameter/<vehicle_id>/<param>', methods=["GET", "POST"])
def capture_page(vehicle_id, param):
    global VIN
    global param_num
    global param_name
    global global_vehicle_id

    # logger.CaptureActivityLogs.get_all_info()
    if flask.request.method == "POST":
        edit_parameters.add_signal(flask.request.form['addNewParam'])
        new_param_id = signals_table.SignalsTable.query.filter_by(signal_description=flask.request.form['addNewParam']).first().signal_id
        existing_info = rationalized_list.RationalizedList.query.filter_by(vehicle_id=vehicle_id).first()
        old_info = json.loads(existing_info.available_signals)
        old_info[new_param_id] = "Park"
        existing_info.available_signals = json.dumps(old_info)
        db.session.commit()
        logger.CaptureActivityLogs.capture_status_to_log(VIN, flask.request.form['addNewParam'], "Added Parameter")
        return flask.redirect(flask.url_for("capture_page", vehicle_id=vehicle_id, param=new_param_id))

    all_rational = {}
    global_vehicle_id = vehicle_id
    total_disk, used_disk, free_disk = shutil.disk_usage('/')
    total_disk = total_disk // (2**30)
    used_disk = used_disk // (2**30)
    free_disk = free_disk // (2**30)
    all_phones = phone_list.PhoneList.query.all()
    # jarred_phones = []
    # for phone in all_phones:
    #     if request.cookies.get(phone.phone_ip):
    #         jarred_phones.append(phone.phone_ip)
    busses = []
    selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
    VIN = selected_vehicle.VIN
    param_num = param
    param_name = signals_table.SignalsTable.query.filter_by(signal_id=param).first().signal_description
    query_rational = rationalized_list.RationalizedList.query.filter_by(vehicle_id=vehicle_id).first()
    for key, value in json.loads(query_rational.available_signals).items():
        if signals_table.SignalsTable.query.filter_by(signal_id=key).first():
            all_rational[key] = signals_table.SignalsTable.query.filter_by(signal_id=key).first().signal_description
    can_busses = selected_vehicle.networks_list.strip().split(',')
    for bus in can_busses:
        busses.append(bus)
    if len(can_busses) == 0:
        initiate_can_busses(vehicle_id)
    info = initiate_can_busses(vehicle_id)
    return render_template('parameter.html', info=info, all_phones=all_phones,
                           param_name=param_name, total_disk=total_disk, free_disk=free_disk,
                           vehicle_vin=selected_vehicle.VIN, all_rational=all_rational, vehicle_id=vehicle_id)


@app.route('/stop_capture')
def stop_capture():
    time.sleep(.5)
    global capturing
    global all_threads
    global logged_lines
    global log_directory
    global all_log_files
    global stored_marks
    global finished
    global sorting
    global fatal_can_error
    global can_channels
    global param_name
    global VIN

    if not capturing:
        return "Capture not started"


    print("stopping")
    can_channels = []
    fatal_can_error = ""
    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    image_path = f"{path}/static/images/"
    try:

        for file in os.listdir(image_path):
            if 'temp' in file:
                os.remove(image_path + file)
    except Exception as e:
        print(e)

    logged_lines = 0
    for log_filename in all_log_files:
        while not os.path.exists(log_filename):
            time.sleep(1)

    for log_filename in all_log_files:
        with open(log_filename, 'r+') as file:
            for mark in stored_marks:
                file.write(mark + '\n')
    capturing = False

    all_threads.clear()
    sorting = True
    safe_param_name = re.sub('\W+','', param_name )
    log_path = f"{path}/static/captures/{VIN}/{safe_param_name}"
    final_log = f"{log_path}/{datetime.now().strftime('%m-%d-%y-%H%M%S')}.log"
    opened_final = open(final_log, 'a+')
    for log_filename in all_log_files:
        temp_list = []
        for line in MyCanutilsLogReader(log_filename).file:
            temp_list.append(line)

        for line in temp_list:
            opened_final.write(line)
    opened_final.close()
    can_messages = sort_file(final_log)
    with open(final_log, 'w') as file:
        for can_message in can_messages:
            arb_length = 8 if can_message.is_extended_id else 3
            file.write(f"({can_message.timestamp:10.6f}) "
                           f"{can_message.channel} "
                           f"{can_message.arbitration_id:0{arb_length}X}#"
                           f"{''.join([f'{data_byte:02X}' for data_byte in can_message.data])}\n")

    for file in os.listdir(log_path):
        if 'temp' in file:
            os.remove(f"{log_path}/{file}")
    logger.CaptureActivityLogs.capture_status_to_log(VIN, safe_param_name, "Stopped Capture")
    finished = True
    print("capture stopped")
    return "stopping"


def sort_file(log_filename):
    global finish_error
    global sorting
    global stored_marks

    can_file = MyCanutilsLogReader(log_filename)
    try:
        listt = sorted(can_file, key=lambda x: x.timestamp)
    except Exception as e:
        finish_error = f"Error in capture. Will be missing frames."
        listt = can_file
    sorting = False
    stored_marks = []

    return listt


@app.route('/set_mark', methods=["POST"])
def set_mark():
    global log_filename
    global stored_marks

    marker_a_fake_can_msg = '7FF#DEADBEEF04F1D0AA'
    marker_b_fake_can_msg = '7FF#DEADBEEF04F1D0BB'
    ajax_info = flask.jsonify(request.json).get_json()
    if ajax_info['mark'] == "a":
        stored_marks.append(current_timestamp + "can0 " + marker_a_fake_can_msg)
    else:
        stored_marks.append(current_timestamp + "can0 " + marker_b_fake_can_msg)
    return "test"


@app.route('/wait_for_finish', methods=['GET'])
def wait_for_finish():
    global finished
    global finish_error
    global param_name

    safe_param_name = re.sub('\W+', '', param_name)
    fin_resp = {}
    if finished == False:
        if finish_error != "":
            fin_resp['error'] = finish_error
            logger.CaptureActivityLogs.capture_status_to_log(VIN, safe_param_name, f"Encountered Error: {finish_error}")
        else:
            fin_resp['error'] = ""
        fin_resp['status'] = False
    else:
        fin_resp['status'] = True
    flask.json.dumps(fin_resp)
    return fin_resp


@app.route('/param_capture_readout', methods=["GET"])
def param_capture_readout():
    global current_timestamp
    global video_ips
    global VIN
    global can_channels
    global log_directory
    global param_name
    global logged_lines
    global can_errors
    global fatal_can_error

    all_readouts = {}
    all_readouts['can_errors'] = can_errors
    all_readouts['current_time'] = current_timestamp
    all_readouts['active_recording_ips'] = video_ips
    all_readouts['active_cans'] = can_channels
    all_readouts['log_directory_path'] = log_directory
    all_readouts['can_log_filename'] = all_log_files
    all_readouts['logged_lines_count'] = logged_lines
    all_readouts['fatal_can_error'] = fatal_can_error

    flask.json.dumps(all_readouts)
    return all_readouts


@app.route('/start_capture', methods=["GET", "POST"])
def start_capture():
    global capturing
    global capture_initialized
    global video_ips
    global screen_cap_ip
    global screen_cap_only
    global finished
    global param_name
    global VIN

    screen_cap_ip = []

    print('start_capture')
    finished = False
    all_log_files.clear()
    if request.method == 'POST':
        ajax_info = flask.jsonify(request.json).get_json()
        video_ips = ajax_info['phone_ips']
        screen_cap_ip = ajax_info['screen_cap_ip']
        if ajax_info['phone_set'] == False:
            print("Phone not set")
            return "Phone Not Set"

    res = "blank"
    # for ip in video_ips:
    #     res = flask.make_response("setting cookie")
    #     print(f"setting cookie for {ip}")
    #     res.set_cookie(str(ip), str(ip))
    capturing = True
    safe_param_name = re.sub('\W+', '', param_name)
    print(VIN)
    print(safe_param_name)
    logger.CaptureActivityLogs.capture_status_to_log(VIN, safe_param_name, "Started Capture")
    start_threads()
    print("Starting!")
    return res


@app.route('/get_capture_amount', methods=["GET" , "POST"])
def finalize_capture():
    global param_num
    global VIN

    if request.method == "POST":
        completed_list = completed_signals.CompletedSignals.query.filter_by(vehicle_id=global_vehicle_id).first()
        if completed_list is None:
            new_info = completed_signals.CompletedSignals(
                vehicle_id = global_vehicle_id,
                completed_signals_list = param_num
            )
            db.session.add(new_info)
            db.session.commit()
            return flask.redirect(flask.url_for("list_vehicles", vehicle_id=global_vehicle_id))

        else:
            if param_num not in completed_list.completed_signals_list:
                completed_list.completed_signals_list = (completed_list.completed_signals_list + "," + param_num)
                db.session.commit()
                return flask.redirect(flask.url_for("list_vehicles", vehicle_id=global_vehicle_id))
        return flask.redirect(flask.url_for("list_vehicles", vehicle_id=global_vehicle_id))

    logs = {}
    videos = {}
    things = {}

    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    safe_param_name = re.sub('\W+', '', param_name)
    logger.CaptureActivityLogs.capture_status_to_log(VIN, safe_param_name, "Finalized Capture")
    log_path = f"{path}/static/captures/{VIN}/{safe_param_name}/"
    video_path = log_path + '/videos'
    num_of_logs = 0

    for log in os.listdir(log_path):
        if ".log" in log:
            logs[num_of_logs] = log
            num_of_logs += 1

    num_of_videos = 0
    for video in os.listdir(video_path):
        videos[num_of_videos] = video
        num_of_videos += 1

    things['logs'] = logs
    things['videos'] = videos

    return json.dumps(things)


def start_threads():
    global thread_count
    global all_threads
    global video_ips
    global global_vehicle_id
    global can_errors
    global fatal_can_error
    global screen_cap_ip

    can_errors = ""

    all_threads.clear()
    thread_count += 1
    if screen_cap_ip is not None:
        screen_cap_thread = threading.Thread(target=screen_capture, daemon=True, args=(thread_count, 8,))
        all_threads.append(screen_cap_thread)
        thread_count += 1

    selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=global_vehicle_id).first()

    for ip in video_ips:
        if ip != screen_cap_ip:
            thread_count += 1
            new_video_thread = threading.Thread(target=capture_video, daemon=True, args=(thread_count, ip,))
            all_threads.append(new_video_thread)

    for bus in selected_vehicle.networks_list.strip().split(','):
        print(bus)
        try:
            thread_count += 1
            new_bus_thread = threading.Thread(target=load_can_bus, daemon=True, args=(thread_count, bus.strip(),))
            all_threads.append(new_bus_thread)
        except:
            print(bus + " not available")
    thread_count += len(all_threads)



    for thread in all_threads:
        thread.start()


def initiate_can_busses(vehicle_id):
    selected_vehicle = vehicles.Vehicles.query.filter_by(vehicle_id=vehicle_id).first()
    global busses
    can_busses = selected_vehicle.networks_list.strip().split(',')
    busses = []
    for can_bus in can_busses:
        try:
            busses.append(can.interface.Bus(channel=can_bus.strip(), interface='socketcan'))
        except OSError as e:
            print(f"INITITIATE CAN BUS ERROR:On appending {can_bus} received error: {e}")
            return False, f"{can_bus} received error: {e}"
    return True, f"Success"


def load_can_bus(thread_num, can_channel):
    global current_timestamp
    global capturing
    global log_directory
    global logged_lines
    global all_log_files
    global can_errors
    global fatal_can_error
    global can_channels
    global param_name

    if not capturing:
        sys.exit()
    try:
        bus = can.Bus(interface='socketcan', channel=can_channel)
        for msg in bus:
            print(msg)
            break
    except Exception as e:
        print(f"----------{can_channel} Not Found------------")
        can_errors = can_errors + can_channel
        sys.exit()
    print('starting bus')
    channel = bus.channel_info.split("'")[1].replace("'", "")
    can_channels.append(channel)
    time_base_format = "10.6f"
    if capturing:
        path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
        safe_param_name = re.sub('\W+', '', param_name)
        log_path = f"{path}/static/captures/{VIN}/{safe_param_name}"
        if not os.path.exists(log_path):
            pathlib.Path(log_path).mkdir(parents=True, exist_ok=True)
        log_file = f"{log_path}/{can_channel.strip()}-{datetime.now().strftime('%m-%d-%y-%H%M%S')}temp.log"
        log_directory = log_path
        all_log_files.append(log_file)
        try:
            the_logger = can.Logger(log_file)
            can_logger = can.Notifier(bus, [the_logger])
            for msg in bus:
                current_timestamp = f"({msg.timestamp:{time_base_format}}) "
                logged_lines += 1
                if not capturing:
                    can_logger.stop()
                    if not the_logger.file.closed:
                        the_logger.file.close()
                    return
        except Exception as e:
            print("----Found a thing----")
            safe_param_name = re.sub('\W+', '', param_name)
            logger.CaptureActivityLogs.capture_status_to_log(VIN, safe_param_name, f"Fatal Error on Can {channel}")
            fatal_can_error = f"{channel} has gone down. Please verify capture hardware and try again."
            sys.exit()

def capture_video(thread_num, video_ip):
    global VIN
    global param_num
    global current_timestamp
    global capturing
    global video_directory
    global param_name

    if not capturing:
        sys.exit()
    safe_param_name = re.sub('\W+', '', param_name)
    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    vid_path = f"{path}/static/captures/{VIN}/{safe_param_name}/videos"
    if not os.path.exists(vid_path):
        pathlib.Path(vid_path).mkdir(parents=True, exist_ok=True)
    print("VID PATH: ", vid_path)
    video_directory = vid_path
    ip_string = video_ip.replace(".","")
    vid_file = f"{vid_path}/{datetime.now().strftime(f'VIDEO-{ip_string}-%m-%d-%y-%H%M%S.mp4')}"
    print("VID FILE ", vid_file)
    temp_file = f"static/images/{video_ip}temp.jpg"
    vc = cv2.VideoCapture(f"http://{video_ip}:4747/video", cv2.CAP_FFMPEG)
    vc.set(3, 640)
    vc.set(4, 480)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output = cv2.VideoWriter(vid_file, fourcc, 20, (640, 480))
    fc = 0
    while capturing:
        in_frame_text = f"IP: {video_ip} -- {current_timestamp}"
        ret, frame = vc.read()
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, in_frame_text, (10, 50), font, .5, (66, 245, 212), 1)
        if ret == True:
            fc += 1
            if fc == 10:
                fc = 0
                cv2.imwrite(temp_file, frame)
            output.write(frame)
    vc.release()
    output.release()
    cv2.destroyAllWindows()


def screen_capture(thread_num, rtsp_ip):
    global VIN
    global param_num
    global current_timestamp
    global capturing
    global video_directory
    global screen_cap_ip
    global screen_cap_only
    global param_name

    if not capturing:
        sys.exit()
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
    safe_param_name = re.sub('\W+', '', param_name)
    vid_path = f"{path}/static/captures/{VIN}/{safe_param_name}/videos"
    if not os.path.exists(vid_path):
        pathlib.Path(vid_path).mkdir(parents=True, exist_ok=True)
    video_directory = vid_path
    vid_file = f"{vid_path}/{datetime.now().strftime(f'SCREENCAPTURE-%m-%d-%y-%H%M%S.avi')}"
    vc = cv2.VideoCapture(f"rtsp://{screen_cap_ip}:4747/video", cv2.CAP_FFMPEG)
    vc.set(3,1920)
    vc.set(4, 1080)
    fourcc = cv2.VideoWriter_fourcc(*'xvid')
    output = cv2.VideoWriter(vid_file, fourcc, 20, (640, 360))
    fc = 0
    temp_file = f"static/images/screen_temp.jpg"
    while capturing:
        in_frame_text = f"SCREEN CAPTURE -- {current_timestamp}"
        ret, frame = vc.read()
        # print(ret)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, in_frame_text, (10, 50), font, .5, (66, 245, 212), 1)
        if ret == True:
            fc += 1
            if fc == 10:
                fc = 0
                cv2.imwrite(temp_file, frame)
            output.write(frame)
    vc.release()
    output.release()
    cv2.destroyAllWindows()
