import flask

from db import db

class Vehicles(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'Vehicles'
    vehicle_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_year = db.Column(db.Integer)
    vehicle_make = db.Column(db.String(255))
    model = db.Column(db.String(255))
    VIN = db.Column(db.String(255))
    transmission_type = db.Column(db.String(255))
    trim_notes = db.Column(db.Text)
    networks_list = db.Column(db.Text, default='can0')

    def __init__(self, model_year, vehicle_make, model, VIN,
                 transmission_type, trim_notes, networks_list):
        self.model_year = model_year
        self.vehicle_make = vehicle_make
        self.model = model
        self.VIN = VIN
        self.transmission_type = transmission_type
        self.trim_notes = trim_notes
        self.networks_list = networks_list



