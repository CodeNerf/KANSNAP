import flask
from app import app
from db import db
from flask import render_template, request
from models import phone_list
import json


@app.route('/update_phones/', methods=["POST", "GET"])
def phone_setup():
    all_phones = phone_list.PhoneList.query.all()
    if request.method == "POST":
        if 'new_ip_btn' in request.form:
            new_ip = phone_list.PhoneList(
                phone_ip=request.form['new_ip'],
                friendly_name=request.form['friendly_name'])
            print(new_ip)
            db.session.add(new_ip)
            db.session.commit()
            return flask.redirect(flask.url_for('phone_setup'))
        elif 'remove_phone_ip' in request.form:
            print(request.form["remove_phone_ip"])
            phone_list.PhoneList.query.filter_by(phone_ip=request.form["remove_phone_ip"]).delete()
            db.session.commit()
            return flask.redirect(flask.url_for('phone_setup'))
    return render_template('phone_setup.html', all_phones=all_phones)