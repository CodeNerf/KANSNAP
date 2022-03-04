from db import db

class RationalizedList(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'RationalizedList'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer)
    available_signals = db.Column(db.Text)
    db.UniqueConstraint(vehicle_id)

    def __init__(self, vehicle_id, available_signals):
        self.vehicle_id = vehicle_id
        self.available_signals = available_signals