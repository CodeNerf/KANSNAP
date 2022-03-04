from db import db

class ActivityLogs(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'ActivityLogs'

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.Text)
    location = db.Column(db.Text)
    vehicle_VIN = db.Column(db.Text)
    parameter_name = db.Column(db.Text)
    action = db.Column(db.Text)

    def __init__(self, datetime, location, vehicle_VIN, parameter_name, action):
        self.datetime = datetime
        self.location = location
        self.vehicle_VIN = vehicle_VIN
        self.parameter_name = parameter_name
        self.action = action