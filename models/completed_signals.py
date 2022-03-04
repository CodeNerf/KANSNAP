from db import db

class CompletedSignals(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'CompletedSignals'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer)
    completed_signals_list = db.Column(db.Text)
    db.UniqueConstraint(vehicle_id)

    def __init__(self, vehicle_id, completed_signals_list):
        self.vehicle_id = vehicle_id
        self.completed_signals_list = completed_signals_list