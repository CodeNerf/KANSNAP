from db import db

class SignalsTable(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'SignalsTable'
    signal_description = db.Column(db.String(255))
    signal_id = db.Column(db.Integer, primary_key=True)
    system = db.Column(db.Text)
    units = db.Column(db.Text)
    capture_mode = db.Column(db.Text, default="Park")
    vehicle_id = db.Column(db.Integer)
    db.UniqueConstraint(signal_description)

    def __init__(self, signal_description, system, units, capture_mode, vehicle_id):
        self.signal_description = signal_description
        self.system = system
        self.units = units
        self.capture_mode = capture_mode
        self.vehicle_id = vehicle_id