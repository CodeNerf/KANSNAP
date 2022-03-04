import os
import pathlib
import flask_sqlalchemy
import flask
from db import db
from models import signals_table


all_systems = []
all_signals_desc = []
all_signal_id = []
def pull():
    db.create_all()
    # dir_path = str(os.path.dirname(os.path.realpath(__file__)))
    # path = str(dir_path + "/dbs/")
    # db_file = path + 'parameters.sql'
    # sql = open(db_file, mode='r', encoding='utf-8')
    # all_lines = sql.readlines()
    # for line in all_lines:
    #     if "INSERT INTO systems" in line:
    #         trimmed = line.split("INSERT INTO systems VALUES")[1].split(",")[1].split(")")[0].replace("'", "")
    #         all_systems.append((trimmed))
    #     if "INSERT INTO signal_table" in line:
    #         signal_desc = line.split("INSERT INTO signal_table VALUES('")[1].split("'")[0]
    #         signal_id = line.split("INSERT INTO signal_table VALUES('")[1].split(",")[1].split(",")[0]
    #
    #         all_signals_desc.append(signal_desc)
    #         all_signal_id.append(signal_id)
    #
    # for i, item in enumerate(all_signals_desc):
    #     new_signal = signals_table.SignalsTable(
    #         signal_description=all_signals_desc[i],
    #         system = None,
    #         units= None,
    #         capture_mode= "Park",
    #         vehicle_id= 0
    #     )
    #     db.session.add(new_signal)
    #     db.session.commit()

pull()