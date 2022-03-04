import csv
import sys
import serial
import threading
import sqlalchemy as sa
import datetime
import time
import socket
import os
import shutil
import subprocess
import sqlalchemy.exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from csv import writer

aws_access_key_id = "AKIA5KJIMDRPPHDCB7P3"
aws_secret_access_key = "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"

base = declarative_base()
engine = sa.create_engine(f'mysql+pymysql://admin:{aws_secret_access_key}@logmaster-instance-1.clopfkyoczic.us-east-2.rds.amazonaws.com:3306/logmaster')
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker())(bind=engine)

storing_local = False



class CaptureActivityLogs(base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'CaptureActivityLogs'

    id = sa.Column(sa.Integer, primary_key=True)
    datetime = sa.Column(sa.Text)
    location = sa.Column(sa.Text)
    vehicle_VIN = sa.Column(sa.Text)
    parameter_name = sa.Column(sa.Text)
    action = sa.Column(sa.Text)

    def __init__(self, datetime, location, vehicle_VIN, parameter_name, action):
        self.datetime = datetime
        self.location = location
        self.vehicle_VIN = vehicle_VIN
        self.parameter_name = parameter_name
        self.action = action

    @staticmethod
    def capture_status_to_log(vehicle_vin, parameter_name, action):
        global storing_local

        datetime_info = datetime.datetime.now().strftime('%m-%d-%y@%H:%M:%S')
        location_info = get_gps_loc()
        if not storing_local:
            storing_local = True
        with open ('log_backup.csv', 'a+') as f:
            writer_object = writer(f)
            writer_object.writerow(['capture_activity', datetime_info, location_info, vehicle_vin, parameter_name, action])
            f.close()

    @staticmethod
    def get_all_info():
        try:
            return session.query(CaptureActivityLogs).all()
        except:
            return None


class GPSTracker(base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'GPSTracker'

    id = sa.Column(sa.Integer, primary_key=True)
    ip_address = sa.Column(sa.Text)
    datetime = sa.Column(sa.Text)
    location = sa.Column(sa.Text)

    def __init__(self, ip_address, datetime, location):
        self.ip_address = ip_address
        self.datetime = datetime
        self.location = location

    @staticmethod
    def tracker_thread():
        global storing_local
        global session

        while True:
            time.sleep(10)

            location_info = get_gps_loc()
            if not location_info:
                continue

            datetime_info = datetime.datetime.now().strftime('%m-%d-%y@%H:%M:%S')
            local_ip = socket.gethostbyname(socket.gethostname())
            if not storing_local:
                storing_local = True
            with open('log_backup.csv', 'a+') as f:
                writer_object = writer(f)
                writer_object.writerow(
                    ['gps_log', location_info, datetime_info, local_ip])
                f.close()


# ---NON DB CLASS RELATED THINGS----
def dump_local_logs():
    global storing_local
    try:
        if os.path.exists('log_backup.csv'):
            with open('log_backup.csv', 'r') as f:
                reader = csv.reader(f)
                for line in reader:
                    if 'capture_activity' in line:
                        dump_capture_activity(line)
                    if 'gps_log' in line:
                        dump_gps_log(line)
                f.close()
            storing_local = False
            os.remove('log_backup.csv')
    except Exception as e:
        print(e)


def dump_capture_activity(line):
    new_info = CaptureActivityLogs(
        datetime=line[1],
        location=line[2],
        vehicle_VIN=line[3],
        parameter_name=line[4],
        action=line[5]
    )
    session.add(new_info)
    session.commit()

def dump_gps_log(line):
    new_info = GPSTracker(
        ip_address=line[3],
        datetime=line[2],
        location=line[1]
    )
    session.add(new_info)
    session.commit()

def start_logger():
    threading.Thread(target=GPSTracker.tracker_thread, daemon=True).start()
    threading.Thread(target=reconnector, daemon=True).start()
    try:
        base.metadata.create_all()
    except:
        print("Cannot connect to AWS Servers. Starting anyway.")


def establish_db_connection():
    global base
    global engine
    global session
    global storing_local

    try:
        base = declarative_base()
        engine = sa.create_engine(
            f'mysql+pymysql://admin:{aws_secret_access_key}@logmaster-instance-1.clopfkyoczic.us-east-2.rds.amazonaws.com:3306/logmaster')
        base.metadata.bind = engine
        session = orm.scoped_session(orm.sessionmaker())(bind=engine)
        if session.query(CaptureActivityLogs).first():
            dump_local_logs()
    except sqlalchemy.exc.OperationalError:
        storing_local = True
        print("Attempting to reconnect to AWS...")


def get_gps_loc():
    # print("trying to connect to gps")
    try:
        port = '/dev/ttyUSB1'
        ser = serial.Serial(port, baudrate=9600, timeout=0.5)
        while True:
            raw_data = str(ser.readline())
            if 'GPGGA' in raw_data:
                data = raw_data.split(",")
                lat_deg = data[2]
                lat_dir = data[3]
                lon_deg = data[4]
                lon_dir = data[5]
                if lat_deg == "":
                    return None
                return ([f"{lat_deg}{lat_dir}", f"{lon_deg}{lon_dir}"])
            else:
                return None
    except Exception as e:
        # print("Cannot connect to GPS")
        # print(e)
        return None

def reconnector():
    global storing_local
    while True:
        time.sleep(30)
        if storing_local:
            establish_db_connection()


def setup_gps():
    # -- Check if GPS has been enabled --
    if not os.path.exists('/etc/minicom_setup.txt'):

        with open('minicom_setup.txt', 'w+') as f:
            f.write('send AT+QGPS=1')
            f.close()

        subprocess.call(['sudo', 'mv', 'minicom_setup.txt', '/etc/minicom_setup.txt'])
        subprocess.call(['sudo', 'cp', 'gps_setup.sh', '/etc/gps_setup.sh'])
        subprocess.call(['sudo', 'chmod', '755', '/etc/gps_setup.sh'])
        subprocess.call(['sudo', 'chmod', '755', '/etc/minicom_setup.txt'])
        subprocess.call(['sudo', 'cp', 'minicom_sysd_config', '/etc/systemd/system/minicom_gps_setup.service'])
        subprocess.call(['sudo', 'systemctl', 'daemon-reload'])
        subprocess.call(['sudo', 'systemctl', 'enable', 'minicom_gps_setup.service'])
        subprocess.call(['sudo', 'systemctl', 'start', 'minicom_gps_setup.service'])

        print("-----------------------------------------------------")
        print("----   Successfully Enabled. Restarting Pi  ----")
        print("-----------------------------------------------------")
        subprocess.call(['sudo', 'reboot'])
        # sys.exit()