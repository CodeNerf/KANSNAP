from db import db

class PhoneList(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'PhoneList'

    id = db.Column(db.Integer, primary_key=True)
    phone_ip = db.Column(db.Text)
    friendly_name = db.Column(db.Text)

    def __init__(self, phone_ip, friendly_name):
        self.phone_ip = phone_ip
        self.friendly_name = friendly_name