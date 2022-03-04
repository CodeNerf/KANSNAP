import flask_sqlalchemy
from app import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dbs/vehicles.db'
SQLALCHEMY_BINDS = {
    'logmaster':  f'mysql+pymysql://admin:zxJn6iwivOFihjjMH4nlpixS7avL6vqdS0T2Loec@logmaster-instance-1.clopfkyoczic.us-east-2.rds.amazonaws.com:3306/logmaster',
}
db = flask_sqlalchemy.SQLAlchemy(app)

db.create_all()