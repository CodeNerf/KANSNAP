# import flask
# import pathlib
# import os
# import shutil
# import threading
# import sys
# import json
# import moviepy.editor as moviepy
# from app import app
# from flask import render_template
# from models import signals_table
# from textwrap import wrap
#
# path = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent
# analysis_path = f"{path}/static/analysis/"
# local_upload_dir = "C:/Users/tom/PycharmProjects/canSNARE/static/captures"
# vin = ""
# all_logs = []
# all_videos = []
# parsed_file = {}
# streaming = False
# startingIdx = 0
# looping = False
#
# @app.route('/carhax', methods=["GET", "POST"])
# def carhax():
#     global vin
#     global all_videos
#     global all_videos
#
#     if flask.request.method == "POST":
#         if "vin" in flask.request.form:
#             all_signals = {}
#             vin = flask.request.form['vin']
#             for path, subdirs, files in os.walk(f"{local_upload_dir}/{vin}"):
#                 for dir in subdirs:
#                     # signal_desc = signals_table.SignalsTable.query.filter_by(signal_id=dir).first()
#                     # if signal_desc:
#                         all_signals[dir] = dir
#                 return render_template('carhax.html', all_signals=all_signals)
#
#         if "param_selection" in flask.request.form:
#             all_logs = []
#             all_videos = []
#             param_id = flask.request.form['param_selection']
#             files_dir = f"{local_upload_dir}/{vin}/{param_id}"
#             temp_files = []
#             for path, subdirs, files in os.walk(f"{local_upload_dir}/{vin}/{param_id}"):
#                 for file in files:
#                     if '.mp4' in file or '.avi' in file:
#                         print(file)
#                         if file not in os.listdir(analysis_path):
#                             clip = moviepy.VideoFileClip(f"{local_upload_dir}/{vin}/{param_id}/videos/{file}")
#                             clip.write_videofile(f"{analysis_path}/{file}")
#                     if 'log' in file:
#                         shutil.copy2(f"{files_dir}/{file}", analysis_path)
#                         all_logs.append(file)
#             for file in os.listdir(analysis_path):
#                 if '.log' not in file:
#                     all_videos.append(file)
#                     continue
#                 if '.log' in file:
#                     all_logs.append(file)
#             print(all_logs)
#             return render_template("carhax.html", files_dir=analysis_path, all_logs=all_logs, all_videos=all_videos)
#
#         return render_template('carhax.html')
#
#     return render_template('carhax.html')
#
# @app.route('/carhax/load_initial/<filename>', methods=["GET"])
# def load_initial(filename):
#     global parsed_file
#
#     parsed_file = {}
#     file = f'{analysis_path}/{filename}'
#     with open(file, 'r') as f:
#         for i, line in enumerate(f):
#             parsed_line = []
#             timestamp = line.split(" ")[0]
#             network = line.split(' ')[1]
#             data = line.split(" ")[2].split("#")[1]
#             arb_id = line.split(" ")[2].split("#")[0]
#             parsed_line.append(timestamp)
#             parsed_line.append(network)
#             parsed_line.append(arb_id)
#             data_bytes = wrap(data, 2)
#             parsed_line.append(data_bytes)
#             parsed_file[i] = parsed_line
#
#     return "done"
#
#
# @app.route("/carhax/start_stream/<sIdx>")
# def start_stream(sIdx):
#     global streaming
#     global parsed_file
#     global startingIdx
#
#     streaming = True
#     a = []
#     for key, value in parsed_file.items():
#
#         a.append(float(value[0].split(" ")[0].replace("(", "").replace(")", "")))
#
#     startingIdx = min(range(len(a)), key=lambda i: abs(a[i] - float(sIdx)))
#     print(startingIdx)
#     print(str(f"{len(parsed_file)},{startingIdx}"))
#     return str(f"{len(parsed_file)},{startingIdx}")
#
#
# @app.route('/carhax/stream_data/<idx>/<streamInc>')
# def stream_data(idx, streamInc):
#     global parsed_file
#     global streaming
#     global looping
#
#     end = False
#     outgoing_data = {}
#     chunk = []
#     incFloat = float(streamInc)
#     end_idx = int(idx) + int(incFloat)
#     if end_idx >= len(parsed_file):
#         end_idx = len(parsed_file)
#         end = True
#     for i in range(int(idx), end_idx):
#         chunk.append(parsed_file[int(i)])
#
#     if not looping and end:
#         print("--END--")
#         streaming = False
#
#     outgoing_data['data'] = json.dumps(chunk)
#     outgoing_data['status'] = streaming
#     outgoing_data['looping'] = looping
#     outgoing_data['end'] = end
#     return outgoing_data
#
# @app.route('/carhax-settings', methods=["POST"])
# def carhax_setting():
#     global looping
#
#     data =  flask.jsonify(flask.request.json).get_json()
#     looping = bool(data['looping'])
#
#     return ""
#
# @app.route("/carhax-get-new-idx/<videoLoc>", methods=["GET"])
# def carhax_new_idx(videoLoc):
#     global parsed_file
#     parsed_line_idx = int(len(parsed_file) * float(videoLoc))
#     return str(parsed_line_idx)