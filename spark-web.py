#!/usr/bin/env python3
from flask import Flask, flash, session, g, redirect, url_for, render_template, current_app, request, abort
import logging
import json
import jwt
import urllib.request
import urllib.parse
import urllib.error

app = Flask(__name__)
app.config.from_envvar('SPARK_SETTINGS')

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
app.logger.addHandler(stream_handler)
app.logger.setLevel(logging.DEBUG)

def spark_login(username, password):
    # client_id and client_secret are always the same, see https://user.spark.bg/client/config.js
    data = urllib.parse.urlencode({'grant_type': 'local', 
                                   'scope': 'RdsApi offline_access',
                                   'username': username,
                                   'password': password,
                                   'client_id': '1',
                                   'client_secret': 'y5pl0em'})
    data = data.encode('ascii')
    url = 'https://user.espark.lt/identity/core/connect/token'
    try:
        with urllib.request.urlopen(url, data) as f:
            resp = f.read().decode('utf-8')
            resp = json.loads(resp)
            token = resp['access_token']
            session['spark_token'] = token
            return True
    except urllib.error.HTTPError as e:
        app.logger.error(e.reason)
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not spark_login(username, password):
            error = 'Invalid username/password'
        else:
            flash('Login successful')
            return redirect(url_for('map'))
    return render_template('login.html', error=error)

@app.route('/')
def map():
    if not session.get('spark_token'):
        return redirect(url_for('login'))
    token = session['spark_token']
    req = urllib.request.Request('https://user.espark.lt/api/mobile/cars')
    req.add_header('Authorization', 'Bearer ' + token)
    with urllib.request.urlopen(req) as f:
        resp = f.read().decode('utf-8')
        cars = json.loads(resp)
    return render_template('map.html',
                           cars=cars,
                           maps_key=app.config['GOOGLE_MAPS_KEY'])

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=False)
