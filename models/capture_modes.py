from db import db

class CaptureModes(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'CaptureModes'

    mode_id = db.Column(db.Integer, primary_key=True)
    mode_description = db.Column(db.Text)

    def __init__(self, mode_description):
        self.mode_description = mode_description