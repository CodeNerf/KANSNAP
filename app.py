import flask

app = flask.Flask(__name__)

app.config['SECRET_KEY'] = "hackingcarsyo"
app.config['ANALYSIS_UPLOAD'] = './static/analysis'