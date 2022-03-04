from db import db

class Systems(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'Systems'

    system_id = db.Column(db.Integer, primary_key=True)
    system_description = db.Column(db.Text)

    def __init__(self, system_description):
        self.system_description = system_description